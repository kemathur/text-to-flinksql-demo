from flask import Flask, request, jsonify
import json
import openai
import re
import logging
import os

import pandas as pd

from pyflink.common import Row
from pyflink.table import (EnvironmentSettings, TableEnvironment, TableDescriptor, Schema,
                           DataTypes, FormatDescriptor)
from pyflink.table.expressions import lit, col
from pyflink.table.udf import udtf

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG)

endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
key = os.environ.get("AZURE_OPENAI_KEY")
deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT")
app.logger.info(f"endpoint: {endpoint}")
app.logger.info(f"key: {key}")
app.logger.info(f"deployment: {deployment}")

# Flink REST endpoint (local)
# rest_url = "http://localhost:8081"
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

# Set up PyFlink table environment with defaults
t_env = TableEnvironment.create(EnvironmentSettings.in_streaming_mode())
t_env.get_config().set("parallelism.default", "1")

# TODO: configuration does not work in Table API
# my_source_ddl = """
#     CREATE TABLE `pageviews` (
#     `url` STRING,
#     `user_id` STRING,
#     `browser` STRING,
#     `ts` TIMESTAMP(3)
#     )
#     WITH (
#     'connector' = 'datagen',
#     'rows-per-second' = '10',
#     'fields.url.expression' = '/#{GreekPhilosopher.name}.html',
#     'fields.user_id.expression' = '#{numerify ''user_##''}',
#     'fields.browser.expression' = '#{Options.option ''chrome'', ''firefox'', ''safari'')}',
#     'fields.ts.expression' =  '#{date.past ''5'',''1'',''SECONDS''}'
#     );
# """

my_source_ddl =  """CREATE TEMPORARY TABLE pageviews (
  random_str STRING
) WITH (
  'connector' = 'datagen',
  'rows-per-second' = '100'
)
"""
t_env.execute_sql(my_source_ddl)
t_env.execute_sql("select * from pageviews limit 10").print() # Test print

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
        prompt_fixed = """
        You are a code generator that helps people write Flink SQL language. 
        Return the Flink SQL select statements only so people can execute the code directly.

        Remember the difference between Flink SQL and standard SQL is the use of window functions
        such as TUMBLE, HOP and CUMULATE and GROUPING SETS.

        The TUMBLE function assigns a window for each row of a relation based on a time attribute field.
        Example: To get the total price every 10 minutes, the command is:
        SELECT window_start, SUM(price) total_price
        FROM TABLE(TUMBLE(TABLE your_table, DESCRIPTOR(event_ts), INTERVAL  '10' MINUTES))
        GROUP BY window_start;
        Example: To get the number of user logins every 30 seconds, the command is:
        SELECT window_start, count(user_id) count_user
        FROM TABLE(TUMBLE(TABLE your_table, DESCRIPTOR(event_ts), INTERVAL '30' seconds))
        GROUP BY window_start;

        The HOP function assigns elements to windows of fixed length. 

        Example: To get the total price every 10 minutes, by supplier:
        SELECT window_start, supplier_id, SUM(price) as price
          FROM TABLE(
            TUMBLE(TABLE Bid, DESCRIPTOR(bidtime), INTERVAL '10' MINUTES))
          GROUP BY window_start, supplier_id;
        Please do not add ORDER BY to the query. If there's no specified table names, use your_table as the default.

        User input:
        """
        response = openai.ChatCompletion.create(
            engine=deployment,
            #model='gpt-3.5-turbo',
            temperature=1,
            messages=[
                {"role": "user", "content": prompt_fixed+cleaned_text}
            ]
        )

        # response = openai.ChatCompletion.create(
        #         engine=deployment,
        #         messages =
        #         [ \
        #             {"role": message["role"], "content": message["content"]}
        #             for message in messages
        #         ] # Feed in past messages (both user and chatbot generated)
        #         + [ \
        #             {"role": "user", "content": cleaned_text}
        #         ]
        #     )
        # assistant_response = response['choices'][0]['message']["content"].replace('\n', '').replace(' .', '.').strip()
        # return jsonify(message=f"{assistant_response}!")
        assistant_response = response['choices'][0]['message']["content"]
        return jsonify(message=f"{assistant_response}")
    return jsonify(message="Hello World!")

@app.route('/get-results/', methods=['GET'])
def get_query_results():
    input_query = request.args.get('flink-sql')
    if input_query:
        t_result = t_env.execute_sql(input_query)
        tdf = t_result.limit(100).to_pandas()
        return tdf.to_json(orient="records")
    return pd.DataFrame({'A' : []}).to_json(orient="records") # empty dataframe


@app.route('/test-pyflink/', methods=['GET'])
def test_pyflink():
    return pageviews.limit(100).to_pandas()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
