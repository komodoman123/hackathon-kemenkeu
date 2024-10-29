from flask import Flask, request, jsonify, session, send_from_directory
import uuid
import openai
import pandas as pd
import base64
import io
import os
import json
import matplotlib.pyplot as plt
import seaborn as sns
import sqlite3

app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = 'your-secret-key'  # Replace with a secure, random key

# Set the path for static files (charts)
STATIC_FOLDER = 'static'
if not os.path.exists(STATIC_FOLDER):
    os.makedirs(STATIC_FOLDER)

# Set your OpenAI API key
openai.api_key = os.environ.get('OPENAI_API_KEY')  # Ensure this environment variable is set

# Function definitions for OpenAI function calling
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
                    "description": "The chart attribute to modify (e.g., color, chart_type)."
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

# Helper function to truncate conversation history to avoid exceeding cookie size limits
def truncate_conversation(conversation):
    MAX_CONVERSATION_LENGTH = 10  # Adjust as needed
    if len(conversation) > MAX_CONVERSATION_LENGTH:
        conversation = conversation[-MAX_CONVERSATION_LENGTH:]
    return conversation

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message')
    if not user_input:
        return jsonify({'error': 'No message provided'}), 400

    # Retrieve or initialize conversation history
    conversation = session.get('conversation', [])
    conversation.append({"role": "user", "content": user_input})

    # Truncate conversation to keep session data small
    conversation = truncate_conversation(conversation)

    # Call OpenAI API with function definitions
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0613",
            messages=conversation,
            functions=function_definitions,
            function_call="auto",
        )
    except Exception as e:
        return jsonify({'error': f'OpenAI API error: {str(e)}'}), 500

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

        # Add the assistant's function call and the function's response to the conversation
        conversation.append(assistant_message)
        conversation.append({"role": "function", "name": function_name, "content": function_response})

        # Truncate conversation
        conversation = truncate_conversation(conversation)

        # Save updated conversation
        session['conversation'] = conversation

        # Call the assistant again with the function's response
        try:
            second_response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-0613",
                messages=conversation,
            )
        except Exception as e:
            return jsonify({'error': f'OpenAI API error: {str(e)}'}), 500

        assistant_reply = second_response['choices'][0]['message']['content']
        conversation.append({"role": "assistant", "content": assistant_reply})
    else:
        # The assistant provided a direct reply
        assistant_reply = assistant_message['content']
        conversation.append({"role": "assistant", "content": assistant_reply})

    # Truncate conversation
    conversation = truncate_conversation(conversation)

    # Save updated conversation
    session['conversation'] = conversation

    return jsonify({'reply': assistant_reply})

# Function to get hardcoded table schema with descriptions
def get_table_schema():
    schema = """
Table sales_data:
  - product_id (INTEGER): Unique identifier for each product.
  - category (TEXT): Category of the product.
  - sales (FLOAT): Sales amount in USD.
  - sale_date (DATE): Date of the sale (YYYY-MM-DD).

Table customers:
  - customer_id (INTEGER): Unique identifier for each customer.
  - name (TEXT): Full name of the customer.
  - join_date (DATE): Date when the customer joined (YYYY-MM-DD).
"""
    return schema

# Function to generate SQL query from user request
def generate_sql_query(user_request, table_schema):
    prompt = f"""
You are an assistant that converts natural language requests into SQL queries.

**Instructions:**

- Only generate **safe**, **read-only** `SELECT` SQL queries.
- Do **not** include any other SQL statements besides `SELECT`.
- Do **not** use `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, `CREATE`, or any other data modification or schema-changing commands.
- The SQL query should only reference the tables and columns provided in the table schema.
- Use the column descriptions to accurately map the user's request to the correct columns.
- If the user's request cannot be answered with a `SELECT` query using the given schema, respond with an error message like "I'm sorry, but I cannot generate a query for that request."

**Table Schema:**

{table_schema}

**User Request:**

"{user_request}"

Provide only the SQL query (without any explanations or additional text) or the error message if applicable.
"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that converts natural language into SQL queries based on provided table schemas."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0,
            n=1,
            stop=None
        )
        sql_query = response['choices'][0]['message']['content'].strip()
        return sql_query
    except Exception as e:
        print(f"OpenAI API error: {str(e)}")
        return None

# Function to validate the generated SQL query
def validate_sql_query(sql_query):
    sql_upper = sql_query.upper()

    # Check if the assistant returned an error message
    if "I'M SORRY" in sql_upper or "CANNOT GENERATE" in sql_upper:
        return False, "The assistant could not generate a valid SQL query for this request."

    # Ensure the query starts with SELECT
    if not sql_upper.strip().startswith('SELECT'):
        return False, "The SQL query does not start with a SELECT statement."

    # Disallowed keywords
    disallowed_keywords = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'TRUNCATE', 'CREATE', 'EXEC', 'EXECUTE', '--', ';']
    if any(keyword in sql_upper for keyword in disallowed_keywords):
        return False, "The SQL query contains disallowed keywords."

    # Prevent multiple statements
    if ';' in sql_query.strip(';'):
        return False, "Multiple SQL statements detected."

    return True, None

# Function to execute the SQL query and return a DataFrame
def execute_sql_query(sql_query):
    try:
        conn = sqlite3.connect('test-database.db')  # Update with your database path
        df = pd.read_sql_query(sql_query, conn)
        conn.close()
        return df
    except Exception as e:
        print(f"SQL execution error: {str(e)}")
        return None

# Function to get visualization type from DataFrame head
def get_visualization_type(df_head):
    prompt = f"""
