# Streamlit Resume Upload and Form Fill

This Streamlit app allows users to upload a resume PDF, extract information, and autofill a Google Form.

## Setup

1. Clone the repository
2. Install dependencies with `pip install -r requirements.txt`
3. Run the app with `streamlit run app.py`

## Features

- Extracts text from PDF resumes
- Identifies emails, phone numbers, addresses, and names using regex and spaCy
- Summarizes text using BART transformer model
- Autofills a Google Form using Selenium
