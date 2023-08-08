import time
import streamlit as st
import requests
import json
import pandas as pd

def main():
    st.title("Chat interface")

    # NOTE: test prints
    # df_test = call_pyflink()
    # st.dataframe(df_test)

    # Initialize chat history from previous session(s)
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Likewise, keep track of executable Flink queries between app reruns
    if "query_exe" not in st.session_state:
        st.session_state.query_exe = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    if prompt := st.chat_input("What's up?"):
        
        # Display user message in chat message container
        with st.chat_message("user"):
            
            # response = call_api(user_input)
            # st.markdown(response.json()['message'])
            st.markdown(prompt)

        # Add user message to chat component
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            # Call API server
            response = call_api(prompt, st.session_state.messages)
            assistant_response = response.json()['message']
            
            # Simulate stream of response with milliseconds delay
            for chunk in assistant_response.split():
                full_response += chunk + " "
                time.sleep(0.05)
                # Add a blinking cursor to simulate typing
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
        
        # Add assistant response to both chat history and query palette
        st.session_state.messages.append({"role": "assistant", "content": full_response})

        # TODO: is there a SQL parser we should run here before appending to state (or regexp)?
        st.session_state.query_exe.append({"role": "assistant", "sql": full_response})

    if st.button('Run lastest response as Flink query!'):
        if len(st.session_state.query_exe) > 0: 
            flink_query = st.session_state.query_exe[-1]["sql"]
            with st.spinner(f'Running query: {flink_query}'):
                response = call_query_api(flink_query) # TODO: expecting a pandas df in json string format
                tdf = pd.DataFrame(response).T.reset_index()
                st.dataframe(tdf)
            st.success('Query executed successfully!')
        else:
            st.write("Sorry, no valid queries in conversation history yet :-(")

def call_api(input_text, messages):
    # Adjust the URL according to your setup
    url = "http://python-app:5000/get-query/"
    params = {
        "input-text": input_text,
        "messages": json.dumps(messages)  # Convert list of dictionaries to a JSON string
    }
    response = requests.get(url, params=params)
    response.raise_for_status()  # This will raise an exception if the API request failed
    return response

# TODO
def call_query_api(flink_sql):
    url = "http://python-app:5000/get-results/" 
    params = {
        "flink-sql": flink_sql,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()  # This will raise an exception if the API request failed
    return response

def call_pyflink():
    url = "http://python-app:5000/test-pyflink/" 
    response = requests.get(url)
    response.raise_for_status()  # This will raise an exception if the API request failed
    return response

if __name__ == "__main__":
    main()

