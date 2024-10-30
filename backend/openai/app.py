from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os 
import api_keys
from function_definition import mini_retrieve_similar_keywords_definition, intermediary_dataframe_retrieval_definition, schema_check_definition
from list_of_tools import mini_retrieve_similar_keywords
from basic_functions import deploy_assistant, add_message, run_assistant, get_answer

app = Flask(__name__)
CORS(app)

os.environ['OPENAI_API_KEY'] = api_keys.openai_key


threads = {}

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message')
        thread_id = data.get('threadId')

        if not user_message:
            return jsonify({'error': 'No message provided'}), 400


        if thread_id and thread_id in threads:
            thread = threads[thread_id]
        else:
            thread = openai.beta.threads.create()
            threads[thread.id] = thread
            thread_id = thread.id


        add_message(thread, user_message, role='user')
        
        run = run_assistant(
            assistant_id="asst_k2yi0kNWxlgBOAlsB690EH8c",  
            thread=thread,
            question=user_message
        )

        annotations, message_content = get_answer(run, thread)
        add_message(thread, message_content, role='assistant')

        return jsonify({
            'threadId': thread_id,
            'message': message_content,
            'annotations': annotations
        })

    except Exception as e:
        print(f"Error: {str(e)}") 
        return jsonify({'error': str(e)}), 500

@app.route('/api/new-thread', methods=['POST'])
def new_thread():
    try:
        thread = openai.beta.threads.create()
        threads[thread.id] = thread
        return jsonify({'threadId': thread.id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)