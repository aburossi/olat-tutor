import streamlit as st
from openai import OpenAI
import os

# Access API key from Streamlit secrets
OPENAI_API_KEY = st.secrets["openai"]["api_key"]
client = OpenAI(api_key=OPENAI_API_KEY)

# List of available message types
MESSAGE_TYPES = [
    "single_choice",
    "multiple_choice",
    "kprim",
    "truefalse",
    "draganddrop"
]

def read_prompt_from_md(filename):
    with open(f"{filename}.md", "r") as file:
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

# Create checkboxes for each message type
selected_types = []
st.subheader("Select message types:")
for msg_type in MESSAGE_TYPES:
    if st.checkbox(msg_type.replace("_", " ").title()):
        selected_types.append(msg_type)

if st.button("Generate Response"):
    if user_input and selected_types:
        all_responses = ""
        for msg_type in selected_types:
            prompt_template = read_prompt_from_md(msg_type)
            full_prompt = f"{prompt_template}\n\nUser Input: {user_input}"
            
            try:
                response = get_chatgpt_response(full_prompt)
                
                st.subheader(f"Generated Response for {msg_type.replace('_', ' ').title()}:")
                st.write(response)
                
                all_responses += f"Response for {msg_type.replace('_', ' ').title()}:\n\n{response}\n\n{'='*50}\n\n"
            except Exception as e:
                st.error(f"An error occurred for {msg_type}: {str(e)}")
        
        if all_responses:
            st.download_button(
                label="Download All Responses",
                data=all_responses,
                file_name="all_responses.txt",
                mime="text/plain"
            )
    elif not user_input:
        st.warning("Please enter some text.")
    elif not selected_types:
        st.warning("Please select at least one message type.")
