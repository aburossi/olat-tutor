import os
import streamlit as st
import openai  # Use OpenAI instead of google.generativeai
import re
import docx
from io import StringIO


# Streamlit setup
st.title("GPT-4 Message Processor")

# Access API key from Streamlit secrets
OPENAI_API_KEY = st.secrets["openai"]["api_key"]
openai.api_key = OPENAI_API_KEY

def read_file(file_path):
    """Reads the content of a file."""
    if file_path.endswith('.docx'):
        doc = docx.Document(file_path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return '\n'.join(full_text)
    else:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()

def get_message_files(folder_path):
    """Returns a sorted list of message files in the given folder."""
    message_files = []
    for filename in os.listdir(folder_path):
        if filename.startswith('message_') and (
            filename.endswith('.md') or 
            filename.endswith('.txt') or 
            filename.endswith('.docx')
        ):
            message_files.append(filename)
    
    # Sort the message files based on their number
    return sorted(message_files, key=lambda x: int(re.search(r'message_(\d+)', x).group(1)))

def get_system_prompt(code_directory):
    """Returns the system prompt from system_prompt.md if it exists, otherwise returns a default prompt."""
    system_prompt_path = os.path.join(code_directory, 'system_prompt.md')
    if os.path.exists(system_prompt_path):
        return read_file(system_prompt_path)
    else:
        return "You are a helpful assistant."

def select_messages(message_files):
    """Displays message files for selection using Streamlit multiselect widget."""
    st.write("Message files found:")
    return st.multiselect("Select the messages to send", message_files)

def download_text_file(content, filename):
    """Allows users to download the response as a txt file in Streamlit."""
    buffer = StringIO()
    buffer.write(content)
    buffer.seek(0)
    st.download_button(label=f"Download {filename}", data=buffer, file_name=filename, mime="text/plain")

def generate_gpt4_response(prompt):
    """Generates a response using GPT-4."""
    response = openai.ChatCompletion.create(
        model="gpt-4",
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

    # Display the folder input field for selecting where the messages are stored
    input_folder = st.text_input("Enter the path of the folder with images and text files")
    if not input_folder:
        st.write("No folder selected. Exiting.")
        return

    # Get sorted message files from the repository folder
    message_files = get_message_files(code_directory)
    if not message_files:
        st.write("No message files found in the repo. Exiting.")
        return

    st.write(f"Found message files: {message_files}")
    st.write(f"Using system prompt: {system_prompt[:50]}...")

    # Allow the user to select which messages to send (message_6 is excluded)
    selected_message_files = [file for file in select_messages(message_files) if "message_6" not in file]

    # Process each file in the selected folder
    for filename in os.listdir(input_folder):
        file_path = os.path.join(input_folder, filename)

        # Handle text files directly (GPT-4 doesn't support direct image analysis without specialized models)
        if filename.lower().endswith(('.txt', '.docx')):
            text_content = read_file(file_path)
            initial_message = f"{system_prompt}\n\n{text_content}"  # Send text content along with system prompt

            # Send the initial message and get the response from GPT-4
            initial_response = generate_gpt4_response(initial_message)

            # Save and offer the initial response as a downloadable file
            output_filename = f"{os.path.splitext(filename)[0]}_response_0.txt"
            st.write(f"Response for {filename}: {initial_response[:100]}...")
            download_text_file(initial_response, output_filename)
        else:
            st.write(f"Skipping unsupported file: {filename}")
            continue

        # Process each selected message file from the repo
        for i, message_file in enumerate(selected_message_files, 1):
            message_path = os.path.join(code_directory, message_file)
            message = read_file(message_path)
            st.write(f"Sending message from {message_file}: {message[:50]}...")

            follow_up_message = f"{system_prompt}\n\n{message}"
            response = generate_gpt4_response(follow_up_message)

            # Extract the suffix from the message file name
            suffix = re.search(r'message_(\d+)', message_file).group(1)

            # Save and offer the response as a downloadable file
            output_filename = f"{os.path.splitext(filename)[0]}_message_{suffix}.txt"
            download_text_file(response, output_filename)

        st.write(f"Finished processing {filename}\n")

if __name__ == "__main__":
    main()
