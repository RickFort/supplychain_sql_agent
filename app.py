import streamlit as st
from sql_agent_db import db_agent
from custom_db_agent import initialize_sql_agent
from datetime import datetime
from env_config import SQL_AGENT_FEW_SHOT

# Imposta il titolo della webapp
st.set_page_config(page_title="Supply Chain AI Agent", layout="centered")
st.title("📦 Supply Chain SQL Agent")
st.write("Fai una domanda sul database supply_chain.db")

# Istanzia l'agente (memorizzazione per evitare ricarichi inutili)
@st.cache_resource
def load_agent(SQL_AGENT_FEW_SHOT=SQL_AGENT_FEW_SHOT):
    if SQL_AGENT_FEW_SHOT==True:
        return initialize_sql_agent()
    else:
        return db_agent()

agent = load_agent()

# Campo input dell'utente
query = st.text_area("Inserisci la tua domanda:", height=100, placeholder="Es: Quanti spedizioni sono state spedite in tempo?")

# Esecuzione agente
if st.button("Esegui") and query.strip():
    with st.spinner("Sto interrogando il database..."):
        try:
            response = agent.invoke(query)
            st.success("✅ Risposta trovata:")
            st.write(response)
        except Exception as e:
            st.error("❌ Errore durante l'interrogazione.")
            st.exception(e)
