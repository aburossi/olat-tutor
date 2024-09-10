import streamlit as st
from openai import OpenAI
import os
import json
import random
import PyPDF2
import docx
import io
import re

# Access API key from Streamlit secrets
OPENAI_API_KEY = st.secrets["openai"]["api_key"]
client = OpenAI(api_key=OPENAI_API_KEY)

# List of available message types
MESSAGE_TYPES = [
    "single_choice",
    "multiple_choice",
    "kprim",
    "truefalse",
    "draganddrop",
    "inline_fib"
]

def read_prompt_from_md(filename):
    with open(f"{filename}.md", "r") as file:
        return file.read()

def get_chatgpt_response(prompt):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are specialized in generating Q&A in specific formats according to the instructions of the user. The questions are used in a vocational school in switzerland. if the user itself upload a test with Q&A, then you transform the original test into the specified formats."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

def clean_json_string(s):
    # Remove any leading/trailing whitespace
    s = s.strip()
    
    # Remove any markdown code block indicators
    s = re.sub(r'^```json\s*', '', s)
    s = re.sub(r'\s*```$', '', s)
    
    # Replace newlines and multiple spaces in the text with a single space
    s = re.sub(r'\s+', ' ', s)
    
    # Escape newlines within the text fields
    s = re.sub(r'(?<=text": ")(.+?)(?=")', lambda m: m.group(1).replace('\n', '\\n'), s)
    
    # Remove any control characters
    s = ''.join(char for char in s if ord(char) >= 32 or char == '\n')
    
    # Attempt to find JSON-like content within the string
    match = re.search(r'\[.*\]', s, re.DOTALL)
    if match:
        return match.group(0)
    
    return s


def convert_json_to_text_format(json_input):
    if isinstance(json_input, str):
        data = json.loads(json_input)
    else:
        data = json_input

    fib_output = []
    ic_output = []

    for item in data:
        text = item.get('text', '')
        blanks = item.get('blanks', [])
        wrong_substitutes = item.get('wrong_substitutes', [])

        num_blanks = len(blanks)

        # Fill-in-the-Blanks format
        fib_lines = [
            "Type\tFIB",
            "Title\t✏✏Vervollständigen Sie die Lücken mit dem korrekten Begriff.✏✏",
            f"Points\t{num_blanks}"
        ]

        for blank in blanks:
            text = text.replace(blank, "{blank}", 1)

        parts = text.split("{blank}")
        for index, part in enumerate(parts):
            fib_lines.append(f"Text\t{part.strip()}")
            if index < len(blanks):
                fib_lines.append(f"1\t{blanks[index]}\t20")

        fib_output.append('\n'.join(fib_lines))

        # Inline Choice format
        ic_lines = [
            "Type\tInlinechoice",
            "Title\tWörter einordnen",
            "Question\t✏✏Wählen Sie die richtigen Wörter.✏✏",
            f"Points\t{num_blanks}"
        ]

        all_options = blanks + wrong_substitutes
        random.shuffle(all_options)

        for index, part in enumerate(parts):
            ic_lines.append(f"Text\t{part.strip()}")
            if index < len(blanks):
                options_str = '|'.join(all_options)
                ic_lines.append(f"1\t{options_str}\t{blanks[index]}\t|")

        ic_output.append('\n'.join(ic_lines))

    return '\n\n'.join(fib_output), '\n\n'.join(ic_output)

