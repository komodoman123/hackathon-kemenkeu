import pandas as pd
import numpy as np
import sqlite3
import json
import base64
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import create_engine, inspect
import api_keys
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib.projections")
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
    x_label: str, 
    y_label: str, 
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
        df.plot(kind='bar', x=x_column, y=y_column, xlabel=x_label, ylabel=y_label, title=chart_title, legend=False)
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
    
    insights = f"""
    Data Insights:
    - Total number of work units: {len(df)}
    - Highest budget: Rp {df[y_column].max()/1e9:.1f}B ({df.iloc[0][x_column]})
    - Lowest budget: Rp {df[y_column].min()/1e9:.1f}B ({df.iloc[-1][x_column]})
    - Average budget: Rp {df[y_column].mean()/1e9:.1f}B
    - Total budget: Rp {df[y_column].sum()/1e9:.1f}B
    """
    
    return f"Image saved at {image_path}. explain in a paragraph this: {insights}"


def line_chart_tool(
    sql_query: str,
    x_column: str,
    y_columns: list,
    x_label: str,
    y_labels: list,
    chart_title: str,
    image_filename: str,
    figsize: tuple = (12, 6)
) -> str:
    """
    Creates a dual-axis line chart from time series data queried from the database.
    
    Parameters:
    -----------
    sql_query : str
        SQL query to retrieve data
    x_column : str
        Column name for x-axis (time)
    y_columns : list
        List of column names for y-axis values
    x_label : str
        Label for x-axis
    y_labels : list
        Labels for y-axes
    chart_title : str
        Title for the chart
    image_filename : str
        Filename for saving the image
    figsize : tuple
        Figure size in inches (width, height)
    """
    import pandas as pd
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import os
    import sqlite3
    from datetime import datetime

    # Define the path for the database
    db_path = 'intermediary.db'

    # Connect to SQLite database and execute the SQL query
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query(sql_query, conn)
    except Exception as e:
        return f"Error executing SQL query: {e}"
    finally:
        conn.close()

    # Convert date string to datetime
    df[x_column] = pd.to_datetime(df[x_column])

    # Create the line chart with dual y-axes
    fig, ax1 = plt.subplots(figsize=figsize)
    
    try:
        # Plot first y-axis (Total Budget)
        color1 = '#2E86C1'
        ax1.set_xlabel(x_label)
        ax1.set_ylabel(y_labels[0])
        line1 = ax1.plot(df[x_column], df[y_columns[0]], color=color1, marker='o')
        ax1.tick_params(axis='y', labelcolor=color1)
        
        # Format y-axis as billions
        def format_billions(x, p):
            return f'Rp {x/1e9:.1f}B'
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(format_billions))
        
        # Create second y-axis for number of packages
        ax2 = ax1.twinx()
        color2 = '#E74C3C'
        ax2.set_ylabel(y_labels[1])
        line2 = ax2.plot(df[x_column], df[y_columns[1]], color=color2, marker='s')
        ax2.tick_params(axis='y', labelcolor=color2)
        
        # Add legend
        lines = line1 + line2
        labels = y_labels
        ax1.legend(lines, labels, loc='upper left')
        
        # Rotate x-axis labels
        plt.xticks(rotation=45, ha='right')
        
        # Add title with padding
        plt.title(chart_title, pad=20)
        
        # Adjust layout
        plt.tight_layout()
        
    except Exception as e:
        return f"Error creating line chart: {e}"

    # Save the chart to the current working directory
    image_path = os.path.join(os.getcwd(), f'images/{image_filename}')
    try:
        plt.savefig(image_path, format='png', bbox_inches='tight', dpi=300)
        plt.close()
    except Exception as e:
        return f"Error saving image: {e}"
    
    # Generate insights
    insights = f"""
    Data Insights:
    - Time period: {df[x_column].min().strftime('%Y-%m')} to {df[x_column].max().strftime('%Y-%m')}
    - Total budget over period: Rp {df[y_columns[0]].sum()/1e9:.1f}B
    - Total packages: {df[y_columns[1]].sum():,.0f}
    - Average monthly budget: Rp {df[y_columns[0]].mean()/1e9:.1f}B
    - Average monthly packages: {df[y_columns[1]].mean():.1f}
    - Peak budget month: {df.loc[df[y_columns[0]].idxmax(), x_column].strftime('%Y-%m')} (Rp {df[y_columns[0]].max()/1e9:.1f}B)
    - Peak packages month: {df.loc[df[y_columns[1]].idxmax(), x_column].strftime('%Y-%m')} ({df[y_columns[1]].max():,.0f} packages)
    """
    
    return f"Image saved at {image_path}, explain in a paragraph this {insights}"


