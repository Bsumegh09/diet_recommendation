from flask import Flask, request, render_template
import fitz  # PyMuPDF for text extraction
import os
import re
import pandas as pd
import joblib  # For loading ML model
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("YOUR_API_KEY"))

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Load ML model
diet_model = joblib.load("diet_recommendation_model.pkl")

# Extract text from PDF
def extract_text_from_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        text = "\n".join([page.get_text("text") for page in doc])
        return text.strip()
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""

# Extract values using regex
def parse_lipid_profile(text):
    data = {
        "Cholesterol Total": None,
        "Triglycerides": None,
        "HDL Cholesterol": None,
        "LDL Cholesterol": None,
        "VLDL Cholesterol": None,
        "Non-HDL Cholesterol": None,
        "Age": None,
        "Gender": None
    }
    
    patterns = {
        "Cholesterol Total": [r"Cholesterol Total[:\s]+(\d+)",
                              r"Total Cholesterol[:\s]+(\d+)"
                              r"(\d+)\s*Cholesterol\s*Total",
                              r"(\d+)\s*Cholesterol\s+",
                             ],
        "Triglycerides": [r"Triglycerides[:\s]+(\d+)",
                          r"(\d+)\s*Triglycerides"],
        "HDL Cholesterol": [r"HDL Cholesterol[:\s]+(\d+)",
                            r"(\d+)\s*HDL"],
        "LDL Cholesterol": [r"LDL Cholesterol[:\s]+(\d+)",
                            r"(\d+)\s*LDL"],
        "VLDL Cholesterol": [r"VLDL Cholesterol[:\s]+(\d+)",
                             r"(\d+)\s*VLDL"],
        "Non-HDL Cholesterol": [r"Non-HDL Cholesterol[:\s]+(\d+)",
                                r"(\d+)\s*Non-HDL"],
        "Age": [r"Age[:\s]+(\d+)",r"(\d{1,3})\s*(?:Years|Yr|Yrs)?", r"Age[:\s]+(\d+)"],
        "Gender": [r"Gender[:\s]+(Male|Female)", 
                   r"(Male|Female|Other)"]
    }
    
    for key, pattern_list in patterns.items():
        for pattern in pattern_list:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                data[key] = int(value) if value.isdigit() else value
                break
    
    data["Gender"] = 1 if data["Gender"] == "Male" else 0 if data["Gender"] == "Female" else None
    return data

# Predict diet recommendation
def predict_diet(data):
    if None in data.values():
        return "Error: Missing values in input. Please verify extracted data."
    
    try:
        input_data = pd.DataFrame([[
            data["Age"], data["Gender"], data["Cholesterol Total"],
            data["LDL Cholesterol"], data["HDL Cholesterol"],
            data["Cholesterol Total"] - data["HDL Cholesterol"]
        ]], columns=["age", "sex", "total_cholesterol", "ldl", "hdl", "non_hdl"])
        
        predicted_label = diet_model.predict(input_data)[0]
        
        diet_mapping = {
            0: "Low-fat, high-fiber diet (fruits, vegetables, grains, beans, peas, lentils)",
            1: "Increase healthy fats - avocados, nuts, seeds, fatty fish, olives",
            2: "Heart-healthy Mediterranean diet - vegetables, fruits, whole grains, beans, nuts, olive oil",
            3: "Balanced diet"
        }
        
        return diet_mapping.get(predicted_label, "No recommendation available")
    except Exception as e:
        print(f"⚠️ Error in diet prediction: {e}")
        return "Error: Could not generate diet recommendation."

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return "No file uploaded."
        file = request.files['file']
        if file.filename == '':
            return "No selected file."

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        pdf_text = extract_text_from_pdf(file_path)
        extracted_data = parse_lipid_profile(pdf_text)
        print(extracted_data)
        if extracted_data:
            diet = predict_diet(extracted_data)
            return render_template('result.html',
                                   total_cholesterol=extracted_data.get("Total Cholesterol", "N/A"),
                                   ldl=extracted_data.get("LDL Cholesterol", "N/A"),
                                   hdl=extracted_data.get("HDL Cholesterol", "N/A"),
                                   text=diet,
                                   extracted_data=extracted_data)
    
    return render_template('upload.html')

if __name__ == '__main__':
    app.run(debug=True)
