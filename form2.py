import streamlit as st
import pdf2image
import pytesseract
import re
import tempfile
import os
import nltk
from nameparser import HumanName
import spacy

poppler_path = "D:/pythonProject1/Release-24.07.0-0/poppler-24.07.0/Library/bin"

pytesseract.pytesseract.tesseract_cmd = r"C:/Program Files/Tesseract-OCR/tesseract.exe"

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Function to convert PDF to images
def convert_pdf_to_images(pdf_path):
    images = pdf2image.convert_from_path(pdf_path, poppler_path=poppler_path)
    return images

# Function to perform OCR on images
def ocr_on_image(image):
    text = pytesseract.image_to_string(image)
    return text

# Function to extract emails using regex
def extract_emails(text):
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.findall(email_pattern, text)

# Function to extract phone numbers using regex
def extract_phone_numbers(text):
    phone_pattern = r'\+?\d[\d -]{8,}\d'
    return re.findall(phone_pattern, text)

# Function to extract addresses using spaCy NER and regex
def extract_addresses(text):
    # A more flexible regex pattern to capture addresses
    address_pattern = r'(\d{1,5}[A-Za-z\s,.-]+(?:\s[A-Za-z\s,.-]+)*[A-Za-z\s,.-]*,\s*[A-Za-z\s]+(?:\s[A-Za-z\s]+)*,\s*[A-Za-z\s]+(?:\s[A-Za-z\s]+)*,\s*\d{6})'

    addresses = re.findall(address_pattern, text)
    cleaned_addresses = [addr.strip() for addr in addresses]

    return cleaned_addresses

# Function to extract names using nameparser
def extract_names(text):
    first_line = text.strip().split("\n")[0]
    name = HumanName(first_line)
    if name.first or name.last:
        return name
    else:
        return None

# Function to process extracted names into first and last names
def process_names(name):
    if name:
        name_parts = name.full_name.split()
        if len(name_parts) == 2:
            first_name = name_parts[0]
            last_name = name_parts[1]
        elif len(name_parts) > 2:
            first_name = " ".join(name_parts[:-1])
            last_name = name_parts[-1]
            if len(last_name) == 1:  # Check if last name is a single alphabet
                last_name = name_parts[-2] + " " + last_name  # Combine it with the previous name part
                first_name = " ".join(name_parts[:-2])
        else:
            first_name = name_parts[0]
            last_name = ""
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

    # Convert PDF to images
    images = convert_pdf_to_images(temp_pdf_path)

    # Perform OCR on all images and combine the text
    extracted_text = ""
    for image in images:
        extracted_text += ocr_on_image(image) + "\n"

    # Display the extracted text
    st.text_area("Extracted Text", extracted_text, height=200)

    # Extract emails and phone numbers
    emails = extract_emails(extracted_text)
    phone_numbers = extract_phone_numbers(extracted_text)

    # Extract addresses using spaCy NER and regex
    addresses = extract_addresses(extracted_text)
    address = addresses[0] if addresses else "Not Found"

    # Extract names using nameparser
    name = extract_names(extracted_text)
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

    # Clean up temporary file
    os.remove(temp_pdf_path)