def pie_chart_tool(
    sql_query: str,
    label_column: str,
    value_column: str,
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

    # Verify that the required columns exist
    if label_column not in df.columns:
        return f"Error: Column '{label_column}' not found in DataFrame."
    if value_column not in df.columns:
        return f"Error: Column '{value_column}' not found in DataFrame."

    # Create the pie chart
    plt.figure()
    try:
        df.set_index(label_column)[value_column].plot(kind='pie', autopct='%1.1f%%', title=chart_title)
        plt.ylabel('')  # Hide the y-label for a cleaner look
    except Exception as e:
        return f"Error creating pie chart: {e}"

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
    
    insights = f"""
    Data Insights:
    - Total units represented: {len(df)}
    - Highest contribution: {df.iloc[0][label_column]} with {df.iloc[0][value_column]} packages
    - Smallest contribution: {df.iloc[-1][label_column]} with {df.iloc[-1][value_column]} packages
    - Total packages: {df[value_column].sum()}
    """
    
    return f"Image saved at {image_path}. explain in a paragraph this: {insights}"


def histogram_tool(
    sql_query: str,
    x_column: str,
    x_label: str, 
    y_label: str, 
    chart_title: str,
    image_filename: str,
    image_directory: str = './images',
    bins: int = 12
) -> str:
    import os
    import sqlite3
    import pandas as pd
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np

    # Define the path for the intermediary database
    db_path = 'intermediary.db'

    # Step 1: Connect to SQLite database and execute the SQL query
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(sql_query, conn)
    conn.close()

    # Step 2: Verify that the x_column exists
    if x_column not in df.columns:
        return f"Error: Column '{x_column}' not found in DataFrame."

    # Step 3: Determine the data type of x_column and process accordingly
    if pd.api.types.is_numeric_dtype(df[x_column]):
        # Numeric data: use directly
        data_to_plot = df[x_column]

    elif pd.api.types.is_datetime64_any_dtype(df[x_column]) or pd.api.types.is_object_dtype(df[x_column]):
        # Datetime data: convert to datetime if not already
        df[x_column] = pd.to_datetime(df[x_column], errors='coerce')
        # Drop rows where conversion failed
        df = df.dropna(subset=[x_column])
        # Extract month numbers
        data_to_plot = df[x_column].dt.month
        bins = np.arange(1, 14) - 0.5  # Edges between months

    else:
        # Categorical data: use as is
        data_to_plot = df[x_column]

    # Step 4: Create the histogram
    try:
        if pd.api.types.is_numeric_dtype(df[x_column]) or pd.api.types.is_datetime64_any_dtype(df[x_column]):
            # Use histogram for numeric/datetime data
            plt.figure()
            plt.hist(data_to_plot, bins=bins, edgecolor='black')
            plt.title(chart_title)
            plt.xlabel(x_label)
            plt.ylabel(y_label)
            if pd.api.types.is_datetime64_any_dtype(df[x_column]) or 'Month' in df.columns:
                # Set x-ticks to month names
                plt.xticks(range(1,13), ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                                         'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
        else:
            # Use bar plot for categorical data
            counts = data_to_plot.value_counts().sort_index()
            counts.plot(kind='bar', title=chart_title, width=1.0)
            plt.xlabel(x_label)
            plt.ylabel(y_label)
            plt.xticks(rotation=45)
    except Exception as e:
        return f"Error creating histogram: {e}"

    # Step 5: Ensure the image directory exists
    try:
        os.makedirs(image_directory, exist_ok=True)
    except OSError as e:
        return f"Error creating directory '{image_directory}': {e}"

    # Step 6: Save the chart
    image_path = os.path.join(image_directory, image_filename)
    try:
        plt.savefig(image_path, format='png', bbox_inches='tight')
        plt.close()
    except Exception as e:
        return f"Error saving image: {e}"
        
    # Data insights
    insights = f"Data Insights:\n- Total records: {len(df)}"
    if pd.api.types.is_datetime64_any_dtype(df[x_column]):
        month_counts = data_to_plot.value_counts().sort_index()
        most_common_month = month_counts.idxmax()
        least_common_month = month_counts.idxmin()
        insights += f"\n- Peak month: {most_common_month}\n- Month with fewest records: {least_common_month}"
    elif pd.api.types.is_numeric_dtype(df[x_column]):
        insights += f"\n- Mean of '{x_column}': {data_to_plot.mean()}\n- Max of '{x_column}': {data_to_plot.max()}\n- Min of '{x_column}': {data_to_plot.min()}"
    else:
        counts = data_to_plot.value_counts()
        most_frequent_category = counts.idxmax()
        insights += f"\n- Most frequent category: {most_frequent_category}"

    # Completion message
    return f"Histogram successfully created and saved at {image_path}. {insights}"
