import os
import streamlit as st
import google.generativeai as genai
import re
import docx
from transform_script_1 import transform_output

# Streamlit setup
st.title("Message Processor for Gemini AI")

def upload_to_gemini(file_path, mime_type=None):
    """Uploads the given file to Gemini."""
    file = genai.upload_file(file_path, mime_type=mime_type)
    st.write(f"Uploaded file '{file.display_name}' as: {file.uri}")
    return file

def select_folder():
    folder_path = st.text_input("Enter the folder path containing images and/or text files")
    return folder_path

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

def main():
    # Get the directory of the script
    code_directory = os.path.dirname(os.path.abspath(__file__))

    # Replace 'YOUR_API_KEY' with your actual Gemini API key
    GEMINI_API_KEY = 'AIzaSyBCGuyDWOBN-Qh9Bi2pzOcFpZgpwcizTU8'
    genai.configure(api_key=GEMINI_API_KEY)

    # Get system prompt
    system_prompt = get_system_prompt(code_directory)

    # Create the model
    generation_config = {
        "temperature": 0.5,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }

    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        generation_config=generation_config,
    )

    # Select folder with images and/or text files
    input_folder = select_folder()
    if not input_folder:
        st.write("No folder selected. Exiting.")
        return

    # Get sorted message files from the code directory
    message_files = get_message_files(code_directory)
    if not message_files:
        st.write("No message files found. Exiting.")
        return

    st.write(f"Found message files: {message_files}")
    st.write(f"Using system prompt: {system_prompt[:50]}...")

    # Prompt the user to select which messages to send (but exclude message_6)
    selected_message_files = [file for file in select_messages(message_files) if "message_6" not in file]

    # Process each file in the folder
    for filename in os.listdir(input_folder):
        file_path = os.path.join(input_folder, filename)

        # Start a chat session for each file
        chat_session = model.start_chat(history=[])
        chat_session.send_message(system_prompt)

        # Determine file type and send content accordingly
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            uploaded_file = upload_to_gemini(file_path)
            initial_message = [uploaded_file, "Analyze this image."]
        elif filename.lower().endswith(('.txt', '.docx')):
            text_content = read_file(file_path)
            initial_message = text_content  # Send text content directly
        else:
            st.write(f"Skipping unsupported file: {filename}")
            continue

        # Send the initial message (file or text)
        initial_response = chat_session.send_message(initial_message)

        # Save the initial response
        output_filename = f"{os.path.splitext(filename)[0]}_response_0.txt"
        output_path = os.path.join(input_folder, output_filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(initial_response.text)
        st.write(f"Saved initial response for {filename} to {output_filename}")

        # Process each selected message file
        for i, message_file in enumerate(selected_message_files, 1):
            message_path = os.path.join(code_directory, message_file)
            message = read_file(message_path)
            st.write(f"Sending message from {message_file}: {message[:50]}...")

            # Upload the message file if it's not a .md file
            if not message_file.endswith('.md'):
                upload_to_gemini(message_path)

            response = chat_session.send_message(message)

            # Extract the suffix from the message file name
            suffix = re.search(r'message_(\w+)', message_file).group(1).lower()

            # Save the response to a text file with the new naming convention
            output_filename = f"{os.path.splitext(filename)[0]}_{suffix}.txt"
            output_path = os.path.join(input_folder, output_filename)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(response.text)

            st.write(f"Saved response for {filename} to {output_filename}")

    st.write("Finished processing all files.")

if __name__ == "__main__":
    main()
