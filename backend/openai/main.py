import openai
import os
import api_keys
import sqlite3
import pandas as pd
from flask_cors import CORS
from flask import Flask, request, jsonify
from flask_socketio import SocketIO 
from function_definition import (
    mini_retrieve_similar_keywords_definition,
    intermediary_dataframe_retrieval_definition,
    schema_check_definition,
    bar_chart_tool_definition,
    line_chart_tool_definition,
    histogram_tool_definition,
    pie_chart_tool_definition
)
from basic_functions import deploy_assistant, add_message, run_assistant, get_answer

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")  

os.environ['OPENAI_API_KEY'] = api_keys.openai_key

all_tools = [mini_retrieve_similar_keywords_definition, 
             schema_check_definition, 
             intermediary_dataframe_retrieval_definition, 
             bar_chart_tool_definition,
             line_chart_tool_definition,
             histogram_tool_definition,
             pie_chart_tool_definition]

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
    
    def progress_callback(status, msg):
        print(f"Sending progress update: {msg}")  
        socketio.emit('progress', {
            'session_id': session_id,
            'message': msg
        })

        socketio.sleep(0)
    
    add_message(thread, question, role='user')
    run = run_assistant(
        assistant_id="asst_2Pna3kraHtUxZZSBXRljNQJM",
        thread=thread,
        question=question
    )
    
    annotations, message_content, charts_info = get_answer(run, thread, progress_callback)
    add_message(thread, message_content, role='assistant')
    
    df_data = get_intermediary_data()
    
    response = {
        'response': message_content,
        'session_id': session_id
    }
    
    if df_data:
        response['data'] = df_data
    
    if charts_info:
        if not isinstance(charts_info, list):
            charts_info = [charts_info]
        response['charts_info'] = charts_info
    
    return jsonify(response)
@socketio.on('connect')
def handle_connect():
    print('Client connected to WebSocket')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected from WebSocket')
if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)  # Change this line