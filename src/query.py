from openai import OpenAI
# 1. Create a file called apikey.py
# 2. Create a variable (String) called api_key
# 3. Add api key to that variable
import apikey

client = OpenAI(api_key=apikey.api_key)

# Define the database schema context
schema = """
Employees table: EmployeeID, Name, Department, Salary
Departments table: DepartmentID, DepartmentName
"""

# Function to interact with OpenAI API and generate SQL query
def get_sql_query(user_query, schema):
    response = client.chat.completions.create(model="gpt-4o",
    messages=[
        {"role": "system", "content": "Generate only the SQL query based on the database schema: {schema}. Do not provide any explanation, just the SQL code. Do not even add the markdown syntax to format the code. Only provide the SQL code. If the user requests something that you determine to be outside the defined schema, try to find the closest match if not, provide an empty output."},
        {"role": "user", "content": user_query}
    ],
    max_tokens=100)
    sql_query = response.choices[0].message.content.strip()
    return sql_query

# Main loop
def main():
    print("Enter your natural language query (type 'exit' to quit):")
    while True:
        # Get user input
        user_query = input("User input: ")

        # Exit condition
        if user_query.lower() == 'exit':
            print("Exiting the program.")
            break

        # Call function to get SQL query
        sql_query = get_sql_query(user_query, schema)

        # Print the translated SQL query
        print(f"Generated SQL query: {sql_query}\n")

# Entry point
if __name__ == "__main__":
    main()