Given the following data sample:
{df_head.to_csv(index=False)}

Suggest the most appropriate visualization type (e.g., bar chart, line chart, scatter plot) and the columns to use for x and y axes.
Provide the answer in JSON format, enclosed in triple backticks like ```{{ ... }}```.
"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a data visualization assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0,
            n=1,
        )
        content = response['choices'][0]['message']['content'].strip()
        # Extract JSON between triple backticks
        import re
        match = re.search(r'```(.*?)```', content, re.DOTALL)
        if match:
            json_str = match.group(1)
            viz_info = json.loads(json_str)
        else:
            viz_info = None
        return viz_info
    except Exception as e:
        print(f"OpenAI API error: {str(e)}")
        return None

# Function to create visualization from DataFrame and visualization info
def create_visualization(df, viz_info):
    plt.figure(figsize=(10, 6))

    chart_type = viz_info.get('chart_type')
    x_axis = viz_info.get('x_axis')
    y_axis = viz_info.get('y_axis')
    title = viz_info.get('title', 'Data Visualization')

    if not all([chart_type, x_axis, y_axis]):
        return None  # Missing required information

    # Check if columns exist
    if x_axis not in df.columns or y_axis not in df.columns:
        return None  # Columns do not exist

    # Create the chart
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

    # Save the image to a BytesIO object
    img_io = io.BytesIO()
    plt.savefig(img_io, format='png')
    img_io.seek(0)
    plt.close()

    return img_io

# Function to generate visualization
def generate_visualization_function(user_request):
    # Get table schema
    table_schema = get_table_schema()

    # Generate SQL query
    sql_query = generate_sql_query(user_request, table_schema)
    if not sql_query:
        return "Failed to generate SQL query."

    # Validate SQL query
    is_valid, error_message = validate_sql_query(sql_query)
    if not is_valid:
        return error_message

    # Execute SQL query
    df = execute_sql_query(sql_query)
    if df is None or df.empty:
        return "The query returned no data."

    # Get visualization type
    viz_info = get_visualization_type(df.head())
    if viz_info is None:
        return "Could not determine visualization type."

    # Create visualization
    image_bytes = create_visualization(df, viz_info)
    if image_bytes is None:
        return "Failed to create visualization."

    # Save image to server
    image_id = str(uuid.uuid4())
    image_filename = f"chart_{image_id}.png"
    image_path = os.path.join(app.static_folder, image_filename)
    with open(image_path, 'wb') as f:
        f.write(image_bytes.getvalue())

    # Store the image filename and data in the session
    session['last_chart'] = image_filename
    session['last_df'] = df.to_json()  # Convert DataFrame to JSON
    session['last_viz_info'] = viz_info

    # Return a message with the image URL
    image_url = f"/static/{image_filename}"
    return f"Here is your visualization: {image_url}"

# Function to explain insight
def explain_insight_function(insight):
    prompt = f"Please provide a detailed explanation of the following insight:\n\n{insight}"
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=150,
            temperature=0.7,
        )
        explanation = response.choices[0].text.strip()
        return explanation
    except Exception as e:
        print(f"OpenAI API error: {str(e)}")
        return "Failed to generate explanation."


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
# Function to modify the chart
def modify_chart_function(attribute, value):
    image_filename = session.get('last_chart')
    df_json = session.get('last_df')
    viz_info = session.get('last_viz_info')

    if not image_filename or not df_json or not viz_info:
        return "Cannot modify the chart without the original data."

    # Load DataFrame
    df = pd.read_json(df_json)

    # Modify viz_info based on attribute and value
    if attribute in viz_info:
        viz_info[attribute] = value
    else:
        # Handle attributes like 'color' which might not be in viz_info
        viz_info[attribute] = value

    # Recreate visualization
    image_bytes = create_visualization(df, viz_info)
    if image_bytes is None:
        return "Failed to modify the chart."

    # Save updated image with the same filename
    image_path = os.path.join(app.static_folder, image_filename)
    with open(image_path, 'wb') as f:
        f.write(image_bytes.getvalue())

    # Update session data
    session['last_viz_info'] = viz_info

    # Return a message with the image URL
    image_url = f"/static/{image_filename}"
    return f"The chart has been updated: {image_url}"

# Route to serve images securely (if needed)
@app.route('/get_image/<filename>')
def get_image(filename):
    # Validate the session or permissions
    if filename != session.get('last_chart'):
        return "Unauthorized", 403
    return send_from_directory(app.static_folder, filename)

# Cleanup temporary files on server shutdown (optional)
import atexit
import glob

def cleanup_temp_files():
    files = glob.glob(os.path.join(app.static_folder, 'chart_*.png'))
    for f in files:
        try:
            os.remove(f)
        except Exception as e:
            print(f"Error deleting file {f}: {str(e)}")

atexit.register(cleanup_temp_files)

if __name__ == '__main__':
    app.run(debug=True)
