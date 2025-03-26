import sqlite3
import tkinter as tk
from tkinter import scrolledtext
from tkinter import ttk
from openai import OpenAI
import apikey

# Globals
db_name = "/mnt/c/Users/admin/Downloads/chinook/chinook.db"
client = OpenAI(api_key=apikey.api_key)


def connect_to_db(db_name):
    """Connect to the SQLite database."""
    try:
        conn = sqlite3.connect(db_name)
        print(f"Connected to {db_name} successfully.")
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return None

def execute_query():
    """Execute the SQL query entered by the user and display the results in tabular format."""
    NLP_query = query_entry.get("1.0", tk.END).strip()
    SQL_query = get_sql_query(NLP_query)
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

def get_sql_query(user_query):
    """Get the SQL query from the OpenAI API based on the user's natural language query."""
    schema = extract_schema_for_prompt('src/schema.txt')
    response = client.chat.completions.create(model="gpt-4o",
        messages=[
            {"role": "system", "content": "Generate only the SQL query based on the database schema: {schema} " +
                "Do not provide any explanation, just the SQL code. " +
                ##"Ensure all names used in SQL query exists and is stated in the schma and the schema only" +
                "Do not add any markdown syntax. " +
                "Only provide the SQL code. If the user requests something that you determine to be outside the defined schema, " +
                "try to find the closest match if not, provide an empty output."},
            {"role": "user", "content": user_query}
        ],
        max_tokens=200)
    sql_query = response.choices[0].message.content.strip()
    print(f"Generated SQL query: {sql_query}")
    return sql_query

def extract_schema_for_prompt(file_path):
    """Extract schema from a txt file and process it into a plain text format for API calls."""
    schema_lines = []
    
    try:
        with open(file_path, 'r') as file:
            print(f"Schema found found: {file_path}")
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
    root.destroy()

class ERDiagramWidget(tk.Canvas):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.tables = {}
        self.selected_tables = set()
        self.create_er_diagram()

    def create_er_diagram(self):
        # Define table positions and sizes
        table_info = {
            'category': {'x': 50, 'y': 50, 'width': 150, 'height': 100},
            'inventory': {'x': 250, 'y': 50, 'width': 150, 'height': 100},
            'customer': {'x': 450, 'y': 50, 'width': 150, 'height': 180},
            'film_category': {'x': 50, 'y': 200, 'width': 150, 'height': 100},
            'rental': {'x': 250, 'y': 200, 'width': 150, 'height': 160},
            'address': {'x': 450, 'y': 250, 'width': 150, 'height': 160},
            'film': {'x': 50, 'y': 350, 'width': 150, 'height': 260},
            'payment': {'x': 250, 'y': 400, 'width': 150, 'height': 140},
            'city': {'x': 450, 'y': 450, 'width': 150, 'height': 100},
            'language': {'x': 50, 'y': 650, 'width': 150, 'height': 100},
            'staff': {'x': 250, 'y': 580, 'width': 150, 'height': 200},
            'country': {'x': 450, 'y': 580, 'width': 150, 'height': 100},
            'film_actor': {'x': 50, 'y': 780, 'width': 150, 'height': 100},
            'actor': {'x': 250, 'y': 820, 'width': 150, 'height': 120},
            'store': {'x': 450, 'y': 720, 'width': 150, 'height': 100},
        }

        # Create tables
        for table, coords in table_info.items():
            self.create_table(table, coords['x'], coords['y'], coords['width'], coords['height'])

        # Draw relationships
        self.draw_relationship('category', 'film_category')
        self.draw_relationship('film_category', 'film')
        self.draw_relationship('inventory', 'film')
        self.draw_relationship('inventory', 'rental')
        self.draw_relationship('customer', 'rental')
        self.draw_relationship('customer', 'address')
        self.draw_relationship('rental', 'payment')
        self.draw_relationship('staff', 'payment')
        self.draw_relationship('staff', 'store')
        self.draw_relationship('address', 'city')
        self.draw_relationship('city', 'country')
        self.draw_relationship('film', 'language')
        self.draw_relationship('film', 'film_actor')
        self.draw_relationship('film_actor', 'actor')

    def create_table(self, name, x, y, width, height):
        table = self.create_rectangle(x, y, x + width, y + height, fill='lightblue', outline='black')
        text = self.create_text(x + width/2, y + 20, text=name, font=('Arial', 12, 'bold'))
        
        # Add table columns
        columns = {
            'category': ['category_id', 'name', 'last_update'],
            'inventory': ['inventory_id', 'film_id', 'store_id', 'last_update'],
            'customer': ['customer_id', 'store_id', 'first_name', 'last_name', 'email', 'address_id', 'activebool', 'create_date', 'last_update', 'active'],
            'film_category': ['film_id', 'category_id', 'last_update'],
            'rental': ['rental_id', 'rental_date', 'inventory_id', 'customer_id', 'return_date', 'staff_id', 'last_update'],
            'address': ['address_id', 'address', 'address2', 'district', 'city_id', 'postal_code', 'phone', 'last_update'],
            'film': ['film_id', 'title', 'description', 'release_year', 'language_id', 'rental_duration', 'rental_rate', 'length', 'replacement_cost', 'rating', 'last_update', 'special_features', 'fulltext'],
            'payment': ['payment_id', 'customer_id', 'staff_id', 'rental_id', 'amount', 'payment_date'],
            'city': ['city_id', 'city', 'country_id', 'last_update'],
            'language': ['language_id', 'name', 'last_update'],
            'staff': ['staff_id', 'first_name', 'last_name', 'address_id', 'email', 'store_id', 'active', 'username', 'password', 'last_update', 'picture'],
            'country': ['country_id', 'country', 'last_update'],
            'film_actor': ['actor_id', 'film_id', 'last_update'],
            'actor': ['actor_id', 'first_name', 'last_name', 'last_update'],
            'store': ['store_id', 'manager_staff_id', 'address_id', 'last_update'],
        }
        
        for i, column in enumerate(columns[name]):
            self.create_text(x + 10, y + 40 + i*20, text=column, anchor='w', font=('Arial', 10))

        self.tables[name] = (table, text)
        self.tag_bind(table, '<Button-1>', lambda event, tn=name: self.toggle_table_selection(tn))
        self.tag_bind(text, '<Button-1>', lambda event, tn=name: self.toggle_table_selection(tn))

    def draw_relationship(self, table1, table2):
        x1, y1 = self.coords(self.tables[table1][0])[:2]
        x2, y2 = self.coords(self.tables[table2][0])[:2]
        self.create_line(x1, y1, x2, y2, fill='gray', arrow=tk.LAST)

    def toggle_table_selection(self, table_name):
        table, text = self.tables[table_name]
        if table_name in self.selected_tables:
            self.selected_tables.remove(table_name)
            self.itemconfig(table, fill='lightblue')
        else:
            self.selected_tables.add(table_name)
            self.itemconfig(table, fill='yellow')
        print(f"Selected tables: {self.selected_tables}")  # For debugging

    def get_selected_tables(self):
        return list(self.selected_tables)

