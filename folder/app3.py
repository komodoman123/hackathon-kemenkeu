from flask import Flask, request, jsonify, session
from flask_session import Session
import sqlite3
import pandas as pd
import json
import io
import matplotlib.pyplot as plt
import seaborn as sns
import base64
import os
import datetime
import requests
import uuid

app = Flask(__name__, static_url_path='/images', static_folder='images')

# OPENAI API KEY is ommited
openai_api_key = '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'  

def get_visualization_type(df_head):
    prompt = f"""
Given the following data sample:
{df_head.to_csv(index=False)}

and based on this query:
Suggest the most appropriate visualization type (e.g., bar chart, line chart, scatter plot) and the columns to use for x and y axes.
Provide the answer in JSON format, enclosed in triple backticks like ```{{ ... }}```.
"""
    # Use OpenAI API to get visualization type
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai_api_key}"
    }

    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are a data visualization assistant."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 150,
        "temperature": 0,
        "n": 1
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

    if response.status_code == 200:
        response_json = response.json()
        content = response_json['choices'][0]['message']['content'].strip()
        # Extract JSON between triple backticks
        match = re.search(r'```(.*?)```', content, re.DOTALL)
        if match:
            json_str = match.group(1)
            try:
                viz_info = json.loads(json_str)
            except json.JSONDecodeError:
                viz_info = None
        else:
            viz_info = None
        return viz_info
    else:
        print("Error:", response.status_code, response.text)
        return None

def create_visualization(df, viz_info):
    plt.figure(figsize=(10, 6))

    chart_type = viz_info.get('chart_type')
    x_axis = viz_info.get('x_axis')
    y_axis = viz_info.get('y_axis')
    title = viz_info.get('title', 'Data Visualization')

    if not all([chart_type, x_axis, y_axis]):
        return None  # Missing required information

    if chart_type.lower() in ['bar', 'bar chart']:
        sns.barplot(data=df, x=x_axis, y=y_axis)
    elif chart_type.lower() in ['line', 'line chart']:
        sns.lineplot(data=df, x=x_axis, y=y_axis)
    elif chart_type.lower() in ['scatter', 'scatter plot']:
        sns.scatterplot(data=df, x=x_axis, y=y_axis)
    else:
        return None  # Unsupported chart type

    plt.title(title)
    plt.tight_layout()

    # Save the image to a file
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    file_name = f"visualization_{timestamp}.png"
    file_path = os.path.join('images', file_name)

    if not os.path.exists('images'):
        os.makedirs('images')

    plt.savefig(file_path)
    plt.close()

    return file_path  

# encode image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def get_chart_insights_with_image(image_path):

    base64_image = encode_image(image_path)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai_api_key}"
    }

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Please analyze this chart and provide insights."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 300
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

    if response.status_code == 200:
        response_json = response.json()
        insights = response_json['choices'][0]['message']['content'].strip()
        return insights
    else:
        print("Error:", response.status_code, response.text)
        return None

def generate_sql_query(user_request, table_schema):
    prompt = f"""
You are an assistant that converts natural language requests into SQL queries.

**Instructions:**

- Only generate **safe**, **read-only** `SELECT` SQL queries.
- Do **not** include any other SQL statements besides `SELECT`.
- Do **not** use `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, `CREATE`, or any other data modification or schema-changing commands.
- The SQL query should only reference the tables and columns provided in the table schema.
- If the user's request cannot be answered with a `SELECT` query using the given schema, respond with an error message like "I'm sorry, but I cannot generate a query for that request."

**Table Schema:**

{table_schema}

**User Request:**

"{user_request}"

Provide only the SQL query (without any explanations or additional text) or the error message if applicable.
"""
    # OpenAI API call
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai_api_key}"
    }

    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant that converts natural language into SQL queries based on provided table schemas."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 150,
        "temperature": 0,
        "n": 1,
        "stop": ["#"]  # Use a stop token to prevent extra output
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

    if response.status_code == 200:
        response_json = response.json()
        sql_query = response_json['choices'][0]['message']['content'].strip()
        return sql_query
    else:
        print("Error:", response.status_code, response.text)
        return None


def get_table_schema():
    # Connect to the database and fetch table schema
    conn = sqlite3.connect('test-database.db')
    cursor = conn.cursor()

    # Get table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    schema = ""
    for table_name in tables:
        table_name = table_name[0]
        schema += f"Table {table_name}:\n"
        # Get columns for each table
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        for column in columns:
            column_name = column[1]
            data_type = column[2]
            schema += f"  - {column_name} ({data_type})\n"
        schema += "\n"

    conn.close()
    return schema

def validate_sql_query(sql_query):
    # Convert query to uppercase for consistent checking
    sql_upper = sql_query.upper()

    # Check for disallowed statements
    disallowed_statements = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'TRUNCATE']
    if any(stmt in sql_upper for stmt in disallowed_statements):
        return False

    # Ensure it starts with SELECT
    if not sql_upper.strip().startswith('SELECT'):
        return False

    # Additional checks can be added here

    return True

def generate_visualization_function(user_request):
    # Generate SQL query from user request
    table_schema = get_table_schema()
    sql_query = generate_sql_query(user_request, table_schema)
    if not sql_query:
        return "Failed to generate SQL query."

    # Validate and execute SQL query
    is_valid, error_message = validate_sql_query(sql_query)
    if not is_valid:
        return error_message

    # Execute SQL query
    df = execute_sql_query(sql_query)
    if df.empty:
        return "The query returned no data."

    # Generate visualization
    image_bytes = create_visualization(df, get_visualization_type(df.head()))
    if not image_bytes:
        return "Failed to create visualization."

    # Encode image to base64
    base64_image = base64.b64encode(image_bytes.getvalue()).decode('utf-8')

    # Store image in session or a database
    session['last_chart'] = base64_image

    return "Here is your visualization."

