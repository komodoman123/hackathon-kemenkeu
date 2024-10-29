import openai
import requests

# Set your OpenAI API key
openai.api_key = "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"

# Function to upload an image and ask a question about it
def ask_question_about_image(image_path, question):
    with open(image_path, "rb") as image_file:
        # Sending the image and the question to OpenAI API
        response = openai.Image.create(
            file=image_file,
            prompt=question,
            n=1,
            size="1024x1024"
        )
    return response['data'][0]['url']

# Path to the image you want to upload
image_path = "test.png"

# The question you want to ask about the image
question = "What can you tell me about this image?"

# Call the function and get the result
result_url = ask_question_about_image(image_path, question)
print("Generated Image URL:", result_url)
