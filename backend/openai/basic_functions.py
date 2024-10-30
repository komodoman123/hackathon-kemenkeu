import openai
import json
from openai import OpenAI
from list_of_tools import mini_retrieve_similar_keywords, schema_check, intermediary_dataframe_retrieval
import api_keys
tool_functions = {
    'mini_retrieve_similar_keywords': mini_retrieve_similar_keywords,
    'schema_check': schema_check,
    'intermediary_dataframe_retrieval': intermediary_dataframe_retrieval
            }

client = OpenAI(api_key=api_keys.openai_key)

prompt = """Guide the user in retrieving relevant information from a database using keyword similarity.

You will assist a user by following a structured sequence to retrieve database information based on keyword similarity. Use provided tools to refine keyword search and construct SQL queries.

# Steps

1. **New Query Start**: Begin every task from this step to ensure consistency.
2. **Use the `mini_retrieve_similar_keywords` tool**: Utilize this tool to find keywords similar to the user's query, filtering data relevant to their request.
3. **Validate and select appropriate keywords**: From the similar keywords returned, select those with high similarity scores (above 0.6). Group them logically based on meaning and their relationship to the user's request.
4. **Check database information**: Use the `schema_check` tool to understand the database table structure before querying.
5. **Construct a SQL query**:
   - Use the validated keywords to filter entries in the 'filtered_keywords' column.
   - Apply logical operators: use `OR` for synonyms and `AND` for non-synonyms. Exclude the word 'pengadaan'.
   - Follow examples for query construction.

6. **Execute query**: Use the `intermediary_dataframe_retrieval` tool to run the constructed query and retrieve data.

# Output Format

- The SQL query should be structured to align with the formatted examples.
- Return results from the query execution in a clear and concise manner.

# Examples

**User Request:** "informasi terkait perbaikan gedung"  
- **Group 1:** 'perbaikan', 'rehabilitasi', 'pemeliharaan'  
- **Group 2:** 'gedung', 'bangunan', 'kantor'  
- **Query Result:**  
  ```plaintext
  SELECT * FROM data_pengadaan WHERE (filtered_keywords LIKE '%perbaikan%' OR filtered_keywords LIKE '%rehabilitasi%' OR filtered_keywords LIKE '%pemeliharaan%') AND (filtered_keywords LIKE '%gedung%' OR filtered_keywords LIKE '%bangunan%' OR filtered_keywords LIKE '%kantor%');
  ```
  (In practice, results will vary based on database contents.)

**User Request:** "informasi terkait alat tulis"  
- **Group 1:** 'alat', 'peralatan'  
- **Group 2:** 'tulis', 'pensil', 'pulpen'  
- **Query Result:**  
  ```plaintext
  SELECT * FROM data_pengadaan WHERE (filtered_keywords LIKE '%alat%' OR filtered_keywords LIKE '%peralatan%') AND (filtered_keywords LIKE '%tulis%' OR filtered_keywords LIKE '%pensil%' OR filtered_keywords LIKE '%pulpen%');
  ```
  (In practice, results will vary based on database contents.)

# Notes

- Ensure each step is completed without omissions.
- Call one tool at a time. Don't call two tools at the same time. Follow the step carefully.
- **Do NOT include any irrelevant information to the user** such as which steps you took.
- Avoid performing DML operations such as INSERT, UPDATE, DELETE, or DROP.
- Where feasible, respond directly with known information rather than performing unnecessary operations.
"""

def deploy_assistant(all_tools):
    assistant = client.beta.assistants.create(
    name="Data Agent",
    instructions=prompt,
    tools=all_tools,
    model="gpt-4o",
    )

    return assistant

def run_assistant(assistant_id, thread, question):

    run = openai.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id,
        instructions=question
    )

    return run

def execute_tool_call(tool_call):
    tool_name = tool_call.function.name
    print(f'Using tool: {tool_name}')
        
    try:
        args = json.loads(tool_call.function.arguments)
        function = tool_functions.get(tool_name)
        output = function(**args) if args else function()        
    except Exception as e:
        output = json.dumps({'error': str(e)})

    return {
            'tool_call_id': tool_call.id,
            'output': output
        }

def get_answer(run, thread):
    while run.status != 'completed':
        run = openai.beta.threads.runs.retrieve(
            thread_id = thread.id,
            run_id = run.id
        )
    
        print(f"Run status: {run.status}")
        if run.status == 'requires_action':
            tool_calls = run.required_action.submit_tool_outputs.tool_calls
            tool_outputs = [execute_tool_call(call) for call in run.required_action.submit_tool_outputs.tool_calls]
            
            run = client.beta.threads.runs.submit_tool_outputs(
                thread_id = thread.id,
                run_id = run.id,
                tool_outputs=tool_outputs
            )
            

    messages = openai.beta.threads.messages.list(
        thread_id=thread.id
    )

    annotations = messages.data[0].content[0].text.annotations
    message_content = messages.data[0].content[0].text.value

    return annotations, message_content

def add_message(thread, message_content, role):
    return client.beta.threads.messages.create(
        thread_id=thread.id,
        role=role,
        content=message_content,
    )