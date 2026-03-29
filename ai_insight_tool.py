import streamlit as st
import sqlite3
import pandas as pd
import google.generativeai as genai
import os
from dotenv import load_dotenv
import re

# ==========================================
# Phase 1: Waking up the AI
# ==========================================
# We use a .env file to hide our secret API key so no one steals it.
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

# If you forgot to paste your key into the .env file, the app stops here and warns you.
if not API_KEY:
    st.error("Hold up! I'm missing the Gemini API Key. Please paste it into your `.env` file.")
    st.stop()

# Tell Gemini to wake up and start using our free-tier model that we proved works!
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash') 

# Here's where our perfectly cleaned database lives 
DB_PATH = "growify_database.db"

# ==========================================
# Phase 2: Building the Robot's SQL Brain
# ==========================================
def get_db_schema():
    """This grabs the column names from our database so the AI knows exactly what tables exist."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # We start building a giant string of text to send to Gemini
        schema = "Here is exactly how our database is structured right now.\n"
        
        # We ask SQLite broadly: 'Hey, what tables do you have?'
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        # We loop through every table (like sales_fact, date_dim) and grab all the column names
        for table in tables:
            table_name = table[0]
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            col_details = [f"{col[1]} ({col[2]})" for col in columns] # "Name (Type)" -> "Spend (DECIMAL)"
            schema += f"Table: {table_name}\nColumns: {', '.join(col_details)}\n\n"
            
        conn.close()
        return schema
    except Exception as e:
        return f"Uh oh. Hit an error grabbing the database map: {e}"

def execute_sql(query):
    """This function just takes whatever SQL code the AI wrote and actually runs it against our database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        return str(e) # If the AI wrote broken SQL, we catch the error instead of crashing

# ==========================================
# Phase 3: The AI Translators
# ==========================================
def text_to_sql(user_question, chat_history):
    """This reads your normal english question and forces the AI to whisper back pure SQL code."""
    schema_context = get_db_schema()
    
    # We pass the last 3 messages so if you say 'what about last month?', it remembers what you were talking about!
    history_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_history[-3:]]) if chat_history else "None"
    
    prompt = f"""
    You are an expert Data Analyst reading this SQLite database:
    {schema_context}
    
    The user is asking a question. Please generate a highly optimized SQLite query to answer the question.
    Only return the SQL query itself, with NO markdown formatting, NO backticks, and NO explanations. Just raw SQL code.
    
    Recent Chat Context (for follow ups):
    {history_str}
    
    User Question: {user_question}
    """
    
    response = model.generate_content(prompt)
    # We strip any weird markdown formatting the AI tries to sneak in
    raw_sql = response.text.replace('```sql', '').replace('```', '').strip()
    return raw_sql

def sql_result_to_insight(user_question, raw_sql, sql_results):
    """Once we have the raw numbers from the database, this makes the AI talk back in normal English."""
    prompt = f"""
    You are a Marketing AI Assistant answering: "{user_question}"
    
    To find the answer, we automatically ran this SQL Query:
    {raw_sql}
    
    The database returned these raw specific numbers:
    {sql_results}
    
    Using ONLY those raw numbers, give me a friendly, short, plain-English summary answering my question. 
    Don't be a robot—act like a normal data analyst updating me. Don't mention that you used SQL to do it.
    """
    response = model.generate_content(prompt)
    return response.text

# ==========================================
# Phase 4: Setting up the Web Screen (Streamlit)
# ==========================================
st.set_page_config(page_title="Growify AI Insight Tool", layout="wide")
st.title("📈 Growify Digital - AI Insight Tool")
st.markdown("ask me anything about our clean Shopify stats or the dirty Facebook ad performance. The AI translates everything for you instantly.")

# Create a memory box so the chat interface remembers what we said earlier
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

# Draw all our past messages on the screen
for msg in st.session_state['chat_history']:
    if msg['role'] == "user":
        st.chat_message("user").markdown(msg['content'])
    else:
        st.chat_message("assistant").markdown(msg['content'])

# Build the cool little textbox at the bottom of the screen
user_input = st.chat_input("E.g., Which region had the worst Cost Per Click?")

if user_input:
    # 1. Print your message to the screen and save it to memory
    st.chat_message("user").markdown(user_input)
    st.session_state['chat_history'].append({"role": "user", "content": user_input})
    
    with st.spinner('Thinking in SQL...'):
        # 2. Tell the AI to convert your text to SQL
        generated_sql = text_to_sql(user_input, st.session_state['chat_history'])
    
    with st.expander("Peek at the Generated SQL"):
        st.code(generated_sql, language='sql')
        
    with st.spinner('Pulling from the Database...'):
        # 3. Reach into our fresh SQLite database to grab the exact rows/columns needed
        sql_df = execute_sql(generated_sql)
        
    if isinstance(sql_df, str): 
        # If the SQL failed, the text here tells you what went wrong.
        final_answer = f"Oops! I tried pulling that but hit a database error: {sql_df}. Maybe rephrase it?"
    else:
         with st.expander("Peek at the Database Results"):
            st.dataframe(sql_df)
         
         with st.spinner('Writing a friendly summary...'):
             # 4. Give the raw numbers back to the AI so it formats a normal text response
             result_str = sql_df.to_string(index=False)
             final_answer = sql_result_to_insight(user_input, generated_sql, result_str)
             
    # 5. Print out the final answer from the AI on the screen!
    st.chat_message("assistant").markdown(final_answer)
    st.session_state['chat_history'].append({"role": "assistant", "content": final_answer})
