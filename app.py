import os
import streamlit as st
import openai  # Use OpenAI instead of google.generativeai
import re
from io import StringIO


# Streamlit setup
st.title("GPT-4 Message Processor")

# Access API key from Streamlit secrets
OPENAI_API_KEY = st.secrets["openai"]["api_key"]
openai.api_key = OPENAI_API_KEY

def get_system_prompt(code_directory):
    """Returns the system prompt from system_prompt.md if it exists, otherwise returns a default prompt."""
    system_prompt_path = os.path.join(code_directory, 'system_prompt.md')
    if os.path.exists(system_prompt_path):
        with open(system_prompt_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    else:
        return "You are a helpful assistant."

def download_text_file(content, filename):
    """Allows users to download the response as a txt file in Streamlit."""
    buffer = StringIO()
    buffer.write(content)
    buffer.seek(0)
    st.download_button(label=f"Download {filename}", data=buffer, file_name=filename, mime="text/plain")

def generate_gpt4_response(prompt):
    """Generates a response using GPT-4."""
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": prompt},
        ],
        max_tokens=8192,
        temperature=0.5,
        top_p=0.95,
        n=1,
    )
    return response['choices'][0]['message']['content']

def main():
    # Get the directory of the script
    code_directory = os.path.dirname(os.path.abspath(__file__))

    # Get system prompt
    system_prompt = get_system_prompt(code_directory)
    
    st.write(f"Using system prompt: {system_prompt[:50]}...")

    # User inputs plain text into a text area
    user_input = st.text_area("Paste your plain text here:")

    if user_input:
        st.write(f"Processing input...")

        # Send the input and system prompt to GPT-4
        initial_message = f"{system_prompt}\n\n{user_input}"
        initial_response = generate_gpt4_response(initial_message)

        # Display the response in the app
        st.write(f"GPT-4 Response: {initial_response}")

        # Save and offer the initial response as a downloadable file
        output_filename = "response.txt"
        download_text_file(initial_response, output_filename)

if __name__ == "__main__":
    main()
