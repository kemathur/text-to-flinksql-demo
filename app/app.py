from flask import Flask, request, jsonify
import json
import openai
import re
import logging
import os

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG)

endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
key = os.environ.get("AZURE_OPENAI_KEY")
deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT")
app.logger.info(f"endpoint: {endpoint}")
app.logger.info(f"key: {key}")
app.logger.info(f"deployment: {deployment}")
"""
Code References:
https://docs.streamlit.io/knowledge-base/tutorials/build-conversational-apps
https://learn.microsoft.com/en-us/azure/ai-services/openai/chatgpt-quickstart?tabs=command-line&pivots=programming-language-python
"""

################

# Set OpenAI API key from Streamlit secrets
openai.api_base = endpoint # your endpoint should look like the following https://YOUR_RESOURCE_NAME.openai.azure.com/
openai.api_key = key
openai.api_type = 'azure'
openai.api_version = '2023-05-15' # this may change in the future

@app.route('/get-query/', methods=['GET'])
def get_query():
    input_text = request.args.get('input-text')
    if input_text:
        # Removing special characters using regex
        cleaned_text = input_text
        # cleaned_text = re.sub(r'[^a-zA-Z0-9\s]', '', input_text) if input_text else ""
        app.logger.info(f"Cleaned Text: {cleaned_text}")
        
        # Deserialize the JSON string to a list of dictionaries
        messages_str = request.args.get('messages', "[]")
        try:
            messages = json.loads(messages_str)
        except json.JSONDecodeError:
            return jsonify(error="Invalid messages format"), 400
        response = openai.ChatCompletion.create(
                engine=deployment, 
                messages = 
                [ \
                    {"role": message["role"], "content": message["content"]}
                    for message in messages
                ] # Feed in past messages (both user and chatbot generated)
                + [ \
                    {"role": "user", "content": cleaned_text}
                ]
            )
        assistant_response = response['choices'][0]['message']["content"].replace('\n', '').replace(' .', '.').strip()
        return jsonify(message=f"{assistant_response}!")
    return jsonify(message="Hello World!")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