# Connect to the database
conn = connect_to_db(db_name)  # Replace with your actual database file

root = tk.Tk()
root.title("SQLite Query Executor with ER Diagram")

# Create a frame for the ER diagram
er_frame = tk.Frame(root)
er_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Create the ER diagram widget
er_diagram = ERDiagramWidget(er_frame, width=800, height=1000)
er_diagram.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Create a scrollbar for the ER diagram
er_scrollbar = tk.Scrollbar(er_frame, orient=tk.VERTICAL, command=er_diagram.yview)
er_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
er_diagram.configure(yscrollcommand=er_scrollbar.set)
er_diagram.configure(scrollregion=er_diagram.bbox("all"))

# Create a frame for the query input and results
query_frame = tk.Frame(root)
query_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

# Add your existing widgets to the query frame
query_label = tk.Label(query_frame, text="Enter your SQL query:")
query_label.pack()

query_entry = tk.Text(query_frame, height=5, width=60)
query_entry.pack()

execute_button = tk.Button(query_frame, text="Execute", command=execute_query)
execute_button.pack()

result_tree = ttk.Treeview(query_frame)
result_tree.pack(fill="both", expand=True)

result_display = scrolledtext.ScrolledText(query_frame, height=5, width=80)
result_display.pack()

exit_button = tk.Button(query_frame, text="Exit", command=on_exit)
exit_button.pack()

'''
# Modify your execute_query function to use the selected tables
def execute_query():
    query = query_entry.get("1.0", tk.END).strip()
    selected_tables = er_diagram.get_selected_tables()
    
    # You can use the selected_tables list to modify or validate the query
    # For example, you could check if all tables in the query are selected
    
    try:
        # Your existing query execution code here
        # ...

        # Display results in the Treeview
        # ...

    except sqlite3.Error as e:
        result_display.delete("1.0", tk.END)
        result_display.insert(tk.END, f"An error occurred: {e}")
'''

# Start the Tkinter event loop
root.mainloop()

