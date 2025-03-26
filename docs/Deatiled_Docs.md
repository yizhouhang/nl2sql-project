# Documentation: SQLite Query Executor with ER Diagram

This application integrates SQLite, OpenAI's GPT API, and Tkinter to create an interactive database query execution and visualization tool. Below is the documentation of its components.

---

## Table of Contents
1. [UI Components](#ui-components)
2. [Console/Error Handling/Reprompting](#consoleerror-handlingreprompting)
3. [Schema Formatting](#schema-formatting)
4. [Query Execution and Database Interaction](#query-execution-and-database-interaction)
5. [General Utilities](#general-utilities)

---

## UI Components

### Main UI Setup (Lines 382–474)
- **`root` (`Tk` object)**: Main application window initialized.
- **ER Diagram Frame (`er_frame`)**: Holds the image-based ER diagram widget.
  - Horizontal and vertical scrollbars are linked to the canvas for the ER diagram.
- **Query Frame (`query_frame`)**: Contains widgets for query input, execution button, result display, and additional functionalities like logging and reprompting.
  - `query_entry`: Multi-line text input for user queries.
  - `execute_button`: Executes the SQL query when clicked.
  - `result_tree`: Displays query results in tabular format.
  - `result_display`: Displays raw error or output information in a scrolled text widget.
  - Exit and utility buttons (Console Log, Reprompt Query).

---

## Console/Error Handling/Reprompting

### Console Popup (`ConsolePopup` Class, Lines 317–355)
- Creates a popup window for logging runtime messages.
- **Key Methods**:
  - `create_window()`: Initializes the popup window and adds a scrolled text widget.
  - `log(message)`: Appends logs to the text area.
  - `show_window()`: Displays the popup.
  - `hide_window()`: Hides the popup but retains logs in memory.

### Error Handling in Query Execution (Lines 143–172, 457–462)
- Errors during query execution (`execute_query`) are caught using `sqlite3.Error` and logged in the console popup.
- Example logged error:
  - `Error executing query: <error_message>`.

### Reprompting Queries (Lines 248–262)
- `reprompt_query()`: Automatically rephrases a failed query using the last technical translation and inserts it into the query entry widget for user correction.

---

## Schema Formatting

### Schema Extraction (`extract_schema_for_prompt`, Lines 287–300)
- Reads and cleans a schema file (`sqlite-sakila-schema.txt`), returning a plain text schema for the OpenAI API.

### Schema Contextualization for LLM (`format_schema`, Lines 67–130)
- Converts the raw schema into a context-aware JSON format for structured input to the GPT API.
- **Outputs**:
  - `selected_tables`: Relevant tables and columns.
  - `suggested_join_strategy`: Suggested table joins based on the query.

---

## Query Execution and Database Interaction

### Database Connection (`connect_to_db`, Lines 14–22)
- Connects to the SQLite database specified by `db_name`. Handles connection errors gracefully.

### Query Execution (`execute_query`, Lines 143–207)
- **Steps**:
  1. Parses user input from `query_entry`.
  2. Fetches the SQL query and technical translation from `get_sql_query`.
  3. Executes the generated SQL query and displays results in `result_tree`.
  4. Handles errors during execution.

### SQL Query Generation via GPT API (`get_sql_query`, Lines 264–285)
- Sends a structured schema and natural language query to GPT via OpenAI's API.
- **Key Parameters**:
  - `schema`: Extracted database schema.
  - `user_query`: User's natural language query.
- **Outputs**:
  - `SQL_query`: Generated SQL query string.
  - `text_response`: Technical explanation of the query generation.

---

## General Utilities

### Chat History Management (Lines 224–246)
- Functions:
  - `add_to_chat_history(role, content)`: Appends a message to chat history with a timestamp.
  - `save_chat_history(file_path)`: Saves chat history to a JSON file.
  - `load_chat_history(file_path)`: Loads chat history at app startup.

### Exit Functionality (`on_exit`, Lines 302–306)
- Ensures the database connection is closed and chat history is saved before exiting the application.

---

## Additional Notes

### File Dependencies
- **Schema File**: `sqlite-sakila-schema.txt` for schema extraction.
- **ER Diagram Image**: Path specified as `/mnt/c/Users/admin/Pictures/SQL_ER_Diagram.png`.

### External Libraries
- `sqlite3`: For database operations.
- `tkinter`: For UI components.
- `PIL (Pillow)`: For displaying the ER diagram image.
- `openai`: For GPT integration.

# Contribution Guide: Updating the SQLite Query Executor with ER Diagram

This guide provides a step-by-step explanation for making common updates to the codebase. The following changes are covered:

1. [Changing the GPT API or Model](#1-changing-the-gpt-api-or-model)
2. [Using Another Database](#2-using-another-database)
3. [Modifying the System Prompt](#3-modifying-the-system-prompt)

---

## 1. Changing the GPT API or Model

### Steps
1. **Locate the API Call**:
   - The API call to OpenAI is in the function `get_sql_query()` (Lines 264–285).
   - Look for the call:
     ```python
     response = client.chat.completions.create(...)
     ```

2. **Replace with New Model/Endpoint**:
   - If using a different model or provider:
     - Update the `model` parameter or equivalent field to the desired model.
     - Ensure that the format of `messages` matches the new provider's API structure.

3. **Update Dependencies**:
   - If switching to a different API library (e.g., Anthropic, Google Bard):
     - Install the required library via `pip`.
     - Replace `openai` library imports and adapt API calls accordingly.

4. **Test the Changes**:
   - Run the application with various queries to ensure the new model integrates seamlessly and returns valid SQL queries.

---

## 2. Using Another Database

The databse is set up to work with SQLite3 databases. To switch to another DB provider, 
changes will need to be made in executing the database query which is on lines 201 ownards on the method execute_query, 
and lines  20 onwards on the method connect_to_db
Switching to a new database involves updating the following components:

### Steps

1. **Replace the Database File**:
   - Update the `db_name` variable (Line 9) with the path to the new database file:
     ```python
     db_name = "/path/to/your/new/database.db"
     ```

2. **Update the ER Diagram**:
   - Replace the image file in the `ImageERDiagramWidget` (Line 392):
     ```python
     image_path='/path/to/new/er_diagram.png'
     ```

3. **Update the Schema File**:
   - Replace the schema file used in `extract_schema_for_prompt()` (Lines 287–300):
     ```python
     schema = extract_schema_for_prompt('path/to/new-schema.txt')
     ```

4. **Verify the Schema Parsing**:
   - Ensure the schema text file follows the expected format for `extract_schema_for_prompt()`.

5. **Update the Table Coordinates (Optional)**:
   - If the new ER diagram has different table positions, update the clickable areas in `ImageERDiagramWidget` (Lines 317–356):
     ```python
     self.table_areas = {
         'new_table_1': (x1, y1, x2, y2),
         ...
     }
     ```

6. **Test the New Database**:
   - Ensure the updated schema works with both the SQL generation and execution components.

---

## 3. Modifying the System Prompt

The system prompt is used to guide GPT's behavior and can be customized for clarity or new requirements.

**Locating the Prompt**:
   - The system prompt is defined in `get_sql_query()` (Lines 264–285).
   - Look for the `system_message` variable:
     ```python
     system_message = ("You are an SQL query bot...")
     ```

---

# Getting Started: SQLite Query Executor with ER Diagram

This guide will help you set up and run the SQLite Query Executor application on your system. The current Python version is **Python 3.11.9**.

---

## Table of Contents
1. [Prerequisites](#1-prerequisites)
2. [Installation](#2-installation)
3. [Setting Up the Application](#3-setting-up-the-application)
4. [Running the Application](#4-running-the-application)
5. [Testing the Application](#5-testing-the-application)
6. [Troubleshooting](#6-troubleshooting)

---

## 1. Prerequisites

### Required Tools
- **Python 3.11.9** or later
- **pip** (comes with Python)
- SQLite database file (e.g., `sakila_master.db`)
- ER diagram image (e.g., `SQL_ER_Diagram.png`)
- Schema text file (e.g., `sqlite-sakila-schema.txt`)

### Python Libraries
The application uses the following Python libraries:
- `sqlite3` (built-in)
- `tkinter` (built-in)
- `Pillow` (for image handling)
- `openai` (for GPT API calls)

### Database Requisites
SQLite3 does not require any requisties as it works natively on python with the SQLite3 package

---

## 2. Installation

### Step 1: Clone the Repository
Download or clone the repository containing the code:
then
cd sqlite-query-executor
cd src

pip install pillow openai

## 3. Setting Up the Application

### Step 1: Configure the Database
- Place your SQLite database file (e.g., `sakila_master.db`) in the project directory.
- Update the `db_name` variable in the code (Line 9) with the database file path:
  ```python
  db_name = "path/to/your/database.db"

### Step 2: Add the Schema File
- Save your database schema in a plain text file (e.g., `sqlite-sakila-schema.txt`).
- Update the schema file path in the function `extract_schema_for_prompt` at Line 287. Replace the file path with the location of your schema file.

### Step 3: Update the ER Diagram
- Replace the ER diagram image with your own (e.g., `SQL_ER_Diagram.png`).
- Update the file path in `ImageERDiagramWidget` at Line 392. Set the path to the location of your new ER diagram image.

### Step 4: Add Your OpenAI API Key
- Update the Python file named `apikey.py`.
- Add your OpenAI API key as a variable named `api_key`.
- Ensure the `apikey.py` file is in the same directory as the main script.

## Guide on OpenAPI key
- To get an OpenAI API key, you can: 
- Go to https://platform.openai.com/ 
- Sign up or log in to your account 
- Click your name in the top-right corner 
- Select View API keys from the dropdown menu 
- Click Create new secret key 
- Name the key and set permissions 
- Click Create secret key 
- Copy the key and store it in a safe place 

---

## 4. Running the Application

### Step 1: Start the Application
Run the script using Python by executing it from the command line.

- under directory ../structured-natural-language/srs
- run 'python3 pgconnection.py'

### Step 2: Interact with the Application
- Use the query input box to enter natural language queries.
- Click the "Execute" button to generate and execute SQL queries.
- View the results in the table display or the console log.

---

## 5. Testing the Application

### Test 1: Default Setup
Use the provided SQLite database file (e.g., `sakila_master.db`) and test queries like:
- "Show all customers who rented a film."
- "List all movies in the inventory."

### Test 2: Custom Database
Replace the database file, schema file, and ER diagram with your own resources. Test queries relevant to your schema to ensure compatibility.

---

## 6. Troubleshooting

### Common Issues
- **Missing Libraries**: If libraries are not found, ensure they are installed using pip.
- **Database Connection Fails**: Verify the `db_name` variable points to the correct database file and that the file exists.
- **OpenAI API Errors**: Check if the API key in `apikey.py` is correct and ensure your API usage limits are not exceeded.
- **ER Diagram Display Issues**: Ensure the image file path is correct and the file format is supported (e.g., PNG or JPG).

---

## Additional Notes

### Debugging
- Use the console log feature in the application to troubleshoot errors.
- Add debug statements (e.g., print statements) to the code to inspect specific functions.

### Further Customization
Refer to the contribution guide for detailed instructions on making advanced modifications to the application.

---

# Setting up postgres database
### 1. Prerequisites
- **PostgreSQL Server**: Ensure you have a PostgreSQL server running locally or remotely.
- **Python Library**: Install `psycopg2`, a PostgreSQL adapter for Python.
  - Use the following command:
    ```bash
    pip install psycopg2
    ```
- **Database Migration**: If you want to use the same schema, migrate your SQLite database to PostgreSQL using a tool like `pgloader` or manually recreate the schema and data.

---

### 2. Update Database Connection
Change connection logic and query execution logic

refer to documentation here: https://pypi.org/project/psycopg2/