import openai
import os 
import api_keys
from function_definition import mini_retrieve_similar_keywords_definition, intermediary_dataframe_retrieval_definition, schema_check_definition
from list_of_tools import mini_retrieve_similar_keywords
from basic_functions import deploy_assistant, add_message, run_assistant, get_answer
print("OpenAI API key:", os.environ['OPENAI_API_KEY'])
print(api_keys.openai_key)
os.environ['OPENAI_API_KEY'] = api_keys.openai_key

all_tools = [mini_retrieve_similar_keywords_definition, schema_check_definition, intermediary_dataframe_retrieval_definition]

# for first time use, deploy assistant and get the assistant.id
# assistant = deploy_assistant(all_tools)
# assistant_id = assistant.id
# print(assistant_id)

thread = openai.beta.threads.create()

while True:
    question = input("how may I help you today? \n")
    if "exit" in question.lower():
        break

    add_message(thread, question, role='user')

    run = run_assistant(assistant_id="asst_k2yi0kNWxlgBOAlsB690EH8c", thread=thread, question=question)
    annotations, message_content = get_answer(run, thread)
    
    add_message(thread, message_content, role='assistant')
    
    print(message_content)

print("happy to serve you")