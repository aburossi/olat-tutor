import streamlit as st
from openai import OpenAI
import os

# Access API key from Streamlit secrets
OPENAI_API_KEY = st.secrets["openai"]["api_key"]
client = OpenAI(api_key=OPENAI_API_KEY)

def read_prompt_from_md():
    with open("message_1_SC.md", "r") as file:
        return file.read()

def get_chatgpt_response(prompt):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

st.title("ChatGPT Prompt Generator")

user_input = st.text_area("Enter your text:")

if st.button("Generate Response"):
    if user_input:
        prompt_template = read_prompt_from_md()
        full_prompt = f"{prompt_template}\n\nUser Input: {user_input}"
        
        try:
            response = get_chatgpt_response(full_prompt)
            
            st.subheader("Generated Response:")
            st.write(response)
            
            st.download_button(
                label="Download Response",
                data=response,
                file_name="response.txt",
                mime="text/plain"
            )
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
    else:
        st.warning("Please enter some text.")
