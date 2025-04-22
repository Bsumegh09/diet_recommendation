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
def extract_values(text):
    data = {}
    patterns = {
       
    "Total Cholesterol": [
                              r"(\d+\.\d+)\s*Cholesterol\s*Total",
                              r"Cholesterol Total[:\s]+(\d+\.\d+)"
                              r"Cholesterol Total[:\s]+(\d+)",
                              r"Total Cholesterol[:\s]+(\d+)",
                              r"(\d+)\s*Cholesterol\s*Total",
                              r"(\d+)\s*Cholesterol\s+",
                              r"Cholesterol Total[:\s]+(\d+)",
                              r"Total Cholesterol[:\s]+(\d+)",
                              r"Cholesterol [\s]+(\d+\,\d)Total"],
    
    "Triglycerides": [        r"(\d+\.\d+)\s*Triglycerides",
                              r"Triglycerides[:\s]+(\d+\.\d+)",
                              r"Triglycerides[:\s]+(\d+)",
                              r"(\d+)\s*Triglycerides"],
    "HDL Cholesterol": [      r"(\d+\.\d+)\s*HDL Cholesterol", 
                              r"HDL Cholesterol[:\s]+(\d+\.\d+)",
                              r"HDL Cholesterol[:\s]+(\d+)",
                              r"(\d+\.\d+)\s*HDL Cholesterol,Calculated",
                              r"(\d+)\s*HDL"],
    "LDL Cholesterol": [      r"(\d+\.\d+)\s*LDL Cholesterol", 
                              r"LDL Cholesterol[:\s]+(\d+\.\d+)",
                              r"LDL Cholesterol[:\s]+(\d+)",
                              r"(\d+\.\d+)\s*LDL Cholesterol,Calculated",
                              r"(\d+)\s*LDL"
                        ],
    "Age": [r"(\d{1,3})\s*Years", r"Age[:\s]+(\d{1,3})"],
    "Gender": [r"Gender[:\s]+(Male|Female)", r"(Male|Female|Other)"]


    }

    for key, pattern_list in patterns.items():
        for pattern in pattern_list:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data[key] = int(match.group(1)) if match.group(1).isdigit() else match.group(1)
                break
        else:
            data[key] = None

    data["Gender"] = 1 if data.get("Gender", "").lower() == "male" else 0 if data.get("Gender", "").lower() == "female" else None
    return data

# Predict diet recommendation
def predict_diet(data, systolic_bp, diastolic_bp, smoking, diabetes, heart_attack):
    if None in data.values():
        return "Error: Missing values in input. Please verify extracted data."
    
    try:
        
        input_data = pd.DataFrame([[data["Age"], data["Gender"], data["Total Cholesterol"],
                                    data["LDL Cholesterol"], data["HDL Cholesterol"],
                                    float(data["Total Cholesterol"] - data["HDL Cholesterol"]),
                                    systolic_bp, diastolic_bp, smoking, diabetes, heart_attack]],
                                  columns=["age", "sex", "total_cholesterol", "ldl", "hdl", 
                                           "non_hdl", "systolic_bp", "diastolic_bp", "smoking", 
                                           "diabetes", "heart_attack"])
        
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
        return "Eat Healthy Food"

# Generate meal plan using Gemini API
def get_meal_plan(name, age, gender, extracted_data):
    prompt = f"""
    Generate a 7-day Heart-Healthy & Diabetes-Friendly Meal Plan & Exercise for:
    - Name: {name}
    - Age: {age}
    - Gender: {'Male' if gender == 1 else 'Female'}
    - Total Cholesterol: {extracted_data.get('Total Cholesterol', 'Unknown')} mg/dL
    - LDL Cholesterol: {extracted_data.get('LDL Cholesterol', 'Unknown')} mg/dL
    - HDL Cholesterol: {extracted_data.get('HDL Cholesterol', 'Unknown')} mg/dL
    - Triglycerides: {extracted_data.get('Triglycerides', 'Unknown')} mg/dL
    """
    try:
        model = genai.GenerativeModel("gemini-1.5-pro-latest")
        response = model.generate_content(prompt)
        meal_plan = response.text.strip() if response and hasattr(response, 'text') else "Error: Meal plan generation failed."
        return re.sub(r'[*#]', '', meal_plan)  # Remove * and # from output
    except Exception as e:
        print(f"⚠️ Error fetching meal plan: {e}")
        return "Error: Could not generate meal plan."

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

        try:
            systolic_bp = int(request.form['sysBP'])
            diastolic_bp = int(request.form['diaBP'])
            smoking = int(request.form['smoker'])
            diabetes = int(request.form['diabetic'])
            heart_attack = int(request.form['heart_attack'])
            name = request.form['name']
        except ValueError:
            return "Error: Invalid input. Please enter numbers only."

        pdf_text = extract_text_from_pdf(file_path)
        extracted_data = extract_values(pdf_text)
        print(extracted_data)
        if extracted_data:
            diet = predict_diet(extracted_data, systolic_bp, diastolic_bp, smoking, diabetes, heart_attack)
            print(diet)
            meal_plan = get_meal_plan(name, extracted_data.get("Age", "Unknown"), extracted_data.get("Gender", "Unknown"), extracted_data)
            return render_template('result.html',
                       text=diet,
                       total_cholesterol=float(extracted_data.get("Total Cholesterol", 0)),
                       ldl=float(extracted_data.get("LDL Cholesterol", 0)),
                       hdl=float(extracted_data.get("HDL Cholesterol", 0)), 
                       meal_plan=meal_plan)

    
    return render_template('upload.html')
   
if __name__ == '__main__':
    app.run(debug=True)
