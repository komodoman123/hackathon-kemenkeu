import pandas as pd
import numpy as np
import sqlite3

# Define ministries and departments
ministries = {
    'Health': ['Public Health', 'Hospitals', 'Pharmaceuticals'],
    'Education': ['Primary Education', 'Secondary Education', 'Higher Education'],
    'Transportation': ['Roads', 'Railways', 'Air Transport'],
    'Finance': ['Taxation', 'Budgeting', 'Auditing'],
    'Agriculture': ['Crop Production', 'Livestock', 'Research'],
}

# Budget categories and subcategories
categories = {
    'Personnel': ['Salaries', 'Benefits'],
    'Operations': ['Utilities', 'Supplies', 'Maintenance'],
    'Capital Expenditures': ['Infrastructure', 'Equipment'],
}

# Funding sources
funding_sources = ['Government Funds', 'Grants', 'Loans', 'Donations']

# Project statuses
project_statuses = ['On Track', 'Delayed', 'Completed']

# Years
years = range(2018, 2024)

# Generate data
data = []

for ministry, departments in ministries.items():
    for department in departments:
        for category, subcategories in categories.items():
            for subcategory in subcategories:
                for year in years:
                    planned_budget = np.random.randint(1_000_000, 10_000_000)
                    actual_expenditure = planned_budget * np.random.uniform(0.8, 1.2)
                    variance = actual_expenditure - planned_budget
                    funding_source = np.random.choice(funding_sources)
                    project_status = np.random.choice(project_statuses)
                    
                    data.append({
                        'ministry': ministry,
                        'department': department,
                        'category': category,
                        'subcategory': subcategory,
                        'year': year,
                        'planned_budget': round(planned_budget, 2),
                        'actual_expenditure': round(actual_expenditure, 2),
                        'variance': round(variance, 2),
                        'funding_source': funding_source,
                        'project_status': project_status,
                    })

# Create DataFrame
df = pd.DataFrame(data)

# Connect to SQLite database
conn = sqlite3.connect('test-database.db')

# Write DataFrame to SQL table
df.to_sql('budget_data', conn, if_exists='replace', index=False)

conn.close()

print("Data generation and database population complete.")
