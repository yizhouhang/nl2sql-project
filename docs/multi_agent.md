

# Architecture for multi-agent Natural Language to SQL translator

## High Level View

### Problems to be addressed
  1. Concise prompting - long prompts often cause LLMs to halucinate as they have a limited focus/attention window
  2. Problem complexity - very complex natural language queries can be hard for LLMs to immediately translate to SQL code
  3. Detecting inadequate details - LLMs tend to showcase extreme behaviour based on prompts, where it will either
     1. Always ask for additional details for a natural language prompt
     2. Always produce code that is likely not functional (and lead to runtime errors) where it is to ask for additional details/context
  4. Non-compliance in using exact column names/finding columns that match
  5. Seperating concerns - when asked to visualise data, LLMs can often focus more on the visalisation rather than fetching the exact data to be visalised

### Agents
I will follow the seperation of concerns principle and assign each problem to one agent, and overll decrease prompt complexity for each agent

  1. Selector 
    - Select the relvant tables by identifying entities and relationships in the natural language, and find the closest mapping of it in the schema
    - Ensures all entities/relationship listed is available in the schema, if not ask for additional details

  2. Decomposer
    - Decompose complex queries into simpler ones with reasoning chains (which is now functionality of GPT o1 models - hence we will experiemnt with this)
  
  3. Error Handler
    - Receives execution errors and the last executed SQL query and refines it with the schema such that SQL query is compatible with the database and language used
  
  4. Data Visualiser
    - Receives final executable SQL query and uses it (especially SELECT statements) to forulate a data visualisation script
    - This script will be run on the tabular data retreived from the executed SQL query
  
  5. Query seperator
    - This will split a data visualisation query into 2 prompts
    - 1 - A query to retreive the data via SQL
    - 2 - A prompt which will take the final working SQL query and formulate a script to visualise the tabular data (with column names, ect)