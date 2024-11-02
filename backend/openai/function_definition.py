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
            To use this tool, you need to use keywords from 'mini_retrieve_similar_keywords'.
            Retrieve data from the database using a SQL query based on grouped keywords with `AND` between groups and `OR` within each group.
            - **Example 1:** For "informasi terkait perbaikan gedung," use:
              ```sql
              SELECT * FROM data_pengadaan WHERE (filtered_keywords LIKE '%perbaikan%' OR filtered_keywords LIKE '%rehabilitasi%' OR filtered_keywords LIKE '%pemeliharaan%') 
              AND (filtered_keywords LIKE '%gedung%' OR filtered_keywords LIKE '%bangunan%' OR filtered_keywords LIKE '%kantor%');
              ```
            - **Example 2:** For "informasi terkait alat tulis," use:
              ```sql
              SELECT * FROM data_pengadaan WHERE (filtered_keywords LIKE '%alat%' OR filtered_keywords LIKE '%peralatan%') 
              AND (filtered_keywords LIKE '%tulis%' OR filtered_keywords LIKE '%penulisan%');
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
            if the user doesn't specify the request, x-axis is satuan_kerja and y-axis is total_pagu. 
            
            - **Inputs**: SQL query, x-axis column, y-axis column, chart title, x label, y label, image filename, and optional image directory.
            - **Output**: Path to the saved image.

            **Example Usage:**
            ```python
            sql_query = "SELECT category, COUNT(*) as count FROM intermediary_table GROUP BY category"
            x_column = "category"
            y_column = "count"
            x_label = "Category"
            y_label = "Total Count"
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
                'x_label': {
                    'type': 'string',
                    'description': 'Label name for the x-axis.'
                },
                'y_label': {
                    'type': 'string',
                    'description': 'Label name for the y-axis.'
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
            'required': ['sql_query', 'x_column', 'y_column', 'x_label', 'y_label', 'chart_title', 'image_filename'],
            'additionalProperties': False
        }
    }
}

line_chart_tool_definition = {
    'type': 'function',
    'function': {
        'name': 'line_chart_tool',
        'description': """
            Creates a dual-axis line chart from intermediary_table showing trends over time with dual y-axes for budget and package counts, automatic date formatting, and data insights.
            Example:
            sql_query: str = 
                SELECT strftime('%Y-%m', tanggal_umumkan_paket) as bulan,
                COUNT(kode_rup) as jumlah_paket,
                SUM(total_pagu) as total_pagu 
            FROM intermediary_table 
            GROUP BY bulan 
            ORDER BY bulan,
            x_column: str = "bulan",
            y_columns: list = ["total_pagu", "jumlah_paket"],
            x_label: str = "Month",
            y_labels: list = ["Total Budget (Rp Billion)", "Number of Packages"],
            chart_title: str = "Procurement Trends Over Time",
            image_filename: str = "procurement_trends.png",
            image_directory: str = './images',
            figsize: tuple = (12, 6)
        """,
        'parameters': {
            'type': 'object',
            'properties': {
                'sql_query': {
                    'type': 'string',
                    'description': 'SQL query to retrieve time series data. Defaults to monthly procurement trends.'
                },
                'x_column': {
                    'type': 'string',
                    'description': 'Column name for x-axis (time). Default: "bulan"'
                },
                'y_columns': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'description': 'List of column names for y-axes. Default: ["total_pagu", "jumlah_paket"]'
                },
                'x_label': {
                    'type': 'string',
                    'description': 'Label for x-axis. Default: "Month"'
                },
                'y_labels': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'description': 'Labels for y-axes. Default: ["Total Budget (Rp Billion)", "Number of Packages"]'
                },
                'chart_title': {
                    'type': 'string',
                    'description': 'Title for the chart. Default: "Procurement Trends Over Time"'
                },
                'image_filename': {
                    'type': 'string',
                    'description': 'Filename for saving the image. Default: "procurement_trends.png"'
                },
                'image_directory': {
                    'type': 'string',
                    'description': 'Directory to save the image. Default: "./images"'
                },
                'figsize': {
                    'type': 'array',
                    'items': {'type': 'number'},
                    'description': 'Figure size in inches (width, height). Default: (12, 6)'
                }
            },
            'required': ['sql_query', 'x_column', 'y_columns','x_label', 'y_labels', 'chart_title', 'image_filename', 'image_directory', 'figsize'],  # All parameters have defaults
            'additionalProperties': False
        }
    }
}


