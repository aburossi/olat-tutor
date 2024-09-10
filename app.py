import streamlit as st
from openai import OpenAI
import os
import json
import random

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
    "json_format"  # New message type
]

def read_prompt_from_md(filename):
    with open(f"{filename}.md", "r") as file:
        return file.read()

def get_chatgpt_response(prompt):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are specialized in generating Q&A in specific formats according to the instructions of the user. The questions are used in a vocational school in switzerland."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

def clean_json_string(s):
    s = s.strip()
    s = s.lstrip('```json').rstrip('```')
    return s

def convert_json_to_text_format(json_input):
    if isinstance(json_input, str):
        data = json.loads(json_input)
    else:
        data = json_input

    fib_output = []
    ic_output = []

    for item in data:
        page_number = item.get('page_number', 'N/A')
        subject = item.get('subject', 'N/A')
        bloom_level = item.get('bloom_level', 'N/A')
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
            text = text.replace(blank, f"{{blank}}", 1)

        parts = text.split("{blank}")
        for index, part in enumerate(parts):
            fib_lines.append(f"Text\t{part.strip()}")
            if index < len(blanks):
                fib_lines.append(f"1\t{blanks[index]}\t20")

        fib_output.append('\n'.join(fib_lines))

        # Inline Choice format
        ic_lines = [
            "Type\tInlinechoice",
            *common_header,
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
        return f"Error parsing JSON: {e}\n\nCleaned input:\n{cleaned_json_string}\n\nOriginal input:\n{json_string}"
    except Exception as e:
        return f"Error processing input: {e}\n\nOriginal input:\n{json_string}"

st.title("OLAT Fragen Generator")

user_input = st.text_area("Enter your text:")

# Add a text area for learning goals
learning_goals = st.text_area("Enter learning goals (Lernziele):")

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
            full_prompt = f"{prompt_template}\n\nUser Input: {user_input}\n\nLearning Goals: {learning_goals}"
            
            try:
                response = get_chatgpt_response(full_prompt)
                
                if msg_type == "json_format":
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
        st.warning("Please enter some text.")
    elif not selected_types:
        st.warning("Please select at least one message type.")