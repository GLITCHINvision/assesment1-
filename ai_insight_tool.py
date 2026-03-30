import streamlit as st
import sqlite3
import pandas as pd
import google.generativeai as genai
import os
from dotenv import load_dotenv
import re


load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")


if not API_KEY:
    st.error("Hold up! I'm missing the Gemini API Key. Please paste it into your `.env` file.")
    st.stop()


genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash') 

DB_PATH = "growify_database.db"


def get_db_schema():
    """This grabs the column names from our database so the AI knows exactly what tables exist."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
   
        schema = "Here is exactly how our database is structured right now.\n"
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            col_details = [f"{col[1]} ({col[2]})" for col in columns] 
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
        return str(e) 



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


st.set_page_config(page_title="Growify AI Insight Tool", layout="wide")
st.title(" Growify Digital - AI Insight Tool")
st.markdown("ask me anything about our clean Shopify stats or the dirty Facebook ad performance. The AI translates everything for you instantly.")


if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

for msg in st.session_state['chat_history']:
    if msg['role'] == "user":
        st.chat_message("user").markdown(msg['content'])
    else:
        st.chat_message("assistant").markdown(msg['content'])

user_input = st.chat_input("E.g., Which region had the worst Cost Per Click?")

if user_input:
 
    st.chat_message("user").markdown(user_input)
    st.session_state['chat_history'].append({"role": "user", "content": user_input})
    
    with st.spinner('Thinking in SQL...'):
    
        generated_sql = text_to_sql(user_input, st.session_state['chat_history'])
    
    with st.expander("Peek at the Generated SQL"):
        st.code(generated_sql, language='sql')
        
    with st.spinner('Pulling from the Database...'):
        
        sql_df = execute_sql(generated_sql)
        
    if isinstance(sql_df, str): 
       
        final_answer = f"Oops! I tried pulling that but hit a database error: {sql_df}. Maybe rephrase it?"
    else:
         with st.expander("Peek at the Database Results"):
            st.dataframe(sql_df)
         
         with st.spinner('Writing a friendly summary...'):
  
             result_str = sql_df.to_string(index=False)
             final_answer = sql_result_to_insight(user_input, generated_sql, result_str)
             

    st.chat_message("assistant").markdown(final_answer)
    st.session_state['chat_history'].append({"role": "assistant", "content": final_answer})
