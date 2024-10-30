import pandas as pd
import numpy as np
import sqlite3
import json
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