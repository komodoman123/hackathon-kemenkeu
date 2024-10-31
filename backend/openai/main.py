import openai
import os
import api_keys
import sqlite3
import pandas as pd
from flask_cors import CORS
from flask import Flask, request, jsonify
from function_definition import (
    mini_retrieve_similar_keywords_definition,
    intermediary_dataframe_retrieval_definition,
    schema_check_definition,
    bar_chart_tool_definition
)
from basic_functions import deploy_assistant, add_message, run_assistant, get_answer

app = Flask(__name__)
os.environ['OPENAI_API_KEY'] = api_keys.openai_key
CORS(app)
all_tools = [
    mini_retrieve_similar_keywords_definition,
    schema_check_definition,
    intermediary_dataframe_retrieval_definition,
    bar_chart_tool_definition
]

threads = {}

def get_intermediary_data():
    try:
        conn = sqlite3.connect('intermediary.db')
        df = pd.read_sql_query("SELECT * FROM intermediary_table", conn)
        return df.to_dict(orient='records')
    except:
        return None
    finally:
        conn.close()

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    session_id = data.get('session_id', 'default')
    question = data.get('message')
    
    if session_id not in threads:
        threads[session_id] = openai.beta.threads.create()
    
    thread = threads[session_id]
    
    add_message(thread, question, role='user')
    run = run_assistant(
        assistant_id="asst_3gKdwwX5uEJKc9RwXHUYenwD",
        thread=thread,
        question=question
    )
    annotations, message_content, tool_info = get_answer(run, thread)
    add_message(thread, message_content, role='assistant')
    
    # Get intermediary data if it exists
    df_data = get_intermediary_data()
    
    response = {
        'response': message_content,
        'session_id': session_id
    }
    
    if df_data:
        response['data'] = df_data
    
    if tool_info:  # Only add tool_info if it exists
        response['tool_info'] = tool_info
    
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True, port=5000)