def modify_chart_function(attribute, value):
    # Modify the last chart based on the attribute and value
    base64_image = session.get('last_chart')
    if not base64_image:
        return "No chart available to modify."

    # Decode image and modify
    image_bytes = io.BytesIO(base64.b64decode(base64_image))
    # Depending on how your charts are generated, you might need to regenerate the chart with new parameters

    # For example, regenerate the chart with a new color
    # Note: You need to store the last DataFrame and visualization info
    df = session.get('last_df')
    viz_info = session.get('last_viz_info')

    if not df or not viz_info:
        return "Cannot modify the chart without the original data."

    # Modify the viz_info based on attribute and value
    viz_info[attribute] = value

    # Recreate visualization
    image_bytes = create_visualization(df, viz_info)
    if not image_bytes:
        return "Failed to modify the chart."

    # Encode image to base64 and update session
    base64_image = base64.b64encode(image_bytes.getvalue()).decode('utf-8')
    session['last_chart'] = base64_image

    return "The chart has been updated."

function_definitions = [
    {
        "name": "generate_visualization",
        "description": "Generates a visualization based on the user's request.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_request": {
                    "type": "string",
                    "description": "The user's request in natural language."
                }
            },
            "required": ["user_request"],
        },
    },
    {
        "name": "explain_insight",
        "description": "Provides a detailed explanation of the insights from the data.",
        "parameters": {
            "type": "object",
            "properties": {
                "insight": {
                    "type": "string",
                    "description": "The insight text to explain further."
                }
            },
            "required": ["insight"],
        },
    },
    {
        "name": "modify_chart",
        "description": "Modifies the chart based on user preferences.",
        "parameters": {
            "type": "object",
            "properties": {
                "attribute": {
                    "type": "string",
                    "description": "The chart attribute to modify (e.g., color, type)."
                },
                "value": {
                    "type": "string",
                    "description": "The new value for the attribute."
                }
            },
            "required": ["attribute", "value"],
        },
    },
]


@app.route('/visualize', methods=['POST'])
def visualize():
    user_request = request.json.get('user_request')
    if not user_request:
        return jsonify({'error': 'No user request provided'}), 400

    # Get table schema
    table_schema = get_table_schema()

    # Generate SQL query
    sql_query = generate_sql_query(user_request, table_schema)
    if not sql_query:
        return jsonify({'error': 'Failed to generate SQL query'}), 500

    # Validate SQL query
    if not validate_sql_query(sql_query):
        return jsonify({'error': 'Generated SQL query is not safe'}), 400
    # 1. connect db
    conn = sqlite3.connect('test-database.db')

    # 2. exec sql query
    try:
        df = pd.read_sql_query(sql_query, conn)
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()

    if df.empty:
        return jsonify({'error': 'The query returned no data'}), 400

    # 3. get vis type
    df_head = df.head(5)
    viz_info = get_visualization_type(df_head)
    if viz_info is None:
        return jsonify({'error': 'Could not determine visualization type'}), 400

    # 4. create visualization
    image_file_path = create_visualization(df, viz_info)
    if image_file_path is None:
        return jsonify({'error': 'Unsupported chart type or missing information'}), 400

    # Encode image to base64
    base64_image = base64.b64encode(image_file_path.getvalue()).decode('utf-8')
    
    # 5. get insight
    insights = get_chart_insights_with_image(image_file_path)
    if insights is None:
        return jsonify({'error': 'Could not get insights from image'}), 500


    response = {
        'image_file_path': image_file_path,
        'image_base64': base64_image,
        'insights': insights
    }
    return jsonify(response)

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message')
    if not user_input:
        return jsonify({'error': 'No message provided'}), 400

    # Retrieve conversation history from the session
    conversation_id = session.get('conversation_id')
    if not conversation_id:
        # Create a new conversation ID if it doesn't exist
        conversation_id = str(uuid.uuid4())
        session['conversation_id'] = conversation_id
        session['conversation_history'] = []

    conversation = session.get('conversation_history', [])

    # Add user input to conversation history
    conversation.append({"role": "user", "content": user_input})

    # Define your function definitions (as before)


    # Call OpenAI API with function definitions and conversation history
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0613",
        messages=conversation,
        functions=function_definitions,
        function_call="auto",
    )

    # Handle the assistant's response
    assistant_message = response['choices'][0]['message']

    if assistant_message.get("function_call"):
        # The assistant wants to call a function
        function_name = assistant_message["function_call"]["name"]
        arguments = json.loads(assistant_message["function_call"]["arguments"])

        # Call the corresponding function
        if function_name == "generate_visualization":
            function_response = generate_visualization_function(**arguments)
        elif function_name == "explain_insight":
            function_response = explain_insight_function(**arguments)
        elif function_name == "modify_chart":
            function_response = modify_chart_function(**arguments)
        else:
            function_response = "Function not recognized."

        # Add the assistant's function call to the conversation
        conversation.append(assistant_message)

        # Add the function's response to the conversation
        conversation.append({"role": "function", "name": function_name, "content": function_response})

        # Update the session with the new conversation history
        session['conversation_history'] = conversation

        # Call the assistant again with the updated conversation
        second_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0613",
            messages=conversation,
        )

        assistant_reply = second_response['choices'][0]['message']['content']
        conversation.append({"role": "assistant", "content": assistant_reply})
    else:
        # The assistant provided a direct reply
        assistant_reply = assistant_message['content']
        conversation.append({"role": "assistant", "content": assistant_reply})

    # Save the updated conversation to the session
    session['conversation_history'] = conversation

    return jsonify({'reply': assistant_reply})



if __name__ == '__main__':
    app.run(debug=True)



