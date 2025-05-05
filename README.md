# AI SQL Agent per Database di Logistica

Un'applicazione AI intelligente che interroga un database logistico in linguaggio naturale, trasformando domande in query SQL automatiche grazie all’integrazione di **LangChain**, **OpenAI** e **SQLite**.

---

## Descrizione del Progetto

Questo progetto dimostra come un agente AI possa essere utilizzato per **interagire con un database relazionale** in modo conversazionale. L’utente può porre domande complesse in linguaggio naturale (es. "Quali clienti hanno effettuato più di 5 ordini?") e ricevere risposte dettagliate, generate tramite query SQL create automaticamente.

L'agente sfrutta esempi, regole di comportamento e accesso diretto a un database SQLite per fornire risposte contestualizzate e corrette.

---

## Stack Tecnologico

- **Python 3.11+**
- **LangChain** – framework per la costruzione di agenti AI
- **OpenAI** – modello linguistico per l’elaborazione del linguaggio naturale
- **SQLite + SQLAlchemy** – database relazionale locale e ORM
- **gdown** – per scaricare il file `.db` da Google Drive

---

## Funzionalità

- Domande in linguaggio naturale  
- Conversione automatica in SQL  
- Risposte dettagliate con spiegazione  
- Gestione sicura delle query (solo lettura)  
- Esempi predefiniti few-shot per l’apprendimento contestuale  
- Agent modulari e componibili

---

## Architettura e Spiegazione dei File

### `sql_agent_db.py`

> **Funzione:** Crea l’agente AI principale che interroga il database.

Contenuti principali:
- Caricamento del database SQLite da Google Drive (se non esiste localmente)
- Creazione dell’**engine SQLAlchemy** e connessione al DB
- Definizione di esempi few-shot: domande e le relative query SQL
- Costruzione del prompt system con istruzioni su tabelle, logica, filtri, limiti
- Inizializzazione del toolkit LangChain per il database
- Creazione dell’agente con `create_sql_agent`, usando il tipo `OPENAI_FUNCTIONS`

### `custom_db_agent.py`

> **Funzione:** Contiene una variante semplificata o personalizzata dell’agente.

Contenuti principali:
- Possibile uso per agenti con strumenti aggiuntivi o modifiche nel comportamento
- Inizializzazione separata del toolkit e dell’agente
- Utile per sperimentare versioni alternative dell’agente standard

### `app.py`

> **Funzione:** Entry point per eseguire l’agente e testarlo da terminale o integrarlo in un’API.

Contenuti principali:
- Importa la funzione `db_agent()` da `sql_agent_db.py`
- Inizializza l’agente e lancia un loop di input da terminale
- Permette all’utente di porre domande manualmente, ottenendo risposte dettagliate
- Uscita con `exit` per terminare la sessione

---

## Esempi di Domande Supportate

- How many shipments were delivered on time?
- What is the total value of orders from client 'CLI123'?
- Which article has the highest price?
- How many orders were registered in March 2024?
- What is the average delivery delay for all shipments?

L’agente interpreta queste domande, consulta lo schema del database e genera una query SQL come questa:

```sql
SELECT COUNT(*) FROM Spedizioni 
WHERE "Data Consegna" <= "Data Prevista Consegna" AND "Flag Consegna Vettore" = 1;
```

---

## Sicurezza e Limitazioni

- Solo query **READ** (nessuna modifica ai dati: INSERT/UPDATE/DELETE)
- Validazione della query prima dell’esecuzione
- In caso di errore SQL, l’agente **rigenera automaticamente la query**
- I risultati sono limitati (default `top_k=10`) per evitare overload

---

## Dataset

Il database contiene le seguenti tabelle:
- **Clienti** – informazioni su clienti, zona geografica, classe
- **Ordini** – ordini effettuati, quantità, valore, date
- **Spedizioni** – dati su consegne, ritardi, vettori
- **Articoli** – articoli ordinati, prezzo, categoria

Il file `.db` viene scaricato automaticamente da Google Drive al primo avvio.

---

## Estendibilità

Il progetto è stato pensato in modo modulare:
- Aggiunta facile di strumenti personalizzati (ad esempio per file CSV o API esterne)
- Estendibile con **memorie LangChain** o **retrieval-augmented generation (RAG)**
- Possibilità di integrazione in una Web API o GUI interattiva
