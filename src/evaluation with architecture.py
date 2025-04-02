import sqlite3
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import re
import ast
import logging
from sqlparse import format
import sqlglot
from openai import OpenAI
import apikey
from collections import Counter

# Configure logging
logging.basicConfig(level=logging.INFO)

# Global configuration
db_directory = "C:/Users/SIM-PC-1/Documents/GitHub/SuperKnowa-QueryCraft/input/spider/database"
client = OpenAI(api_key=apikey.api_key)

class SQLQueryProcessor:
    def __init__(self, db_directory, client, interactive=False):
        self.db_directory = db_directory
        self.client = client
        self.interactive = interactive

    def connect_to_db(self, db_path):
        """Establish connection to SQLite database."""
        try:
            conn = sqlite3.connect(db_path)
            logging.info(f"Connected to {db_path} successfully.")
            return conn
        except sqlite3.Error as e:
            logging.error(f"Error connecting to database: {e}")
            return None

    def extract_schema_from_context(self, context):
        """
        Extract table and column names from the provided schema context.
        """
        if isinstance(context, list):
            schema_statements = context
        elif isinstance(context, str):
            try:
                schema_statements = ast.literal_eval(context)
            except (ValueError, SyntaxError):
                schema_statements = [context]
        else:
            logging.error(f"Unexpected context type: {type(context)}")
            return {}, {}

        table_mappings = {}
        column_mappings = {}
        for schema_str in schema_statements:
            matches = re.findall(r'CREATE TABLE\s*["`]?(\w+)["`]?\s*\((.*?)\)', schema_str, re.DOTALL)
            for table, columns in matches:
                table_mappings[table] = table
                column_names = []
                for col in columns.split(','):
                    col = col.strip()
                    if col:
                        column_name = col.split()[0].replace('"', '').replace('`', '')
                        column_names.append(column_name)
                column_mappings[table] = column_names
        return table_mappings, column_mappings

    def normalize_sql(self, query):
        """Standardizes SQL formatting and structure for comparison."""
        try:
            formatted_query = format(query, reindent=True, keyword_case='upper')
            parsed_query = sqlglot.parse_one(formatted_query, dialect="sqlite")
            return parsed_query.sql()
        except Exception as e:
            logging.error(f"SQL parsing error: {e}")
            return query.strip().lower()

    def execute_query(self, db_path, query):
        """Executes a SQL query and returns the result as a DataFrame."""
        if not query or query.strip() == "Invalid SQL":
            logging.error(f"Query validation failed: {query}")
            return None
        try:
            conn = sqlite3.connect(db_path)
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except Exception as e:
            logging.error(f"Error executing query: {e}")
            return None

    def compare_queries(self, db_path, golden_sql, generated_sql):
        """Executes and compares two SQL queries with comprehensive error handling."""
        if not generated_sql or generated_sql == "Invalid SQL":
            logging.error("Generated SQL is invalid or empty")
            return "Mismatch (Invalid Generated SQL)"
        
        golden_result = self.execute_query(db_path, golden_sql)
        generated_result = self.execute_query(db_path, generated_sql)

        if golden_result is None:
            logging.error("Golden SQL Query Execution Failed")
            return "Mismatch (Golden SQL Execution Error)"
        if generated_result is None:
            logging.error("Generated SQL Query Execution Failed")
            return "Mismatch (Generated SQL Execution Error)"

        try:
            golden_result.columns = [str(col).lower().strip() for col in golden_result.columns]
            generated_result.columns = [str(col).lower().strip() for col in generated_result.columns]

            if golden_result.shape[1] == generated_result.shape[1]:
                standard_columns = [f'col{i}' for i in range(golden_result.shape[1])]
                golden_result.columns = standard_columns
                generated_result.columns = standard_columns
            else:
                logging.error("The two results have a different number of columns.")
                return "Mismatch (Different number of columns)"

            golden_result = golden_result.astype(str).applymap(str.strip)
            generated_result = generated_result.astype(str).applymap(str.strip)

            if golden_result.equals(generated_result):
                return "Match"
            else:
                logging.error("Mismatch detected between query results.")
                return "Mismatch (Different Results)"
        except Exception as e:
            logging.error(f"Unexpected Error in Comparison: {e}")
            return f"Mismatch (Error: {str(e)})"

    def create_few_shot_examples(self, column_mappings):
        """Creates few-shot examples based on available schema."""
        examples = []
        if 'head' in column_mappings and 'age' in column_mappings['head']:
            examples.append(
                "User Question: How many heads of the departments are older than 56?\n"
                f"Available Schema: {column_mappings}\n"
                "{{{Technical Explanation: Count the number of department heads whose age is greater than 56 from the 'head' table.}}}\n"
                "/** SELECT COUNT(*) FROM head WHERE age > 56; **/\n"
            )
        if 'head' in column_mappings and all(col in column_mappings['head'] for col in ['name', 'born_state', 'age']):
            examples.append(
                "User Question: List the names, born states, and ages of heads sorted by age.\n"
                f"Available Schema: {column_mappings}\n"
                "{{{Technical Explanation: Retrieve name, born state, and age of heads, ordered by age in ascending order.}}}\n"
                "/** SELECT name, born_state, age FROM head ORDER BY age; **/\n"
            )
        if 'department' in column_mappings and 'num_employees' in column_mappings['department']:
            examples.append(
                "User Question: What is the average number of employees across departments?\n"
                f"Available Schema: {column_mappings}\n"
                "{{{Technical Explanation: Calculate the average number of employees from the department table.}}}\n"
                "/** SELECT AVG(num_employees) FROM department; **/\n"
            )
        return "\n\n".join(examples)

    def get_sql_query_candidates(self, user_query, table_mappings, column_mappings, n_candidates=3):
        """
        Calls the API to generate multiple candidate SQL queries.
        """
        schema_description = "Available Tables and Columns:\n"
        for table, columns in column_mappings.items():
            schema_description += f"Table '{table}': {columns}\n"

        few_shot_examples = self.create_few_shot_examples(column_mappings)
        system_message = (
            "You are an expert SQL query translator for SQLite3. Your task is to convert natural language questions into precise SQL queries.\n\n"
            "CRITICAL RULES:\n"
            "1. USE ONLY the table and column names in the provided schema.\n"
            "2. NEVER invent or modify table/column names.\n"
            "3. Preserve EXACTLY the capitalization of table and column names.\n"
            "4. If you cannot generate a valid query, respond with 'Invalid SQL'.\n\n"
            f"Available Schema:\n{schema_description}\n\n"
            "EXAMPLE QUERIES:\n"
            f"{few_shot_examples}\n\n"
            "Response Format:\n"
            "{{{Technical Explanation: <concise technical translation>}}}\n"
            "/** <Precise SQL Query> **/\n"
        )

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_query}
                ],
                max_tokens=500,
                n=n_candidates
            )
            candidates = []
            for choice in response.choices:
                response_text = choice.message.content.strip()
                try:
                    technical_translation = re.search(
                        r"\{\{\{Technical Explanation: (.*?)\}\}\}",
                        response_text, re.DOTALL
                    ).group(1).strip()
                except AttributeError:
                    technical_translation = "Technical explanation not found"
                try:
                    sql_query = re.search(
                        r"/\*\*(.*?)\*\*/",
                        response_text, re.DOTALL
                    ).group(1).strip()
                except AttributeError:
                    sql_query = "Invalid SQL"
                candidates.append((sql_query, technical_translation))
            return candidates
        except Exception as e:
            logging.error(f"Error in get_sql_query_candidates: {e}")
            return [("Invalid SQL", "Query generation failed")]

    def choose_query_candidate(self, candidates):
        """
        Automatically selects the best candidate using normalization and frequency count.
        If all normalized candidates are unique, flag as "DIVERGENT" and return the first candidate.
        """
        normalized_candidates = [self.normalize_sql(sql) for sql, _ in candidates]
        freq = Counter(normalized_candidates)
        if all(count == 1 for count in freq.values()):
            flag = "DIVERGENT"
            chosen_sql, tech = candidates[0]
        else:
            flag = "CONSENSUS"
            most_common, _ = freq.most_common(1)[0]
            for sql, tech in candidates:
                if self.normalize_sql(sql) == most_common:
                    chosen_sql, tech = sql, tech
                    break
        return chosen_sql, tech, flag

    def choose_query_candidate_execution_guided(self, candidates, db_path):
        """
        Re-ranks candidates based on execution feedback.
        Each candidate is executed on the provided db_path and scored by the number of rows returned.
        If all candidates score zero, fallback to the normalization-based selection.
        """
        scores = []
        for sql, tech in candidates:
            try:
                df = self.execute_query(db_path, sql)
                score = len(df) if df is not None else 0
            except Exception:
                score = 0
            scores.append(score)
        if all(score == 0 for score in scores):
            chosen_sql, tech, flag = self.choose_query_candidate(candidates)
            return chosen_sql, tech, flag
        else:
            max_idx = scores.index(max(scores))
            chosen_sql, tech = candidates[max_idx]
            flag = "EXEC_GUIDED"
            return chosen_sql, tech, flag

    def get_sql_query(self, user_query, table_mappings, column_mappings, db_path=None):
        """
        Generates an SQL query based on the user query and schema.
        If a db_path is provided, it uses execution-guided re-ranking; otherwise, it defaults to normalization.
        Returns the chosen SQL, its explanation, and a flag indicating the selection method.
        """
        candidates = self.get_sql_query_candidates(user_query, table_mappings, column_mappings)
        if db_path:
            chosen_sql, technical_translation, flag = self.choose_query_candidate_execution_guided(candidates, db_path)
        else:
            chosen_sql, technical_translation, flag = self.choose_query_candidate(candidates)
        return chosen_sql, technical_translation, flag

    def process_csv(self, file_path):
        """Processes the uploaded CSV file and evaluates generated queries."""
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read CSV file: {e}")
            return

        required_columns = {'db_id', 'question', 'query', 'context'}
        if not required_columns.issubset(set(df.columns)):
            messagebox.showerror("Error", "CSV must contain 'db_id', 'question', 'query', and 'context' columns!")
            return

        results = []
        for index, row in df.iterrows():
            db_id = row['db_id']
            user_query = row['question']
            golden_sql = row['query']
            schema_context = row['context']

            db_path = os.path.join(self.db_directory, f"{db_id}/{db_id}.sqlite")
            if not os.path.exists(db_path):
                logging.error(f"Database file {db_path} not found!")
                continue

            table_mappings, column_mappings = self.extract_schema_from_context(schema_context)
            generated_sql, tech_translation, flag = self.get_sql_query(user_query, table_mappings, column_mappings, db_path)
            comparison = self.compare_queries(db_path, golden_sql, generated_sql)

            results.append({
                'db_id': db_id,
                'question': user_query,
                'golden_sql': golden_sql,
                'generated_sql': generated_sql,
                'comparison': comparison,
                'technical_translation': tech_translation,
                'selection_flag': flag
            })

        output_df = pd.DataFrame(results)
        output_file = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if output_file:
            output_df.to_csv(output_file, index=False)
            messagebox.showinfo("Success", f"Results saved to {output_file}")

def select_file(processor):
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")], title="Select Query CSV")
    if file_path:
        processor.process_csv(file_path)

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Multi-DB SQL Query Processor")
    # Set interactive=False to enable automatic candidate selection.
    processor = SQLQueryProcessor(db_directory, client, interactive=False)
    
    frame = tk.Frame(root)
    frame.pack(pady=20)

    label = tk.Label(frame, text="Select Query CSV:")
    label.pack()

    upload_button = tk.Button(frame, text="Upload CSV", command=lambda: select_file(processor))
    upload_button.pack()

    exit_button = tk.Button(frame, text="Exit", command=root.quit)
    exit_button.pack()

    root.mainloop()
