import sqlite3
import tkinter as tk
from tkinter import scrolledtext
from tkinter import ttk
from PIL import Image, ImageTk
from openai import OpenAI
import apikey
import json
import textwrap
from datetime import datetime


# # Globals
db_name = "C:/Users/SIM-PC-1/Desktop/sakila-sqlite3/sakila_master.db"
client = OpenAI(api_key=apikey.api_key)
chat_history = []
last_technical_translation = ""


def connect_to_db(db_name):
    """Connect to the SQLite database."""
    try:
        conn = sqlite3.connect(db_name)
        print(f"Connected to {db_name} successfully.")
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return None
'''
def execute_query(er_diagram):
    """Execute the SQL query entered by the user and display the results in tabular format."""
    NLP_query = query_entry.get("1.0", tk.END).strip()
    selected_tables = er_diagram.get_selected_tables()
    print(f"Selected tables: {selected_tables}")
    SQL_query, text_response = get_sql_query(NLP_query)
    try:
        cursor = conn.cursor()
        cursor.execute(SQL_query)
        results = cursor.fetchall()
        columns = [description[0] for description in cursor.description]  # Get column names
        
        # Clear the treeview before showing new results
        for item in result_tree.get_children():
            result_tree.delete(item)

        # Set the columns and headers in the treeview
        result_tree["columns"] = columns
        result_tree["show"] = "headings"  # Only show the headings, no default column
        for col in columns:
            result_tree.heading(col, text=col)
            result_tree.column(col, width=150)  # Adjust the width of each column

        # Insert the results row by row
        for row in results:
            result_tree.insert("", "end", values=row)

    except sqlite3.Error as e:
        result_display.delete("1.0", tk.END)
        result_display.insert(tk.END, f"Error executing query: {e}\n")
'''

def format_schema(full_schema, user_query):
    """
    Perform soft schema selection to provide context-aware schema information for an LLM.
    
    Args:
    full_schema (list): List of table creation statements and descriptions
    user_query (str): Natural language query to generate SQL for
    
    Returns:
    dict: A dictionary containing soft schema selection details
    """
    def extract_table_details(table_definition):
        """
        Extract key details from table creation statement and description
        """
        # Split table definition into lines
        lines = table_definition.split('\n')
        
        # Extract table name (first line typically contains CREATE TABLE)
        table_name = lines[0].split()[2].strip('(')
        
        # Find table description
        description_lines = [line for line in lines if 'Table Description:' in line]
        description = description_lines[0].split(':', 1)[1].strip() if description_lines else ''
        
        # Extract columns
        columns = []
        for line in lines:
            if ' ' in line and ('NOT NULL' in line or 'DEFAULT' in line):
                # Basic column parsing
                column_parts = line.strip().split()
                column_name = column_parts[0]
                column_type = column_parts[1]
                columns.append({
                    'name': column_name,
                    'type': column_type
                })
        
        return {
            'name': table_name,
            'description': description,
            'columns': columns
        }
    
    # Parse schema into structured format
    parsed_schema = [extract_table_details(table) for table in full_schema]
    
    # System message for soft schema selection
    system_message = textwrap.dedent(f"""
    You are an expert database schema analyzer tasked with performing soft schema selection.
    
    Soft Schema Selection Guidelines:
    1. Analyze the entire database schema
    2. Identify most relevant tables and columns for the user query
    3. Provide detailed context about selected tables
    4. Maintain the full schema visibility
    5. Focus on columns that directly answer the query
    
    Full Database Schema:
    {json.dumps(parsed_schema, indent=2)}
    
    Instructions:
    - Extract key entities from the query
    - Identify tables and columns most likely to contain relevant information
    - Provide reasoning for your column selections
    - Suggest potential join strategies
    - Output your analysis in a structured JSON format
    """)
    
    # Soft Schema Selection Prompt Structure
    soft_schema_prompt = {
        "system_message": system_message,
        "user_query": user_query,
        "instructions": {
            "output_format": {
                "selected_tables": [
                    {
                        "table_name": "str",
                        "relevance_score": "float (0-1)",
                        "reasoning": "str",
                        "selected_columns": [
                            {
                                "column_name": "str",
                                "column_type": "str",
                                "relevance_score": "float (0-1)",
                                "reasoning": "str"
                            }
                        ]
                    }
                ],
                "suggested_join_strategy": "str",
                "potential_query_template": "str"
            }
        }
    }
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_query},
            {"role": "user", "content": f"Please provide the schema extraction in the following JSON format: {json.dumps(soft_schema_prompt['instructions']['output_format'], indent=2)}"}
        ],
        response_format={"type": "json_object"},
        max_tokens=500
    )

    # Extract and parse the JSON response
    try:
        final_schema = json.loads(response.choices[0].message.content)
        return final_schema
    except json.JSONDecodeError:
        print("Error parsing the JSON response")
        return None


