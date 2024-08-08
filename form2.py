import streamlit as st
import fitz  # PyMuPDF
import re
import tempfile
import os
import spacy
from spacy.cli import download
from transformers.models.bart import BartTokenizer, BartForConditionalGeneration
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

# Load spaCy model
@st.cache_resource
def load_spacy_model(model_name="en_core_web_lg"):
    # Check if the model is already installed
    if not spacy.util.is_package(model_name):
        print(f"Model '{model_name}' not found. Downloading...")
        download(model_name)

    # Load the model
    nlp = spacy.load(model_name)
    return nlp

nlp = load_spacy_model()

# Load pre-trained BART model and tokenizer
tokenizer = BartTokenizer.from_pretrained('facebook/bart-large-cnn')
model = BartForConditionalGeneration.from_pretrained('facebook/bart-large-cnn')


def fill_form(driver, data):
    field_mappings = {
        'Name1': ['First Name', 'first name', 'fname', 'Fname', 'Name', 'NAME', 'name'],
        'Name2': ['Last Name', 'last name', 'lname', 'Lname', 'Family Name', 'Family name'],
        'email': ['email', 'e-mail', 'mail', 'Email', 'EMAIL'],
        'address': ['address', 'location', 'ADDRESS', 'Address'],
        'mobile': ['phone', 'telephone', 'contact', 'Mobile', 'Phone', 'Phone number', 'Mobile number']
    }
    my_form = dict(zip(field_mappings.keys(), data))

    for field, data in my_form.items():
        # Try each possible field name until we find a match
        for possible_name in field_mappings[field]:
            try:
                text_input = driver.find_element(by='xpath',
                                                 value=f'//div[contains(@data-params, "{possible_name}")]//textarea | '
                                                       f'//div[contains(@data-params, "{possible_name}")]//input')
                text_input.send_keys(data)
                break  # Exit loop if the field is found
            except:
                continue  # Try next possible name


# Function to get ChromeDriver with Brave Browser
def get_chrome_driver():
    options = Options()
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver


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


# Function to summarize text using BART
@st.cache_resource
def summarize_text(text):
    text = text.replace('\n', ' ')
    inputs = tokenizer.encode("summarize: " + text, return_tensors="pt", max_length=1024, truncation=True)
    summary_ids = model.generate(inputs, max_length=150, min_length=30, length_penalty=2.0, num_beams=4, early_stopping=True)
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    return summary


# Function to extract person names using spaCy
@st.cache_resource
def extract_person_from_text(text):
    doc = nlp(text)
    labels_dict = {}
    for ent in doc.ents:
        if ent.label_ not in labels_dict:
            labels_dict[ent.label_] = []
        labels_dict[ent.label_].append(ent.text)
    person_name = labels_dict.get('PERSON', [None])[0]
    return person_name


# Function to extract addresses with spaCy
@st.cache_resource
def extract_addresses_with_spacy(text):
    cleaned_text = text.replace('\n', '')
    address_entities = []
    doc = nlp(cleaned_text)
    fac_found = False
    for ent in doc.ents:
        if ent.label_ == "FAC":
            address_entities.append(ent.text)
            fac_found = True
        elif fac_found and ent.label_ in ["ADDRESS", "GPE", "LOC"]:
            address_entities.append(ent.text)
            if len(address_entities) == 3:
                break

    # If no FAC entity was found, collect the first two ADDRESS, GPE, or LOC entities
    if not fac_found:
        address_entities = []
        for ent in doc.ents:
            if ent.label_ in ["ADDRESS", "GPE", "LOC"]:
                address_entities.append(ent.text)
                if len(address_entities) == 2:
                    break
    address = ' '.join(address_entities)
    return address


# Function to process extracted names into first and last names
def split_name(text):
    if text:
        name_parts = text.split()
        if len(name_parts) == 1:
            first_name = name_parts[0]
            last_name = ''
        elif len(name_parts) == 2:
            first_name, last_name = name_parts
        else:
            first_name = name_parts[0]
            last_name = name_parts[-1]
        return first_name, last_name
    return None, None


# Streamlit app
def main():
    st.title("Resume Upload and Form Fill")

    uploaded_file = st.file_uploader("Choose a resume PDF file", type="pdf")

    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_pdf.write(uploaded_file.getbuffer())
            temp_pdf_path = temp_pdf.name

            extracted_text = extract_text_from_pdf(temp_pdf_path)

        os.remove(temp_pdf_path)

        st.text_area("Extracted Text", extracted_text, height=200)

        emails = extract_emails(extracted_text)
        phone_numbers = extract_phone_numbers(extracted_text)
        address = extract_addresses_with_spacy(extracted_text)
        name = extract_person_from_text(summarize_text(extracted_text))
        first_name, last_name = split_name(name)

        email = emails[0] if emails else "Not Found"
        phone_number = phone_numbers[0] if phone_numbers else "Not Found"

        st.subheader("Parsed Data for Debugging")
        st.write("Emails:", emails)
        st.write("Phone Numbers:", phone_numbers)
        st.write("Addresses:", address)
        st.write("Name:", name)
        st.write("First Name:", first_name)
        st.write("Last Name:", last_name)

        st.subheader("Google Form Autofill App")

        form_url = st.text_input('Form URL')

        if st.button('Fill Form', key='fill_form_button'):
            if not form_url:
                st.error("Please enter the form URL")
            else:
                if 'driver' not in st.session_state:
                    st.session_state.driver = get_chrome_driver()

                driver = st.session_state.driver

                try:
                    driver.get(form_url)
                    time.sleep(3)
                    data = []
                    data.extend([first_name, last_name, email, address, phone_number])

                    fill_form(driver, data)
                    time.sleep(1)

                    with st.sidebar:
                        st.subheader("Form Submission")
                        st.write("Would you like to submit the form or leave the browser open?")

                        submit_form = st.button("Submit Form", key='submit_form')
                        leave_open = st.button("Leave Browser Open", key='leave_button')

                    if submit_form:
                        try:
                            submit_button = WebDriverWait(driver, 10).until(
                                EC.element_to_be_clickable((By.XPATH, '//div[@role="button"]//span[text()="Submit"]'))
                            )
                            submit_button.click()
                            st.write("Form has been submitted.")
                        except Exception as e:
                            st.error(f"An error occurred while submitting the form: {e}")
                        finally:
                            driver.quit()
                    elif leave_open:
                        st.write("The browser window is left open. Please submit the form manually.")

                except Exception as e:
                  st.error(f"An error occurred: {e}")
                  driver.quit()


        #time.sleep(15)
        #driver.quit()

if __name__ == "__main__":
    main()
