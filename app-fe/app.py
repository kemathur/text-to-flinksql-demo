import time
import streamlit as st
import requests
import json

def main():
    # st.title("Hello Streamlit!")
    # user_input = st.text_input("Type something:")

    # if st.button("Send to API"):
    #     response = call_api(user_input)
    #     st.write(response.json()['message'])

    st.title("Chat interface")

    # Initialize chat history from previous session(s)
    if "messages" not in st.session_state:
        st.session_state.messages = []

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
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": full_response})

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

if __name__ == "__main__":
    main()