# Modify the execute_query function
def execute_query(er_diagram):
    """Execute the SQL query entered by the user and display the results in tabular format."""
    global last_technical_translation
    NLP_query = query_entry.get("1.0", tk.END).strip()
    selected_tables = er_diagram.get_selected_tables()
    print(f"Selected tables: {selected_tables}")
    
    add_to_chat_history("user", NLP_query)
    
    SQL_query, text_response = get_sql_query(NLP_query)
    last_technical_translation = text_response

    add_to_chat_history("assistant", f"Technical Translation: {text_response}\nSQL Query: {SQL_query}")

    console_popup.log(f"Technical Translation: {text_response}")
    # Show technical translation & SQL query every time
    console_popup.log(f"Technical Translation: {text_response}")
    console_popup.log(f"Generated SQL Query: {SQL_query}")
    console_popup.show_window()  # <--- Force pop-up every time


    console_popup.log(f"Generated SQL Query: {SQL_query}")

    try:
        cursor = conn.cursor()
        cursor.execute(SQL_query)
        results = cursor.fetchall()
        columns = [description[0] for description in cursor.description]

        # Clear the treeview before showing new results
        for item in result_tree.get_children():
            result_tree.delete(item)

        # Set the columns and headers in the treeview
        result_tree["columns"] = columns
        result_tree["show"] = "headings"
        for col in columns:
            result_tree.heading(col, text=col)
            result_tree.column(col, width=150)

        # Insert the results row by row
        for row in results:
            result_tree.insert("", "end", values=row)

        console_popup.log("Query executed successfully.")

    except sqlite3.Error as e:
        error_message = f"Error executing query: {e}"
        console_popup.log(error_message)
        console_popup.show_window()

def save_chat_history(file_path='chat_history.json'):
    """Save the chat history to a JSON file."""
    with open(file_path, 'w') as f:
        json.dump(chat_history, f, indent=2)

def load_chat_history(file_path='chat_history.json'):
    """Load the chat history from a JSON file."""
    global chat_history
    try:
        with open(file_path, 'r') as f:
            chat_history = json.load(f)
    except FileNotFoundError:
        chat_history = []

def add_to_chat_history(role, content):
    """Add a message to the chat history."""
    global chat_history
    chat_history.append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    })
    save_chat_history()

def reprompt_query():
    """Reprompt the last query using the technical translation."""
    global last_technical_translation
    if last_technical_translation:
        new_prompt = f"The previous query '{last_technical_translation}' failed. Please provide a more specific or corrected SQL query for this request."
        query_entry.delete("1.0", tk.END)
        query_entry.insert(tk.END, new_prompt)
        console_popup.log(f"Reprompting with: {new_prompt}")
    else:
        no_translation_message = "No previous query to reprompt. Please enter a new query."
        console_popup.log(no_translation_message)
        query_entry.delete("1.0", tk.END)
        query_entry.insert(tk.END, "Enter your query here...")

