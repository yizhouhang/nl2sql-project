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


def extract_schema_from_context(context):
    """
    Extracts table and column names from the provided schema context.
    
    Args:
        context (str or list): Schema context containing CREATE TABLE statements
    
    Returns:
        tuple: A tuple of table_mappings and column_mappings dictionaries
    """
    # Handle different input types
    if isinstance(context, list):
        # If it's already a list, use it directly
        schema_statements = context
    elif isinstance(context, str):
        try:
            # Try to evaluate the string as a list
            import ast
            schema_statements = ast.literal_eval(context)
        except (ValueError, SyntaxError):
            # If evaluation fails, split the string or wrap in a list
            schema_statements = [context]
    else:
        print(f"Unexpected context type: {type(context)}")
        return {}, {}

    table_mappings = {}
    column_mappings = {}

    # Regex to extract table and column names
    for schema_str in schema_statements:
        # More robust regex to handle different quote styles
        matches = re.findall(r'CREATE TABLE\s*["`]?(\w+)["`]?\s*\((.*?)\)', schema_str, re.DOTALL)
        
        for table, columns in matches:
            # Preserve original case of table names
            table_mappings[table] = table
            
            # Extract column names, handling different quote styles and types
            column_names = []
            for col in columns.split(','):
                col = col.strip()
                if col:  # Ignore empty columns
                    # Split at the first space to isolate the column name
                    column_name = col.split()[0].replace('"', '').replace('`', '')
                    column_names.append(column_name)
            
            column_mappings[table] = column_names

    
    #print(f"Extracted Table Mappings: {table_mappings}")
    #print(f"Extracted Column Mappings: {column_mappings}")
    
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
    """Executes a SQL query and returns the result as a DataFrame with improved error handling."""
    if not query or query.strip() == "Invalid SQL":
        print(f"Query validation failed: {query}")
        return None
        
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        print(f"Error executing query: {e}")
        return None  # Return None if query execution fails


def compare_queries(db_path, golden_sql, generated_sql):
    """Executes and compares two SQL queries with comprehensive error handling."""
    print(f"\nDEBUG - Comparing Queries:")
    print(f"Golden SQL: {golden_sql}")
    print(f"Generated SQL: {generated_sql}")

    if not generated_sql or generated_sql == "Invalid SQL":
        print("Generated SQL is invalid or empty")
        return "Mismatch (Invalid Generated SQL)"

    golden_result = execute_query(db_path, golden_sql)
    generated_result = execute_query(db_path, generated_sql)

    if golden_result is None:
        print("Golden SQL Query Execution Failed")
        return "Mismatch (Golden SQL Execution Error)"
    
    if generated_result is None:
        print("Generated SQL Query Execution Failed")
        print(f"Problematic Query: {generated_sql}")
        return "Mismatch (Generated SQL Execution Error)"

    try:
        # Normalize column names to lowercase and trim whitespace
        golden_result.columns = [str(col).lower().strip() for col in golden_result.columns]
        generated_result.columns = [str(col).lower().strip() for col in generated_result.columns]

        # Standardize column names to ignore differences
        if golden_result.shape[1] == generated_result.shape[1]:
            standard_columns = [f'col{i}' for i in range(golden_result.shape[1])]
            golden_result.columns = standard_columns
            generated_result.columns = standard_columns
        else:
            print("The two results have a different number of columns.")
            return "Mismatch (Different number of columns)"

        # Normalize data values by converting all to strings and stripping spaces
        golden_result = golden_result.astype(str).applymap(str.strip)
        generated_result = generated_result.astype(str).applymap(str.strip)

        if golden_result.equals(generated_result):
            return "Match"
        else:
            print("\nMISMATCH DETECTED:")
            print("Golden Result:\n", golden_result)
            print("\nGenerated Result:\n", generated_result)
            return "Mismatch (Different Results)"
    
    except Exception as e:
        print(f"Unexpected Error in Comparison: {e}")
        return f"Mismatch (Error: {str(e)})"


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
    # Convert mappings to a clear, readable string representation
    schema_description = "Available Tables and Columns:\n"
    for table, columns in column_mappings.items():
        schema_description += f"Table '{table}': {columns}\n"
    
    # Few-shot examples generator
    def create_few_shot_examples(column_mappings):
        examples = []
        
        # Example 1: Counting rows with a condition
        if 'head' in column_mappings and 'age' in column_mappings['head']:
            examples.append(
                "User Question: How many heads of the departments are older than 56?\n"
                f"Available Schema: {column_mappings}\n"
                "{{{Technical Explanation: Count the number of department heads whose age is greater than 56 from the 'head' table.}}}\n"
                "/** SELECT COUNT(*) FROM head WHERE age > 56; **/\n"
            )
        
        # Example 2: Selecting and ordering
        if 'head' in column_mappings and all(col in column_mappings['head'] for col in ['name', 'born_state', 'age']):
            examples.append(
                "User Question: List the names, born states, and ages of heads sorted by age.\n"
                f"Available Schema: {column_mappings}\n"
                "{{{Technical Explanation: Retrieve name, born state, and age of heads, ordered by age in ascending order.}}}\n"
                "/** SELECT name, born_state, age FROM head ORDER BY age; **/\n"
            )
        
        # Example 3: Aggregation
        if 'department' in column_mappings and 'num_employees' in column_mappings['department']:
            examples.append(
                "User Question: What is the average number of employees across departments?\n"
                f"Available Schema: {column_mappings}\n"
                "{{{Technical Explanation: Calculate the average number of employees from the department table.}}}\n"
                "/** SELECT AVG(num_employees) FROM department; **/\n"
            )
        
        return "\n\n".join(examples)
    
    # Generate few-shot examples based on available schema
    few_shot_examples = create_few_shot_examples(column_mappings)
    
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
    
    except Exception as e:
        print(f"Error in get_sql_query: {e}")
        return "", "Invalid SQL", "Query generation failed"
    
    
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
