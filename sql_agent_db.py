# Import langchain LLM function -> OpenAI
from langchain_openai import ChatOpenAI
# Import langchain Agent DB
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain.agents import create_sql_agent
from langchain_community.utilities.sql_database import SQLDatabase
from langchain.agents.agent_types import AgentType
# Import Libraries for DB
import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
# Import Other Libraries
from datetime import datetime
from env_config import OPENAI_API_KEY, LLM_MODEL, DB_PATH, DB_NAME, FILE_ID
import gdown
import os

#impostiamo le variabili da usare per l'agente
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

output_path = f"{DB_PATH}{DB_NAME}"

if not os.path.exists(output_path):
    url = f"https://drive.google.com/uc?id={FILE_ID}"
    gdown.download(url, output_path, quiet=False)


engine = create_engine(
    f"sqlite:////{output_path}",
    poolclass=StaticPool)
db = SQLDatabase(engine)

system_prefix ="""
You are an agent designed to interact with a SQL database.
You are an expert at answering questions about logistics, shipments, clients, and product orders.
Given an input question, create a syntactically correct {dialect} query to run, then look at the results of the query and return the answer.
Always start by checking the schema of the available tables.
Unless the user specifies a specific number of examples they wish to obtain, always limit your query to at most {top_k} results.
You can order the results by a relevant column to return the most interesting examples in the database.
Never query for all the columns from a specific table — only ask for the relevant columns given the question.
You have access to tools for interacting with the database.
Only use the given tools. Only use the information returned by the tools to construct your final answer.
You MUST double check your query before executing it. If you get an error while executing a query, rewrite the query and try again.
DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.
The current date is {date}.
Use the following guidelines when choosing which table to query:
- For questions about **shipments**, delays, delivery dates or carriers, use the `Spedizioni` table.
- For questions about **clients**, zones, classes or locations, use the `Clienti` table.
- For questions about **orders**, values, delivery dates, and quantities, use the `Ordini` table.
- For questions about **products or articles**, prices or categories, use the `Articoli` table.
For date comparisons, assume all date fields are in `YYYY-MM-DD` format unless stated otherwise.
If the question is not related to the database, just return "I don't know" as the answer.
"""

format_instructions = """
## Use the following format:
Question: the input question you must answer.
Thought: you should always think about what to do.
Action: the action to take, should be one of [{tool_names}].
Action Input: the input to the action.
Observation: the result of the action.
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer.
Final Answer: the final answer to the original input question.
Example of Final Answer:
<=== Beginning of example
Action: query_sql_db
Action Input: 
SELECT
    Ordini."Codice Articolo",
    Ordini.Quantità,
    Ordini.Valore
FROM Ordini
INNER JOIN Articoli ON Ordini."Codice Articolo" = Articoli."Codice Articolo"
WHERE "Data Consegna Prevista" BETWEEN DATE('now') AND DATE('now', '+7 days')
      and "Categoria"='Categoria1'
Observation:
[('Articolo10', 72, 2759.04), ('Articolo10', 48, 1839.36), ('Articolo11', 8, 86.56), ('Articolo13', 45, 1948.5), ('Articolo13', 72, 3117.6), ('Articolo28', 54, 1650.7), ('Articolo32', 81, 1362.4), ('Articolo34', 58, 2781.68), ('Articolo34', 83, 3980.68), ('Articolo35', 58, 2820.54)]
Thought:I now know the final answer
Final Answer: Cod Item Articolo34 is the most order next 7 days for the category 1. the quantity order are 141 for a sell value of 6762.36.
Explanation:
I queried the `Ordini` table for the `Valore` column for all cod items where the category is 'Categoria1'
and the date is between now and now + 7 days. The query returned a list of tuples
with the quantity and value for each cod item in the next 7 days. To answer the question,
I took the sum of quantity and value for each item and order by descendig and take the first cod item.
I used the following query
```sql
SELECT Ordini."Codice Articolo", Ordini.Quantità, Ordini.Valore FROM Ordini INNER JOIN Articoli ON Ordini."Codice Articolo" = Articoli."Codice Articolo" WHERE "Data Consegna Prevista" BETWEEN DATE('now') AND DATE('now', '+7 days') and "Categoria"='Categoria1'
```
===> End of Example
"""

def db_agent(model_llm=LLM_MODEL,
             system_prefix=system_prefix,
             format_instructions =format_instructions,
             top_k=10):
    llm = ChatOpenAI(model=model_llm,
                     temperature=0.0,
                     verbose=True)
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    context = toolkit.get_context()
    print("**Info del DB**")
    print(context)
    tools = toolkit.get_tools() 
    print("**Lista dei Tools Predefiniti**")
    tool_names = [tool.name for tool in tools]
    print(tool_names)
    # Ottieni la data corrente in formato stringa
    formatted_prefix = system_prefix.format(
        dialect =toolkit.dialect,
        top_k=top_k,
        date = datetime.now().strftime("%Y-%m-%d")
    )
    return create_sql_agent(llm=llm,
                            toolkit=toolkit,
                            prefix=formatted_prefix ,
                            verbose=True,
                            format_instructions=format_instructions,
                            agent_type=AgentType.OPENAI_FUNCTIONS,)
