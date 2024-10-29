from flask import Flask, request, jsonify
import sqlite3
import pandas as pd
import openai
import json
import io
import matplotlib.pyplot as plt
import seaborn as sns
import base64
import os
import datetime

app = Flask(__name__)


#openai.api_key = os.environ.get('OPENAI_API_KEY')
openai.api_key="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"
def get_visualization_type(df_head):
    prompt = f"""
Given the following data sample:
{df_head.to_csv(index=False)}

Suggest the most appropriate visualization type (e.g., bar chart, line chart, scatter plot) and the columns to use for x and y axes.
Provide the answer in JSON format like:
{{
    "chart_type": "scatter",
    "x_axis": "column_name",
    "y_axis": "column_name",
    "title": "Your suggested title"
}}
"""
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a data visualization assistant."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=150,
        temperature=0,
        n=1,
    )

    try:
        content = response.choices[0].message.content.strip()
        viz_info = json.loads(content)
    except json.JSONDecodeError:
        viz_info = None
    return viz_info


def create_visualization(df, viz_info):

    plt.figure(figsize=(10, 6))
    
    # Extract chart details from the response
    chart_type = viz_info.get('chart_type')
    x_axis = viz_info.get('x_axis')
    y_axis = viz_info.get('y_axis')
    title = viz_info.get('title', 'Data Visualization')
    
    # Ensure data is exist
    if not all([chart_type, x_axis, y_axis]):
        return None  # ada data hilang
    
    
    if chart_type == 'bar' or chart_type == 'bar chart':
        sns.barplot(data=df, x=x_axis, y=y_axis)
    elif chart_type == 'line' or chart_type == 'line chart':
        sns.lineplot(data=df, x=x_axis, y=y_axis)
    elif chart_type == 'scatter' or chart_type == 'scatter plot':
        sns.scatterplot(data=df, x=x_axis, y=y_axis)
    else:
        return None  # chart ga ada yang cocok
    

    plt.title(title)
    plt.tight_layout()

    #save
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    file_name = f"visualization_{timestamp}.png"
    file_path = os.path.join('images', file_name)  

    if not os.path.exists('images'):
        os.makedirs('images')  

    plt.savefig(file_path)  
    plt.close()  

    
    return file_path

def get_chart_insights_from_summary(summary_stats, viz_info):
    prompt = f"""
Given the following data summary and visualization details, provide insights.

Visualization Type: {viz_info['chart_type']}
X-Axis: {viz_info['x_axis']}
Y-Axis: {viz_info['y_axis']}
Title: {viz_info.get('title', 'Data Visualization')}

Data Summary:
{summary_stats}

Describe the key findings and any notable patterns or trends in a concise manner.
"""
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a data analyst."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=200,
        temperature=0,
        n=1,
    )
    insights = response.choices[0].message.content.strip()
    return insights


@app.route('/visualize', methods=['POST'])
def visualize():
    sql_query = request.json.get('sql_query')
    if not sql_query:
        return jsonify({'error': 'No SQL query provided'}), 400

    # 1. connect db
    conn = sqlite3.connect('test-database.db')

    # Execute query
    try:
        df = pd.read_sql_query(sql_query, conn)
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()

    if df.empty:
        return jsonify({'error': 'The query returned no data'}), 400

    # determine tipe visualisasi
    df_head = df.head(5)
    viz_info = get_visualization_type(df_head)
    if viz_info is None:
        return jsonify({'error': 'Could not determine visualization type'}), 400

    # create and save
    image_file_path = create_visualization(df, viz_info)
    if image_file_path is None:
        return jsonify({'error': 'Unsupported chart type or missing information'}), 400

    # get summary
    summary_stats = df.describe(include='all').to_string()

    # get insight
    insights = get_chart_insights_from_summary(summary_stats, viz_info)


    response = {
        'image_file_path': image_file_path, 
        'insights': insights
    }
    return jsonify(response)



if __name__ == '__main__':
    app.run(debug=True)
