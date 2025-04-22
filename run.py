import pdfplumber  # Better than PyMuPDF for structured data
import re
import json

# ---------------------- 1️⃣ EXTRACT TEXT FROM PDF ----------------------

def extract_text_from_pdf(pdf_path):
    """ Extract text from a given PDF file using pdfplumber (better for tables) """
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                extracted_text = page.extract_text()
                if extracted_text:
                    text += extracted_text + "\n"
        return text.strip()
    except Exception as e:
        print(f"❌ Error reading PDF: {e}")
        return ""

# ---------------------- 2️⃣ STRUCTURE DATA USING REGEX ----------------------

def clean_text(text):
    """ Normalize text by removing extra spaces, special characters, and newlines """
    text = text.replace("\n", " ")  # Convert newlines to spaces
    text = re.sub(r"\s{2,}", " ", text)  # Replace multiple spaces with single space
    return text.strip()

def parse_lipid_profile(text):
    """ Extract lipid profile values from raw text using multiple regex patterns """
    lipid_profile = {
        "Cholesterol Total": None,
        "Triglycerides": None,
        "HDL Cholesterol": None,
        "LDL Cholesterol": None,
        "VLDL Cholesterol": None,
        "Non-HDL Cholesterol": None
    }

    # Define regex patterns for each lipid component
    patterns = {
        "Cholesterol Total": [
            r"Cholesterol\s*Total.*?([\d.]+)",  
            r"Cholesterol Total[:\s]+(\d+)", 
            r"Total Cholesterol[:\s]+(\d+)", 
            r"(\d+)\s*Cholesterol\s*Total",  
            r"(\d+)\s*Cholesterol\s+"  
        ],
        "Triglycerides": [r"Triglycerides.*?([\d.]+)"],
        "HDL Cholesterol": [r"HDL\s*Cholesterol.*?([\d.]+)"],
        "LDL Cholesterol": [r"LDL\s*Cholesterol.*?([\d.]+)"],
        "VLDL Cholesterol": [r"VLDL\s*Cholesterol.*?([\d.]+)"],
        "Non-HDL Cholesterol": [r"Non-HDL\s*Cholesterol.*?([\d.]+)"]
    }

    text = clean_text(text)  # Normalize extracted text

    for key, pattern_list in patterns.items():
        for pattern in pattern_list:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                if value.replace(".", "").isdigit():  # Ensure valid number
                    lipid_profile[key] = float(value)  # Convert to float
                    break  # Stop checking once we find a valid match
                else:
                    print(f"⚠️ Warning: Skipping invalid value '{value}' for {key}")

    return lipid_profile

# ---------------------- 3️⃣ FINAL EXECUTION ----------------------

def extract_lipid_profile_from_pdf(pdf_path):
    """ Extract lipid profile data from a PDF file """
    text = extract_text_from_pdf(pdf_path)
    
    if not text:
        return json.dumps({"error": "No text extracted from PDF"}, indent=4)

    print(f"📄 Extracted Text: \n{text[:500]}...\n")  # Debug: Print first 500 chars

    structured_data = parse_lipid_profile(text)

    # Convert to JSON format
    json_output = json.dumps(structured_data, indent=4)
    
    return json_output

# ---------------------- RUN SCRIPT ----------------------

if __name__ == "__main__":
    pdf_path = r"D:\sem 8 project\lipid.pdf"  # Ensure raw string or use double backslashes
    result = extract_lipid_profile_from_pdf(pdf_path)
    print(result)
