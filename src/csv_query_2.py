import sqlite3 
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox
from openai import OpenAI
import apikey
import json
import os
import re
from sqlparse import format
import sqlglot

# Globals
db_directory = "C:/Users/SIM-PC-1/Documents/GitHub/SuperKnowa-QueryCraft/input/spider/database"  
client = OpenAI(api_key=apikey.api_key)


def connect_to_db(db_path):
    """Establish connection to SQLite database."""
    try:
        conn = sqlite3.connect(db_path)
        print(f"Connected to {db_path} successfully.")
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return None


def extract_schema_from_context(context_str):
    """Extracts table and column names from the provided schema in the 'context' column."""
    table_mappings = {}
    column_mappings = {}
    
    matches = re.findall(r'CREATE TABLE \"(.*?)\" \((.*?)\);', context_str, re.DOTALL)
    for table, columns in matches:
        table_mappings[table] = table  # Preserve original case of table names
        column_mappings[table] = [col.strip().split()[0].replace('"', '') for col in columns.split(',')]
    
    return table_mappings, column_mappings


def normalize_sql(query):
    """Standardizes SQL formatting, capitalization, and structure for comparison."""
    try:
        formatted_query = format(query, reindent=True, keyword_case='upper')  # Normalize case & format
        parsed_query = sqlglot.parse_one(formatted_query, dialect="sqlite")  # Parse into AST
        return parsed_query.sql()  
    except Exception as e:
        print(f"SQL parsing error: {e}")
        return query.strip().lower()  # Fallback to lowercase comparison


def execute_query(db_path, query):
    """Executes a SQL query and returns the result as a DataFrame."""
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        print(f"Error executing query: {e}")
        return None  # Return None if query execution fails


def compare_queries(db_path, golden_sql, generated_sql):
    """Executes and compares two SQL queries based on result sets."""
    golden_result = execute_query(db_path, golden_sql)
    generated_result = execute_query(db_path, generated_sql)

    if golden_result is None or generated_result is None:
        print(f"Query Execution Error:\nGolden SQL: {golden_sql}\nGenerated SQL: {generated_sql}")
        return "Mismatch (Execution Error)"

    # Debug: Print actual results before comparison
    print("\n---- QUERY RESULTS ----")
    print(f"Golden SQL Result:\n{golden_result}")
    print(f"Generated SQL Result:\n{generated_result}")
    print("-----------------------\n")

    # Normalize DataFrame by converting to string, stripping spaces, and ignoring order
    try:
        golden_result = golden_result.astype(str).applymap(str.strip).sort_values(by=list(golden_result.columns), ignore_index=True)
        generated_result = generated_result.astype(str).applymap(str.strip).sort_values(by=list(generated_result.columns), ignore_index=True)

        if golden_result.equals(generated_result):
            return "Match"
        else:
            return "Mismatch (Different Results)"
    except Exception as e:
        print(f"Error comparing results: {e}")
        return "Mismatch (Comparison Error)"


def process_csv(file_path):
    """Processes the uploaded CSV file, generates SQL queries, and evaluates them."""
    df = pd.read_csv(file_path)
    
    if 'db_id' not in df.columns or 'question' not in df.columns or 'query' not in df.columns or 'context' not in df.columns:
        messagebox.showerror("Error", "CSV must contain 'db_id', 'question', 'query', and 'context' columns!")
        return
    
    results = []
    for index, row in df.iterrows():
        db_id = row['db_id']
        user_query = row['question']
        golden_sql = row['query']
        schema_context = row['context']
        
        # Find the corresponding database
        db_path = os.path.join(db_directory, f"{db_id}/{db_id}.sqlite")
        if not os.path.exists(db_path):
            print(f"Database file {db_path} not found!")
            continue  # Skip if database does not exist
        
        table_mappings, column_mappings = extract_schema_from_context(schema_context)
        
        raw_response, sql_query, text_response = get_sql_query(user_query, table_mappings, column_mappings)
        
        # Use query execution-based evaluation
        comparison = compare_queries(db_path, golden_sql, sql_query)

        results.append({
            'db_id': db_id,
            'question': user_query,
            'golden_sql': golden_sql,
            'generated_sql': sql_query,
            'comparison': comparison,
            'technical_translation': text_response
        })
    
    output_df = pd.DataFrame(results)
    output_file = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    if output_file:
        output_df.to_csv(output_file, index=False)
        messagebox.showinfo("Success", f"Results saved to {output_file}")


def get_sql_query(user_query, table_mappings, column_mappings):
    """Generates an SQL query based on a user question and schema context."""
    system_message = (
        "You are an SQL query bot that translates natural language queries into SQL queries for SQLite3. "
        "Use ONLY the table and column names provided in the schema. DO NOT invent new table or column names. "
        "Preserve the exact capitalization of table and column names as provided. "
        "Translate the user's natural language query into a structured technical explanation first, then generate the SQL query. "
        "Always return responses in the following format:\n"
        "{{{Technical Explanation: <technical_translation>}}}\n/** <SQL Query> **/\n"
        "\n"
         
         
         "Example 1:\n"
        "User Question: How many heads of the departments are older than 56?\n"
        "Schema: {\"head\": [\"head_ID\", \"name\", \"born_state\", \"age\", \"department_ID\"]}\n"
        "Response:\n"
        "{{{Technical Explanation: To answer the query, we need to count the number of department heads whose age is greater than 56. Assuming we have a table named 'head' with a column 'age' representing the ages of the department heads, we will filter the rows where 'age' is greater than 56 and then count those rows.}}}\n"
        "**SELECT COUNT(*) FROM head WHERE age > 56;**"
        "\n"
        "Now generate a response following this format."
    )
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_query}
        ],
        max_tokens=500
    )
    
    response_text = response.choices[0].message.content.strip()
    
    try:
        technical_translation = re.search(r"\{\{\{Technical Explanation: (.*?)\}\}\}", response_text, re.DOTALL).group(1).strip()
    except AttributeError:
        technical_translation = "Technical explanation not found"
    
    try:
        sql_query = re.search(r"/\*\*(.*?)\*\*/", response_text, re.DOTALL).group(1).strip()
    except AttributeError:
        sql_query = "Invalid SQL"
    
    return response_text, sql_query, technical_translation


def select_file():
    """Opens a file dialog for CSV selection and starts processing."""
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")], title="Select Query CSV")
    if file_path:
        process_csv(file_path)


# GUI Setup
root = tk.Tk()  
root.title("Multi-DB SQL Query Processor")

frame = tk.Frame(root)
frame.pack(pady=20)

label = tk.Label(frame, text="Select Query CSV:")
label.pack()

upload_button = tk.Button(frame, text="Upload CSV", command=select_file)
upload_button.pack()

exit_button = tk.Button(frame, text="Exit", command=root.quit)
exit_button.pack()

root.mainloop()
