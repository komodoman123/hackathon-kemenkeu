mini_retrieve_similar_keywords_definition = {
    'type': 'function',
    'function': {
        'name': 'mini_retrieve_similar_keywords',
        'description': (
            "Use this tool to find available keywords similar to the query based on cosine similarity. "
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