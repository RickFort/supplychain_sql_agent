# Import langchain LLM function -> OpenAI
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
# Import Langchain function for vettorizzation
from langchain_community.vectorstores import FAISS
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
# Import Langchain Prompt function
from langchain_core.prompts import (ChatPromptTemplate, FewShotPromptTemplate,
                                    MessagesPlaceholder, PromptTemplate, SystemMessagePromptTemplate,)
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
from env_config import OPENAI_API_KEY, LLM_MODEL, EMBEDDING_MODEL, DB_PATH, DB_NAME, FILE_ID
import gdown
import os

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
output_path = f"{DB_PATH}{DB_NAME}"

if not os.path.exists(output_path):
    url = f"https://drive.google.com/uc?id={FILE_ID}"
    gdown.download(url, output_path, quiet=False)


engine = create_engine(
    f"sqlite:////{output_path}",
    poolclass=StaticPool)
db = SQLDatabase(engine)

examples = [
    {
        "input": "How many shipments were delivered on time?",
        "query": """SELECT COUNT(*) FROM Spedizioni WHERE "Data Consegna" <= "Data Prevista Consegna" AND "Flag Consegna Vettore" = 1;""",
    },
    {
        "input": "What is the total value of orders from client 'CLI123'?",
        "query": """SELECT SUM(Valore) FROM Ordini WHERE "Codice Cliente" = 'CLI123';""",
    },
    {
        "input": "Which article has the highest price?",
        "query": """SELECT "Codice Articolo", Prezzo FROM Articoli ORDER BY Prezzo DESC LIMIT 1;""",
    },
    {
        "input": "How many orders were registered in March 2024?",
        "query": """SELECT COUNT(*) FROM Ordini WHERE strftime('%Y-%m', "Data Registrazione") = '2024-03';""",
    },
    {
        "input": "What is the average delivery delay for all shipments?",
        "query": """SELECT AVG(julianday("Data Consegna") - julianday("Data Prevista Consegna")) AS AvgDelay FROM Spedizioni WHERE "Data Consegna" IS NOT NULL AND "Data Prevista Consegna" IS NOT NULL;""",
    },
    {
        "input": "List all clients from 'UE' zone.",
        "query": """SELECT "Codice Cliente" FROM Clienti WHERE Zona = 'UE';""",
    },
    {
        "input": "What is the total quantity ordered for article 'ART456'?",
        "query": """SELECT SUM(Quantita) FROM Ordini WHERE "Codice Articolo" = 'ART456';""",
    },
    {
        "input": "Which customers placed more than 5 orders?",
        "query": """SELECT "Codice Cliente", COUNT(*) as NumOrdini FROM Ordini GROUP BY "Codice Cliente" HAVING NumOrdini > 5;""",
    },
    {
        "input": "Which delivery companies (vettori) have the most delayed shipments?",
        "query": """SELECT "Codice Vettore", COUNT(*) as NumRitardi FROM Spedizioni WHERE "Data Consegna" > "Data Prevista Consegna" GROUP BY "Codice Vettore" ORDER BY NumRitardi DESC;""",
    },
    {
        "input": "What is the average order value per client class?",
        "query": """SELECT Clienti.Classe, AVG(Ordini.Valore) as AvgValore FROM Ordini JOIN Clienti ON Ordini."Codice Cliente" = Clienti."Codice Cliente" GROUP BY Clienti.Classe;""",
    },
]



def initialize_sql_agent(db=db,
                         examples=examples,
                         EMBEDDING_MODEL=EMBEDDING_MODEL,
                         LLM_MODEL=LLM_MODEL,
                         top_k=5):
    llm_model = ChatOpenAI(model=LLM_MODEL, temperature=0)
    toolkit = SQLDatabaseToolkit(db=db, llm=llm_model)
    print("**Tool Descriptions**")
    for tool in toolkit.get_tools():
        print(f"Tool name: {tool.name}\nDescription: {tool.description}\n")
    
    example_selector = SemanticSimilarityExampleSelector.from_examples(
        examples,
        OpenAIEmbeddings(model=EMBEDDING_MODEL),
        FAISS,
        k=top_k
    )
    example_prompt = PromptTemplate(
        input_variables=["input", "query"],
        template="Domanda: {input}\nSQL: {query}"
    )
    few_shot_prompt = FewShotPromptTemplate(
        example_selector=example_selector,
        example_prompt=example_prompt,
        prefix=(
            """Sei un assistente AI che traduce domande in linguaggio naturale in query SQL valide per un database {dialect}.
            La data corrente è {date}.
            Assicurati che le query siano compatibili con il dialetto SQL '{dialect}'.
            NON eseguire comandi DML (INSERT, UPDATE, DELETE, DROP).
            Linea guida per le tabelle:
            - Spedizioni: per date, ritardi, consegne
            - Clienti: per zone, classi, localizzazione
            - Ordini: per quantità, valore, date previste
            - Articoli: per prodotti, prezzi, categorie
            I campi data sono nel formato 'YYYY-MM-DD'."""
        ),
        suffix="Domanda: {input}\nSQL:",
        input_variables=["input", "dialect", "top_k", "date"],
    )

    few_shot_prompt_partial = few_shot_prompt.partial(
        dialect=toolkit.dialect,
        top_k=top_k,
        date=datetime.now().strftime("%Y-%m-%d")
    )

    return create_sql_agent(
        llm=llm_model,
        toolkit=toolkit,
        verbose=True,
        agent_type=AgentType.OPENAI_FUNCTIONS ,
        agent_executor_kwargs={
            "prompt": few_shot_prompt_partial
        }
    )
