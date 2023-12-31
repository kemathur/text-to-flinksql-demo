
#repeat after me: select * from pageviews_kafka;
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
env_settings = EnvironmentSettings.new_instance().in_streaming_mode().build()
t_env = TableEnvironment.create(env_settings)
# t_env = TableEnvironment.create(EnvironmentSettings.in_streaming_mode())

# Specify the table environment configuration
t_env_config = t_env.get_config()

## COMMENTED OUT: attempt to connect to SQL client run in a separate terminal
# rest_url = "http://sql-client:8081"
# t_env_config.set("execution.target", "remote")
# t_env_config.set("execution.remote-url", rest_url)
# t_env_config.set("jobmanager.rpc.address", "jobmanager") # comms to jobmanager

t_env_config.set("execution.target", "local")
t_env_config.set("execution.shutdown-on-application-finish", "false")
t_env_config.set("parallelism.default", "1")

# Assume that you have a Flink catalog and data source set up
t_env.use_catalog('default_catalog')
t_env.use_database('default_database')

# Given the table name pageviews_kafka, and columns: url, user_id, browser and proc_time. Return number of distinct web visitors every 5 seconds, grouped by browser

# TODO: this DDL statement does not work in PyFlink
my_source_ddl = """
    CREATE TABLE `pageviews_kafka` (
    `url` STRING,
    `user_id` STRING,
    `browser` STRING,
    `proc_time` as PROCTIME()
    )
    WITH (
    'connector' = 'datagen',
    'rows-per-second' = '10'
    );
"""

my_sink_ddl = """
    CREATE TABLE `print` (
    `url` STRING,
    `user_id` STRING,
    `browser` STRING,
    `proc_times` as PROCTIME()
    )
"""

# my_source_ddl =  """CREATE TABLE pageviews_kafka (
#   random_str STRING
# ) WITH (
#   'connector' = 'datagen',
#   'rows-per-second' = '100'
# )
# """
t_env.execute_sql(my_source_ddl)
t_env.execute_sql("select * from pageviews_kafka limit 10").print() # Test print

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
        
        prompt_ksql = """
        You are a code generator that helps people translate KSQL to Flink SQL. 
        Return the Flink SQL select statements only so people can execute the code directly.

        Remember the difference between KSQL and Flink SQL is syntax for window functions
        such as TUMBLE and HOP commands. Unlike in KSQL where you can just call WINDOW TUMBLING,
        in Flink SQL you need to run TUMBLE(Table table_name, DESCRIPTOR(rowtime), INTERVAL X) to specify
        the window length.

        Example KSQL input:
        SELECT windowstart, count(*) AS cnt
        FROM your_table
        WINDOW TUMBLING (SIZE 5 SECONDS)
        GROUP BY windowstart
        EMIT CHANGES;

        Correct Output:
        SELECT window_start as windowstart, count(*) AS cnt
        FROM TABLE(
          TUMBLE(TABLE your_table, DESCRIPTOR(rowtime), INTERVAL '5' SECOND))
        GROUP BY window_start;

        Please do not add ORDER BY to Flink SQL query.
        User input:
        """
        
        
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
        
        if 'ksql' in cleaned_text.lower():
            response = openai.ChatCompletion.create(
                engine=deployment,
                #model='gpt-3.5-turbo',
                temperature=1,
                messages=[
                    {"role": "user", "content": prompt_ksql+cleaned_text}
                ]
            )
        else: 
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

    app.logger.info(f"\n\n\t\tRunning test query again")
    # t_env.execute_sql("select * from pageviews_kafka limit 3").print() # Test print within GET request

    try:
        input_query = request.args.get('flink-sql')
        app.logger.info(f"input_query: {input_query}")
        if input_query:
            
            t_env.execute_sql(input_query.replace(";","")+" limit 5;").print()
            t_result = t_env.execute_sql(input_query.replace(";","")+" limit 5;")

            results_list = []

            ## NOTE: seeing if basic queries execute successfully and can print to logs
            ctr = 0

            with t_result.collect() as results:
                for result in results:
                    app.logger.info(f"result: {result}")  
                    results_list.append(str(result)) 
                app.logger.info(f"Finished outputting results")

            ## TODO: return results as JSON   
            # tdf = t_result.limit(100).to_pandas()
            # return tdf.to_json(orient="records")

            return jsonify(result=results_list)
        
        return pd.DataFrame({'A' : []}).to_json(orient="records") # empty dataframe
    except Exception as e:
        app.logger.error(f"error: {e}")
        return jsonify(error=str(e)), 500


@app.route('/test-pyflink/', methods=['GET'])
def test_pyflink():
    return pageviews_kafka.limit(100).to_pandas()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