pie_chart_tool_definition = {
    'type': 'function',
    'function': {
        'name': 'pie_chart_tool',
        'description': (
            """
            Creates a pie chart. If the user doesn't specify, shows the distribution of procurement packages based on the work unit category.
            Uses data queried from 'intermediary_table' in 'intermediary.db'.
            
            - **Inputs**: SQL query, label column (work unit), value column (package count), chart title, image filename, optional image directory.
            - **Output**: Path to the saved image.

            **Example Usage:**
            ```python
            sql_query = "SELECT satuan_kerja, COUNT(kode_rup) as jumlah_paket FROM intermediary_table GROUP BY satuan_kerja"
            label_column = "satuan_kerja"
            value_column = "jumlah_paket"
            chart_title = "Distribution of Procurement Packages by Work Unit"
            image_filename = "work_unit_distribution_pie_chart.png"
            image_directory = "./images"
            ```
            """
        ),
        'parameters': {
            'type': 'object',
            'properties': {
                'sql_query': {
                    'type': 'string',
                    'description': 'SQL query to retrieve data for the pie chart.'
                },
                'label_column': {
                    'type': 'string',
                    'description': 'Column name for the labels in the pie chart (e.g., work unit categories).'
                },
                'value_column': {
                    'type': 'string',
                    'description': 'Column name for the values in the pie chart (e.g., package count).'
                },
                'chart_title': {
                    'type': 'string',
                    'description': 'Title for the chart.'
                },
                'image_filename': {
                    'type': 'string',
                    'description': 'Filename for saving the image (e.g., "pie_chart.png").'
                },
                'image_directory': {
                    'type': 'string',
                    'description': 'Optional directory to save the image.',
                    'default': './images'
                }
            },
            'required': ['sql_query', 'label_column', 'value_column', 'chart_title', 'image_filename'],
            'additionalProperties': False
        }
    }
}


histogram_tool_definition = {
    'type': 'function',
    'function': {
        'name': 'histogram_tool',
        'description': (
            """
            Creates a histogram. If the user, doesn't specify, shows the distribution of procurement announcement dates over the months.
            Uses data queried from 'intermediary_table' in 'intermediary.db'.
            
            - **Inputs**: SQL query, x-axis column, chart title, x label, y label, image filename, optional image directory, and number of bins.
            - **Output**: Path to the saved image.

            **Example Usage:**
            ```python
            sql_query = "SELECT tanggal_umumkan_paket FROM intermediary_table"
            x_column = "tanggal_umumkan_paket"
            x_label = "Month of Announcement"
            y_label = "Frequency"
            chart_title = "Monthly Procurement Announcements"
            image_filename = "announcement_histogram.png"
            image_directory = "./images"
            bins = 12
            ```
            """
        ),
        'parameters': {
            'type': 'object',
            'properties': {
                'sql_query': {
                    'type': 'string',
                    'description': 'SQL query to retrieve announcement dates for the histogram.'
                },
                'x_column': {
                    'type': 'string',
                    'description': 'Column name for the x-axis.'
                },
                'x_label': {
                    'type': 'string',
                    'description': 'Label name for the x-axis.'
                },
                'y_label': {
                    'type': 'string',
                    'description': 'Label name for the y-axis.'
                },
                'chart_title': {
                    'type': 'string',
                    'description': 'Title for the chart.'
                },
                'image_filename': {
                    'type': 'string',
                    'description': 'Filename for saving the image (e.g., "histogram.png").'
                },
                'image_directory': {
                    'type': 'string',
                    'description': 'Optional directory to save the image.',
                    'default': './images'
                },
                'bins': {
                    'type': 'integer',
                    'description': 'Number of bins for the histogram (e.g., 12 for monthly distribution).',
                    'default': 12
                }
            },
            'required': ['sql_query', 'x_column', 'x_label', 'y_label', 'chart_title', 'image_filename', 'image_directory', 'bins'],
            'additionalProperties': False
        }
    }
}