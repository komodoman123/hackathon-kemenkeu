from flask import Flask, request, jsonify
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
import re
import json

app = Flask(__name__, static_url_path='/images', static_folder='images')

# OPENAI API KEY is ommited

def get_visualization_type(df_head,query):
    prompt = f"""
Given the following data sample:
{df_head.to_csv(index=False)}
and the query that get that data:
{query}
Suggest the most appropriate visualization type (e.g., bar chart, line chart, scatter plot) and the columns to use for x and y axes.
Provide the answer in JSON format, enclosed in triple backticks like ```{{ ... }}```.
Provide the answer in JSON format like:
{{
    "chart_type": "scatter",
    "x_axis": "column_name",
    "y_axis": "column_name",
    "title": "Your suggested title"
}}
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
    print("viz_info",viz_info)
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

def get_chart_insights_with_image(image_path, viz_info):

    base64_image = encode_image(image_path )
    
    chart_type = viz_info.get('chart_type')
    x_axis = viz_info.get('x_axis')
    y_axis = viz_info.get('y_axis')
    title = viz_info.get('title', 'Data Visualization')
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
                        "text": "I have a {chart_type} titled '{title}' plotting '{x_axis}' against '{y_axis}'.Please provide insights based on this information."
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
        "model": "gpt-4o-mini",
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
    print("schema",schema)
    conn.close()
    return schema

def validate_sql_query(sql_query):
    # Convert query to uppercase for consistent checking
    sql_upper = sql_query.upper()
    print("sql_upper",sql_upper)
    # Check for disallowed statements
    disallowed_statements = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'TRUNCATE']
    if any(stmt in sql_upper for stmt in disallowed_statements):
        return False

    # Ensure it starts with SELECT
    if not sql_upper.strip().startswith('SELECT'):
        return False

    # Additional checks can be added here

    return True


@app.route('/visualize', methods=['POST'])
def visualize():
    user_request = request.json.get('user_request')
    if not user_request:
        return jsonify({'error': 'No user request provided'}), 400

    # Get table schema
    table_schema = get_table_schema()

    # Generate SQL query
    sql_query = generate_sql_query(user_request, table_schema)
    sql_query = re.sub(r'```(sql)?\n?', '', sql_query).strip()
    print("query",sql_query)
    if not sql_query:
        return jsonify({'error': 'Failed to generate SQL query'}), 500

    # Validate SQL query
    # if not validate_sql_query(sql_query):
    #     return jsonify({'error': 'Generated SQL query is not safe'}), 400
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
    viz_info = get_visualization_type(df_head,sql_query)
    if viz_info is None:
        return jsonify({'error': 'Could not determine visualization type'}), 400

    # 4. create visualization
    image_file_path = create_visualization(df, viz_info)
    if image_file_path is None:
        return jsonify({'error': 'Unsupported chart type or missing information'}), 400

    # Encode image to base64
    #base64_image = base64.b64encode(image_file_path.getvalue()).decode('utf-8')
    
    # 5. get insight
    insights = get_chart_insights_with_image(image_file_path, viz_info)
    if insights is None:
        return jsonify({'error': 'Could not get insights from image'}), 500


    response = {
        'image_file_path': image_file_path,
        #'image_base64': base64_image,
        'insights': insights
    }
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
