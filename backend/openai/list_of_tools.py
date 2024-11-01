import pandas as pd
import numpy as np
import sqlite3
import json
import base64
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import create_engine, inspect
import api_keys

client = OpenAI(api_key=api_keys.openai_key)

def get_embedding(text):
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-large" 
    )
    return response.data[0].embedding

def mini_retrieve_similar_keywords(query: str, top_k: int = 10) -> str:
    # Load DataFrame from CSV
    df = pd.read_csv('v2_key.csv')

    # Convert 'embedding' column to numeric vectors
    df['embedding'] = df['embedding'].apply(lambda x: np.fromstring(x.strip('[]'), sep=','))

    # Get embedding for the query
    query_embedding = get_embedding(query)

    # Calculate cosine similarity
    similarities = df['embedding'].apply(lambda x: cosine_similarity([query_embedding], [x])[0][0])

    # Add similarity scores to the DataFrame
    df['similarity'] = similarities

    # Sort and retrieve top_k results
    results = df.sort_values(by='similarity', ascending=False).head(top_k)

    # Return the DataFrame with keyword and similarity
    return results[['keyword', 'similarity']].to_json(orient='records')

def intermediary_dataframe_retrieval(query: str) -> str:

    # Define your database path
    db_path = 'data_pengadaan_copy.db'  # Update with your actual database path
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(query, conn)

    df.to_sql('intermediary_table', sqlite3.connect('intermediary.db'), if_exists='replace', index=False)

    # Get the first 5 rows from the intermediary_table
    first_rows = df.head(5).to_dict(orient='records')

    # Prepare the output
    output = {
        "schema": { "columns": list(df.columns) },
        "first_rows": first_rows
    }

    # Return the JSON formatted result
    return json.dumps(output, indent=4)


def schema_check() -> str:
    # Create database engine
    conn = sqlite3.connect("data_pengadaan_copy.db")
    cursor = conn.cursor()

    # Initialize schema dictionary
    schema_info = {}

    # Get table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    for table in tables:
        table_name = table[0]
        # Initialize table info in schema dictionary
        schema_info[table_name] = []
        
        # Get column information
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        
        # Add column information to schema
        for column in columns:
            column_info = {
                "name": column[1],
                "type": column[2],
                "nullable": not column[3],  # column[3] is "notnull"
                "primary_key": bool(column[5])  # column[5] is "pk"
            }
            schema_info[table_name].append(column_info)

    # Close connection
    conn.close()

    # Return the schema information as formatted JSON
    return json.dumps({"schema": schema_info}, indent=4)

def bar_chart_tool(
    sql_query: str,
    x_column: str,
    y_column: str,
    chart_title: str,
    image_filename: str,
    image_directory: str = './images'
) -> str:
    import pandas as pd
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import os
    import sqlite3

    # Define the path for the intermediary database
    db_path = 'intermediary.db'

    # Connect to SQLite database and execute the SQL query
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query(sql_query, conn)
    except Exception as e:
        return f"Error executing SQL query: {e}"
    finally:
        conn.close()

    # Verify that columns exist
    if x_column not in df.columns:
        return f"Error: Column '{x_column}' not found in DataFrame."
    if y_column not in df.columns:
        return f"Error: Column '{y_column}' not found in DataFrame."
    

    # Create the bar chart
    plt.figure()
    try:
        df.plot(kind='bar', x=x_column, y=y_column, title=chart_title, legend=False)
        plt.xticks(rotation=45)
    except Exception as e:
        return f"Error creating bar chart: {e}"

    # Ensure the image directory exists
    try:
        os.makedirs(image_directory, exist_ok=True)
    except OSError as e:
        return f"Error creating directory '{image_directory}': {e}"

    # Save the chart
    image_path = os.path.join(image_directory, image_filename)
    try:
        plt.savefig(image_path, format='png', bbox_inches='tight')
        plt.close()
    except Exception as e:
        return f"Error saving image: {e}"

    return f"Image saved at {image_path}. Give Insights to the user based on this data: {df}"

