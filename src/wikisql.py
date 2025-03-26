import sqlite3

db_path = "C:/Users/SIM-PC-1/Desktop/WikiSQL/data/train.db"
output_file = "wikisql_schema.txt"

# Connect to SQLite
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

# Open the file to save schema
with open(output_file, "w", encoding="utf-8") as f:
    for table in tables:
        table_name = table[0]
        f.write(f"\n🔹 Schema for table: {table_name}\n")
        
        cursor.execute(f"PRAGMA table_info({table_name});")
        schema = cursor.fetchall()

        for col in schema:
            line = f"Column: {col[1]} | Type: {col[2]}\n"
            f.write(line)

conn.close()

print(f"Schema saved to {output_file}")
