mini_retrieve_similar_keywords_definition = {
    'type': 'function',
    'function': {
        'name': 'mini_retrieve_similar_keywords',
        'description': (
            "Use this tool to find available keywords on the database"
            "The tool performs a search to retrieve the most similar keywords. "
            "Input: Query and top_k. Output: A DataFrame with the most similar keywords and their similarity scores."
        ),
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': 'The search query keyword to find similar ones.'
                },
                'top_k': {
                    'type': 'integer',
                    'description': 'Number of top similar results to return. Default is 10.',
                    'default': 10
                }
            },
            'required': ['query'],
            'additionalProperties': False
        }
    }
}

intermediary_dataframe_retrieval_definition = {
    'type': 'function',
    'function': {
        'name': 'intermediary_dataframe_retrieval',
        'description': (
            """
            Retrieve data from the database using a SQL query based on grouped keywords with `AND` between groups and `OR` within each group.
            - **Example 1:** For "informasi terkait perbaikan gedung," use:
              ```sql
              SELECT * FROM data_pengadaan WHERE (filtered_keywords LIKE '%perbaikan%' OR filtered_keywords LIKE '%rehabilitasi%' OR filtered_keywords LIKE '%pemeliharaan%') 
              AND (filtered_keywords LIKE '%gedung%' OR filtered_keywords LIKE '%bangunan%' OR filtered_keywords LIKE '%kantor%');
              ```
            - **Example 2:** For "informasi terkait alat tulis," use:
              ```sql
              SELECT * FROM data_pengadaan WHERE (filtered_keywords LIKE '%alat%' OR filtered_keywords LIKE '%peralatan%') 
              AND (filtered_keywords LIKE '%tulis%' OR filtered_keywords LIKE '%pensil%' OR filtered_keywords LIKE '%pulpen%');
              ```
            """
        ),
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': 'SQL query to retrieve data.'
                }
            },
            'required': ['query'],
            'additionalProperties': False
        }
    }
}

schema_check_definition = {
    'type': 'function',
    'function': {
        'name': 'schema_check',
        'description': (
            "Retrieves the schema information for each table in the `data_pengadaan_copy.db` database. "
            "No input is required. "
            "Output: Schema with table names and column details for each table."
        ),
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': [],
            'additionalProperties': False
        }
    }
}

bar_chart_tool_definition = {
    'type': 'function',
    'function': {
        'name': 'bar_chart_tool',
        'description': (
            """
            Creates a bar chart from data queried from the 'intermediary_table' in the 'intermediary.db'.
            
            - **Inputs**: SQL query, x-axis column, y-axis column, chart title, image filename, and optional image directory.
            - **Output**: Path to the saved image.

            **Example Usage:**
            ```python
            sql_query = "SELECT category, COUNT(*) as count FROM intermediary_table GROUP BY category"
            x_column = "category"
            y_column = "count"
            chart_title = "Category Count"
            image_filename = "category_count_chart.png"
            image_directory = "./images"
            ```
            """
        ),
        'parameters': {
            'type': 'object',
            'properties': {
                'sql_query': {
                    'type': 'string',
                    'description': 'SQL query to retrieve data for the bar chart from the intermediary_table.'
                },
                'x_column': {
                    'type': 'string',
                    'description': 'Column name for the x-axis.'
                },
                'y_column': {
                    'type': 'string',
                    'description': 'Column name for the y-axis.'
                },
                'chart_title': {
                    'type': 'string',
                    'description': 'Title for the chart.'
                },
                'image_filename': {
                    'type': 'string',
                    'description': 'Filename for saving the image (e.g., "bar_chart.png").'
                },
                'image_directory': {
                    'type': 'string',
                    'description': 'Optional directory to save the image.',
                    'default': './images'
                }
            },
            'required': ['sql_query', 'x_column', 'y_column', 'chart_title', 'image_filename'],
            'additionalProperties': False
        }
    }
}