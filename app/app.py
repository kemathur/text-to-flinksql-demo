from flask import Flask, request, jsonify
import re

app = Flask(__name__)

@app.route('/get-query/', methods=['GET'])
def get_query():
    input_text = request.args.get('input-text')
    if input_text:
        # Removing special characters using regex
        cleaned_text = re.sub(r'[^a-zA-Z0-9\s]', '', input_text) if input_text else ""
        return jsonify(message=f"Hello {cleaned_text}!")
    return jsonify(message="Hello World!")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
