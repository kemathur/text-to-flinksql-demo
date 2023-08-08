from flask import Flask, request, jsonify
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

@app.route('/get-query/', methods=['GET'])
def get_query():
    input_text = request.args.get('input-text')
    if input_text:
        # Removing special characters using regex
        cleaned_text = input_text
        # cleaned_text = re.sub(r'[^a-zA-Z0-9\s]', '', input_text) if input_text else ""
        app.logger.info(f"Cleaned Text: {cleaned_text}")
        return jsonify(message=f"Hello {cleaned_text}!")
    return jsonify(message="Hello World!")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
