import streamlit as st
import fitz  # PyMuPDF
import re
import tempfile
import os
from nameparser import HumanName
import spacy

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Function to extract text from PDF using PyMuPDF
def extract_text_from_pdf(pdf_path):
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text()
    return text

# Function to extract emails using regex
def extract_emails(text):
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.findall(email_pattern, text)

# Function to extract phone numbers using regex
def extract_phone_numbers(text):
    phone_pattern = r'\+?\d[\d -]{8,}\d'
    return re.findall(phone_pattern, text)

def preprocess_text_for_spacy(text):
    doc = nlp(text)
    return doc
# Function to extract addresses using regex
def extract_addresses_with_spacy(text):
    addresses = []
    doc = preprocess_text_for_spacy(text)

    for ent in doc.ents:
        if ent.label_ == "GPE":  # Check if entity is a location
            address = ent.text
            # Check if address ends with 6-digit pincode
            if re.search(r'[0-9]{1,3} .+, .+, [A-Z]{2} [0-9]{3}', address):
                addresses.append(address)

    return addresses


# Function to extract name from the first line using spaCy and nameparser
def extract_name_from_first_line(text):
    first_line = text.strip().split("\n")[0]
    # Check if the first line is a person's name
    if first_line:
        # Remove email from the first line if present
        first_line = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', first_line).strip()
        name = HumanName(first_line)
        return name
    return HumanName("")  # Return empty name if not identified as a person

# Function to process extracted names into first and last names
def process_names(name):
    if name:
        first_name = name.first
        last_name = name.last
    else:
        first_name = "Not Found"
        last_name = "Not Found"
    return first_name, last_name

def preprocess_text(text):
    subheadings = ["Education", "Experience", "Skills", "Projects", "Certifications", "Languages"]
    for subheading in subheadings:
        text = re.sub(rf'\s*{subheading}\s*', f'\n{subheading}\n', text, flags=re.IGNORECASE)
    return text

# Streamlit app
st.title("Resume Upload and Form Fill")

# Upload PDF
uploaded_file = st.file_uploader("Choose a resume PDF file", type="pdf")

if uploaded_file is not None:
    # Save the uploaded file to a temporary location
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        temp_pdf.write(uploaded_file.getbuffer())
        temp_pdf_path = temp_pdf.name

        # Extract text from PDF
        extracted_text = extract_text_from_pdf(temp_pdf_path)

    # Clean up temporary file
    os.remove(temp_pdf_path)

    # Display the extracted text
    st.text_area("Extracted Text", extracted_text, height=200)

    # Extract emails and phone numbers
    emails = extract_emails(extracted_text)
    phone_numbers = extract_phone_numbers(extracted_text)

    # Extract addresses using regex
    addresses = extract_addresses_with_spacy(extracted_text)
    address = addresses[0] if addresses else "Not Found"

    # Extract name from the first line using spaCy and nameparser
    name = extract_name_from_first_line(extracted_text)
    first_name, last_name = process_names(name)

    # Set default values if no data is found
    email = emails[0] if emails else "Not Found"
    phone_number = phone_numbers[0] if phone_numbers else "Not Found"
    education = "Not Found"  # Assuming education extraction logic is not yet implemented
    experience = "Not Found"  # Assuming experience extraction logic is not yet implemented

    # Display parsed data for debugging
    st.subheader("Parsed Data for Debugging")
    st.write("Extracted Text:", extracted_text)
    st.write("Emails:", emails)
    st.write("Phone Numbers:", phone_numbers)
    st.write("Addresses:", addresses)
    st.write("Name:", name)
    st.write("First Name:", first_name)
    st.write("Last Name:", last_name)

    # Display the form with pre-filled data
    st.subheader("Fill the form with extracted data")

    # Form fields with pre-filled data
    first_name_input = st.text_input("First Name", value=first_name)
    last_name_input = st.text_input("Last Name", value=last_name)
    email_input = st.text_input("Email", value=email)
    phone_number_input = st.text_input("Phone Number", value=phone_number)
    address_input = st.text_area("Address", value=address, height=100)
    education_input = st.text_area("Education", value=education, height=100)
    experience_input = st.text_area("Experience", value=experience, height=100)

    # When the user submits the form
    if st.button("Submit"):
        st.write("Form Submitted!")
        st.write("First Name:", first_name_input)
        st.write("Last Name:", last_name_input)
        st.write("Email:", email_input)
        st.write("Phone Number:", phone_number_input)
        st.write("Address:", address_input)
        st.write("Education:", education_input)
        st.write("Experience:", experience_input)