def get_sql_query(user_query):
    """Get the SQL query from the OpenAI API based on the user's natural language query."""
    schema = extract_schema_for_prompt('sqlite-sakila-schema.txt')

    # Format the schema for better readability
    #formatted_schema = format_schema(schema, user_query)
    
    system_message = ("You are an SQL query bot who translates a natural language query to a SQL query (compatible with SQlite3). " +
                      "You are to generate 2 things. 1. A SQL query 2. A more technical translation of the natural language query so that the user" +
                      "can understand your approach. It should mimic what an expert SQL querier would say in natural language. Here are the instructions to do so. " +
                      "For the technical translation, provide a more technical translation of the natural language query. " +
                      "This should be a more detailed explanation of the natural language query provided. " +
                      "For the technical translation, encapsulate the response in a string {{{ technical-translation }}} to make a text box, where text-response refers to the technical translation. " +
                      f"Generate the SQL query based on the database schema: {schema} " +
                      "Do not provide any explanation, just the SQL code that is compatible with SQlite only. " +
                      "Do not add any markdown syntax. " +
                      "Only provide the SQL code. If the user requests something that you determine to be outside the defined schema, " +
                      "generate the closest possible SQL query, or dont generate any response. " +
                      "Do not include any comments in the SQL code. " +
                      "For SQL code, encapsulate the SQL query in a string /** SQL-query **/. where SQL-query refers to the SQL query generated. "
                      "Here are some few shot examples of the natural language query and the technical translation and SQL query that should be generated. " +
                      "Natural language query: 'Show me all the customers who have rented a film.' " +
                      "Technical translation: '{{{Provide a list of customers ((from the customer table) who have rented a film (checked in the rental table)}}}' " +
                      "SQL query: '/** SELECT * FROM customer WHERE customer_id IN (SELECT customer_id FROM rental); **/' " +
                      "Ensure that SQL query is enclosed in a string with /** to denote the start and **/ to denothe the end.")
                    
    '''
    "For text-based responses, encapsulate the response in a string {{{ text-response }}} to make a text box, where text-response refers to the text response generated. " + 
    "For example, if the response is 'Provide more details on which tables I should use.', the response should be {{{ Provide more details on which tables I should use. }}}.")
    ''' 
    
    print("\n--- Debug: Input to Language Model ---")
    print(f"System Message:\n{system_message}")
    print(f"\nUser Query:\n{user_query}")
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_query}
        ],
        max_tokens=400
    )
    
    sql_text_response = response.choices[0].message.content.strip()
    
    print("\n--- Debug: Output from Language Model ---")
    print(f"Generated SQL query:\n{sql_text_response}")
    
    try :
        sql_query = sql_text_response.split("/**")[1].split("**/")[0].strip()
    except IndexError:
        sql_query = "Query not found"


    try :
        text_response = sql_text_response.split("{{{")[1].split("}}}")[0].strip()
    except IndexError:
        text_response = "Response not found"
    
    return sql_query, text_response

'''
def format_schema(schema):
    """Format the schema for better readability by the LLM."""
    formatted_lines = []
    for line in schema.split('\n'):
        if line.strip().startswith('CREATE TABLE'):
            formatted_lines.append('\n' + line)
        elif line.strip().startswith(');'):
            formatted_lines.append(line + '\n')
        else:
            formatted_lines.append('  ' + line)
    return '\n'.join(formatted_lines)
'''

def extract_schema_for_prompt(file_path):
    """Extract schema from a txt file and process it into a plain text format for API calls."""
    schema_lines = []
    
    try:
        with open(file_path, 'r') as file:
            print(f"Schema found: {file_path}")
            for line in file:
                clean_line = line.strip()  # Remove unnecessary whitespace
                if clean_line:  # Skip empty lines
                    schema_lines.append(clean_line)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return ""
    
    # Join the lines into a single string, separated by spaces
    schema_as_string = " ".join(schema_lines)
    
    return schema_as_string

def on_exit():
    """Close the database connection and exit the program."""
    if conn:
        conn.close()
    save_chat_history()
    root.destroy()

class ImageERDiagramWidget(tk.Frame):
    def __init__(self, master, image_path, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.image_path = image_path
        self.selected_tables = set()
        self.create_widget()

    def create_widget(self):
        # Load and display the image
        self.image = Image.open(self.image_path)
        self.photo = ImageTk.PhotoImage(self.image)
        self.canvas = tk.Canvas(self, width=self.image.width, height=self.image.height)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)

        # Define clickable areas for each table
        first_row_x_coords = (43, 209)
        second_row_x_coords = (312, 478)
        third_row_x_coords = (592, 758)
        self.table_areas = {
            'category': (first_row_x_coords[0], 110, first_row_x_coords[1], 220),
            'film_category': (first_row_x_coords[0], 270, first_row_x_coords[1], 376),
            'film': (first_row_x_coords[0], 414, first_row_x_coords[1], 701),
            'language': (first_row_x_coords[0], 773, first_row_x_coords[1], 880),
            'film_actor': (first_row_x_coords[0], 920, first_row_x_coords[1], 1026),
            'inventory': (second_row_x_coords[0], 110, second_row_x_coords[1], 231),
            'rental': (second_row_x_coords[0], 269, second_row_x_coords[1], 432),
            'payment': (second_row_x_coords[0], 491, second_row_x_coords[1], 635),
            'staff': (second_row_x_coords[0], 670, second_row_x_coords[1], 902),
            'actor': (second_row_x_coords[0], 928, second_row_x_coords[1], 1038),
            'customer': (third_row_x_coords[0], 110, third_row_x_coords[1], 332),
            'address': (third_row_x_coords[0], 391, third_row_x_coords[1], 579),
            'city': (third_row_x_coords[0], 638, third_row_x_coords[1], 758),
            'country': (third_row_x_coords[0], 807, third_row_x_coords[1], 902),
            'store': (third_row_x_coords[0], 928, third_row_x_coords[1], 1038)
        }

        # Create clickable rectangles for each table
        self.table_rectangles = {}
        for table, coords in self.table_areas.items():
            rect = self.canvas.create_rectangle(coords, outline='', fill='', tags=table)
            self.table_rectangles[table] = rect
            self.canvas.tag_bind(rect, '<Button-1>', lambda event, t=table: self.toggle_table_selection(t))

    def toggle_table_selection(self, table):
        if table in self.selected_tables:
            self.selected_tables.remove(table)
            self.canvas.itemconfig(self.table_rectangles[table], fill='')
        else:
            self.selected_tables.add(table)
            self.canvas.itemconfig(self.table_rectangles[table], fill='yellow', stipple='gray50')
        #print(f"Selected tables: {self.selected_tables}")  # For debugging

    def get_selected_tables(self):
        return list(self.selected_tables)


