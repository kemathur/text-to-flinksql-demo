import streamlit as st

def main():
    st.title("Hello Streamlit!")
    user_input = st.text_input("Type something:")
    st.write(f"You typed: {user_input}")

if __name__ == "__main__":
    main()