def transform_output(json_string):
    try:
        cleaned_json_string = clean_json_string(json_string)
        json_data = json.loads(cleaned_json_string)
        fib_output, ic_output = convert_json_to_text_format(json_data)
        return f"{ic_output}\n---\n{fib_output}"
    except json.JSONDecodeError as e:
        st.error(f"Error parsing JSON: {e}")
        st.text("Cleaned input:")
        st.code(cleaned_json_string, language='json')
        st.text("Original input:")
        st.code(json_string)
        
        # Attempt to salvage partial JSON
        try:
            # Add missing closing bracket if necessary
            if not cleaned_json_string.strip().endswith(']'):
                cleaned_json_string += ']'
            partial_json = json.loads(cleaned_json_string)
            st.warning("Attempted to salvage partial JSON. Results may be incomplete.")
            fib_output, ic_output = convert_json_to_text_format(partial_json)
            return f"{ic_output}\n---\n{fib_output}"
        except:
            st.error("Unable to salvage partial JSON.")
            return "Error: Invalid JSON format"
    except Exception as e:
        st.error(f"Error processing input: {str(e)}")
        st.text("Original input:")
        st.code(json_string)
        return "Error: Unable to process input"

def extract_text_from_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def extract_text_from_docx(file):
    doc = docx.Document(file)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

st.title("OLAT Fragen Generator")

# File uploader
uploaded_file = st.file_uploader("Upload a PDF or DOCX file", type=["pdf", "docx"])

text_content = ""
if uploaded_file is not None:
    # Extract text based on file type
    if uploaded_file.type == "application/pdf":
        text_content = extract_text_from_pdf(uploaded_file)
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        text_content = extract_text_from_docx(uploaded_file)
    else:
        st.error("Unsupported file type. Please upload a PDF or DOCX file.")
    
    st.success("Text extracted successfully. You can now edit it in the text area below.")

user_input = st.text_area("Füge deinen Text ein oder bearbeite den extrahierten Text:", value=text_content)

# Add a text area for learning goals
learning_goals = st.text_area("Lernziele (Falls besondere Aspekte des Text mit den Fragen geprüft werden müssen):")

# Create checkboxes for each message type
selected_types = []
st.subheader("Wähle die Art von Fragen zu generieren:")
for msg_type in MESSAGE_TYPES:
    if st.checkbox(msg_type.replace("_", " ").title()):
        selected_types.append(msg_type)

if st.button("Generiere Fragen"):


# File uploader
uploaded_file = st.file_uploader("Upload a PDF or DOCX file", type=["pdf", "docx"])

text_content = ""
if uploaded_file is not None:
    # Extract text based on file type
    if uploaded_file.type == "application/pdf":
        text_content = extract_text_from_pdf(uploaded_file)
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        text_content = extract_text_from_docx(uploaded_file)
    else:
        st.error("Unsupported file type. Please upload a PDF or DOCX file.")
    
    st.success("Text extracted successfully. You can now edit it in the text area below.")

user_input = st.text_area("Füge deinen Text ein oder bearbeite den extrahierten Text:", value=text_content, key="user_input_area")

# Add a text area for learning goals
learning_goals = st.text_area("Lernziele (Falls besondere Aspekte des Text mit den Fragen geprüft werden müssen):", key="learning_goals_area")

# Create checkboxes for each message type
selected_types = []
st.subheader("Wähle die Art von Fragen zu generieren:")
for msg_type in MESSAGE_TYPES:
    if st.checkbox(msg_type.replace("_", " ").title(), key=f"checkbox_{msg_type}"):
        selected_types.append(msg_type)

if st.button("Generiere Fragen"):
    if user_input and selected_types:
        all_responses = ""
        for msg_type in selected_types:
            prompt_template = read_prompt_from_md(msg_type)
            full_prompt = f"{prompt_template}\n\nUser Input: {user_input}\n\nLearning Goals: {learning_goals}"
            
            try:
                response = get_chatgpt_response(full_prompt)
                
                if msg_type == "inline_fib":
                    processed_response = transform_output(response)
                    st.subheader(f"Generated and Processed Response for JSON Format:")
                    st.text(processed_response)
                    all_responses += f"{processed_response}\n\n"
                else:
                    st.subheader(f"Generated Response for {msg_type.replace('_', ' ').title()}:")
                    st.write(response)
                    all_responses += f"{response}\n\n"
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
        st.warning("Please enter some text or upload a file.")
    elif not selected_types:
        st.warning("Please select at least one message type.")