class ConsolePopup:
    def __init__(self, parent):
        self.parent = parent
        self.window = None
        self.text_content = ""

    def create_window(self):
        self.window = tk.Toplevel(self.parent)
        self.window.title("Console Log")
        self.window.geometry("600x400")
        self.window.protocol("WM_DELETE_WINDOW", self.hide_window)

        self.text_area = scrolledtext.ScrolledText(self.window, wrap=tk.WORD, width=70, height=20)
        self.text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        self.text_area.insert(tk.END, self.text_content)

        self.close_button = tk.Button(self.window, text="Close", command=self.hide_window)
        self.close_button.pack(pady=5)

    def show_window(self):
        if self.window is None or not self.window.winfo_exists():
            self.create_window()
        else:
            self.window.deiconify()
        self.window.lift()

    def hide_window(self):
        if self.window and self.window.winfo_exists():
            self.text_content = self.text_area.get("1.0", tk.END)
            self.window.withdraw()

    def log(self, message):
        self.text_content += message + "\n"
        if self.window and self.window.winfo_exists():
            self.text_area.insert(tk.END, message + "\n")
            self.text_area.see(tk.END)


# Connect to the database
conn = connect_to_db(db_name)  # Replace with your actual database file

root = tk.Tk()
root.title("SQLite Query Executor with ER Diagram")

# Load chat history at the start of the application
load_chat_history()

console_popup = ConsolePopup(root)

# Create a frame for the ER diagram
er_frame = tk.Frame(root)
er_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Create the Image-based ER diagram widget
# Replace 'path_to_your_image.png' with the actual path to your ER diagram image
er_diagram = ImageERDiagramWidget(er_frame, image_path='C:/Users/SIM-PC-1/Desktop/SQL_ER_Diagram.png')
# er_diagram.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Create scrollbars for the ER diagram
h_scrollbar = tk.Scrollbar(er_frame, orient=tk.HORIZONTAL, command=er_diagram.canvas.xview)
h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
v_scrollbar = tk.Scrollbar(er_frame, orient=tk.VERTICAL, command=er_diagram.canvas.yview)
v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

er_diagram.canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
er_diagram.canvas.configure(scrollregion=er_diagram.canvas.bbox(tk.ALL))

# Create a frame for the query input and results
query_frame = tk.Frame(root)
query_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

# Add your existing widgets to the query frame
query_label = tk.Label(query_frame, text="Enter your SQL query:")
query_label.pack()

query_entry = tk.Text(query_frame, height=5, width=60)
query_entry.pack()

execute_button = tk.Button(query_frame, text="Execute", command=lambda: execute_query(er_diagram))
execute_button.pack()

result_tree = ttk.Treeview(query_frame)
result_tree.pack(fill="both", expand=True)

result_display = scrolledtext.ScrolledText(query_frame, height=5, width=80)
result_display.pack()


exit_button = tk.Button(query_frame, text="Exit", command=root.quit)
exit_button.config(command=on_exit)
exit_button.pack()

# Add buttons for console log and reprompt
button_frame = tk.Frame(query_frame)
button_frame.pack(before=exit_button)

# Add a button to open the console log
console_button = tk.Button(button_frame, text="Open Console Log", command=console_popup.show_window)
console_button.pack(side=tk.LEFT, padx=5)

reprompt_button = tk.Button(button_frame, text="Reprompt Last Query", command=reprompt_query)
reprompt_button.pack(side=tk.LEFT, padx=5)
# Start the Tkinter event loop
root.mainloop()