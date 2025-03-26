# from openai import OpenAI
# import apikey

# # OpenAI API Key
# client = OpenAI(api_key=apikey.api_key)

# # Define the XiYanSQL-style prompt
# nl2sql_template_cn = """你是一名{dialect}专家，现在需要阅读并理解下面的【数据库schema】描述，以及可能用到的【参考信息】，并运用{dialect}知识生成sql语句回答【用户问题】。
# 【用户问题】
# {question}

# 【数据库schema】
# {db_schema}

# 【参考信息】
# {evidence}

# 【用户问题】
# {question}

# ```sql"""

# # Fill in prompt values
# dialect = "SQLite"  # Change to "MySQL" or "PostgreSQL" as needed
# db_schema = "C:/Users/SIM-PC-1/Desktop/sakila-sqlite3/sakila_master.db"
# question = "movies that are rated PG-13"
# evidence = ""

# prompt = nl2sql_template_cn.format(dialect=dialect, db_schema=db_schema, question=question, evidence=evidence)

# # Call OpenAI API (GPT-4o)
# response = client.chat.completions.create(
#         model="gpt-4o",
#         messages=[
#             {"role": "system", "content": "You are an SQL expert. Generate SQL queries based on the user's request."},
#             {"role": "user", "content": prompt}
#         ],
#         max_tokens=400
#     )

# # Extract the SQL response
# generated_sql = response.choices[0].message.content.strip()

# # Print the generated SQL query
# print("Generated SQL Query:\n", generated_sql)


from openai import OpenAI
import apikey
import os


# OpenAI API Key
client = OpenAI(api_key=apikey.api_key)
dialect = "SQLite"  # Change to "MySQL" or "PostgreSQL" as needed
db_schema = "C:/Users/SIM-PC-1/Desktop/WikiSQL/data/train.db"
question = "What school did Patrick O'Bryant play for?"
evidence = ""

# 🟢 Step 1: Schema Linking
schema_linking_prompt = f"""
你是一名{dialect}数据库专家，负责分析用户问题，并从数据库schema中找到最相关的表和列。

【数据库schema】
{db_schema}

【用户问题】
{question}

请列出与问题相关的表和列：
"""

schema_response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "你是一名SQL专家，分析schema并提取相关表和列。"},
        {"role": "user", "content": schema_linking_prompt}
    ],
    max_tokens=200
)
relevant_schema = schema_response.choices[0].message.content.strip()

# 🟢 Step 2: Candidate Generation
candidate_prompt = f"""
基于以下数据库schema和用户问题，生成多个可能的SQL查询：

【数据库schema】
{relevant_schema}

【用户问题】
{question}

请生成3种可能的SQL查询：
"""
candidate_response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "你是一名SQL专家，生成多个SQL查询候选项。"},
        {"role": "user", "content": candidate_prompt}
    ],
    max_tokens=600
)
sql_candidates = candidate_response.choices[0].message.content.strip()

# 🟢 Step 3: Candidate Selection
selection_prompt = f"""
以下是多个可能的SQL查询，请选择最符合用户问题的SQL，并进行优化。

【SQL候选查询】
{sql_candidates}

请返回最佳SQL查询：
"""
selection_response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "你是一名SQL优化专家，选择最佳SQL。"},
        {"role": "user", "content": selection_prompt}
    ],
    max_tokens=400
)
final_sql = selection_response.choices[0].message.content.strip()

# 🔥 Output the final optimized SQL query
print("Final Optimized SQL Query:\n", final_sql)
