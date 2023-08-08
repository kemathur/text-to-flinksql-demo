import streamlit as st
import requests

def main():
    st.title("Hello Streamlit!")
    user_input = st.text_input("Type something:")

    if st.button("Send to API"):
        response = call_api(user_input)
        st.write(response.json()['message'])

def call_api(input_text):
    # Adjust the URL according to your setup
    url = "http://python-app:5000/get-query/"
    params = {"input-text": input_text}
    response = requests.get(url, params=params)
    response.raise_for_status()  # This will raise an exception if the API request failed
    return response

if __name__ == "__main__":
    main()

