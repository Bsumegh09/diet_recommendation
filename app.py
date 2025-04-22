from flask import Flask, request, render_template
import fitz  # PyMuPDF
import os
import re
import pandas as pd
import joblib  # For loading ML model

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

'''def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text'''

model = joblib.load("diet_recommendation_model.pkl")

def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file."""
    try:
        doc = fitz.open(pdf_path)
        text = "\n".join([page.get_text("text") for page in doc])
        return text.strip()
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""

def extract_values(text):
    """Extracts required values using multiple regex patterns."""
    data = {}

    # Define multiple patterns for each key
    patterns = {
        "Name": [
            r"Mr\.?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"Name[:\s]+(?:Mr\.|Mrs\.|Ms\.|Dr\.)?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
        ],
        "Age": [
            r"(\d{1,3})\s*(?:Years|Yr|Yrs)?",
            r"Age[:\s]+(\d+)"
        ],
        "Gender": [
            r"(Male|Female|Other)",
            r"Gender[:\s]+(Male|Female)"
        ],
        "Total Cholesterol": [
            r"Total Cholesterol[:\s]+(\d+)",
            r"(\d+)\s*Cholesterol\s*Total",
            r"(\d+)\s*Cholesterol\s+"

        ],
        "Triglycerides": [
            r"Triglycerides[:\s]+(\d+)",
            r"(\d+)\s*Triglycerides"
        ],
        "HDL Cholesterol": [
            r"HDL Cholesterol[:\s]+(\d+)",
            r"(\d+)\s*HDL\s*Cholesterol"
        ],
        "LDL Cholesterol": [
            r"LDL Cholesterol[:\s]+(\d+)",
            r"(\d+)\s*LDL\s*Cholesterol"
        ]
    }
    
    # Try each pattern in order until a match is found
    for key, pattern_list in patterns.items():
        for pattern in pattern_list:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                data[key] = int(value) if value.isdigit() else value
                break  # Stop trying once a match is found
        else:
            data[key] = None  # No match found

    # Convert Gender to numeric format
    data["Gender"] = 1 if data.get("Gender") == "Male" else 0 if data.get("Gender") == "Female" else None
    
    return data

def get_user_inputs():
    """Ask user for missing inputs like BP, smoking, diabetes."""
    try:
        systolic_bp = int(input("Enter Systolic Blood Pressure: "))
        diastolic_bp = int(input("Enter Diastolic Blood Pressure: "))
        smoking = int(input("Are you a smoker? (1: Yes, 0: No): "))
        diabetes = int(input("Do you have diabetes? (1: Yes, 0: No): "))
        heart_attack = int(input("Have you had a heart attack? (1: Yes, 0: No): "))

        return systolic_bp, diastolic_bp, smoking, diabetes, heart_attack
    except ValueError:
        print("Invalid input! Please enter numbers only.")
        return None, None, None, None, None

def predict_diet(data, systolic_bp, diastolic_bp, smoking, diabetes, heart_attack):
    """Uses the trained ML model to predict the diet recommendation."""
    if None in data.values():
        print("Missing data! Please check PDF extraction.")
        return None

    # Get additional user inputs
    # systolic_bp, diastolic_bp, smoking, diabetes, heart_attack = get_user_inputs()
    
    if None in [systolic_bp, diastolic_bp, smoking, diabetes, heart_attack]:
        print("Error in user inputs. Exiting.")
        return None

    # Prepare final data for model prediction
    input_data = pd.DataFrame([[
        data["Age"], data["Gender"], data["Total Cholesterol"],
        data["LDL Cholesterol"], data["HDL Cholesterol"],
        data["Total Cholesterol"] - data["HDL Cholesterol"],  # Non-HDL Cholesterol
        systolic_bp, diastolic_bp, smoking, diabetes, heart_attack
    ]], columns=["age", "sex", "total_cholesterol", "ldl", "hdl", "non_hdl", 
                 "systolic_bp", "diastolic_bp", "smoking", "diabetes", "heart_attack"])
    
    # Predict diet
    predicted_label = model.predict(input_data)[0]
    
    # Mapping diet labels to recommendations
    diet_mapping = {
        0: "\n Low-fat, high-fiber diet - \n fruits,\n vegetables, \n grains, \n beans, \n peas,\n  lentils",
        1: "\n Increase healthy fats - \n avocados,\n nuts,\n seeds,\n fatty fish,\n olives",
        2: "\nHeart-healthy Mediterranean diet\n Vegetables \n Fruits. \n Whole grains.\nBeans. Nuts seeds \n Olive oil\nSeasoning with herbs and spices. ",
        3: "\nBalanced diet"
    }
    diet_recommendation = diet_mapping.get(predicted_label, "No recommendation available")
    print("\n🔹 **Diet Recommendation:**", diet_recommendation)
    # Print recommendation
    return diet_recommendation



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
        systolic_bp = request.form['sysBP']
        diastolic_bp = request.form['diaBP']
        smoking = request.form['smoker']
        diabetes = request.form['diabetic']
        heart_attack = request.form['heart_attack']
        pdf_text = extract_text_from_pdf(file_path)
        extracted_data = extract_values(pdf_text)

        if extracted_data:
            print("\n📌 The Recommendation is :")
            for key, value in extracted_data.items():
                print(f"{key}: {value}")
            
            diet = predict_diet(extracted_data, systolic_bp, diastolic_bp, smoking, diabetes, heart_attack)
            total_cholesterol = extracted_data.get("Total Cholesterol", "N/A")
            ldl = extracted_data.get("LDL Cholesterol", "N/A") 
            hdl = extracted_data.get("HDL Cholesterol", "N/A")

            return render_template('result.html', text=diet, total_cholesterol=total_cholesterol, ldl=ldl, hdl=hdl)
    
    return render_template('upload.html')

if __name__ == '__main__':
    app.run(debug=True)


# from flask import Flask, request, render_template
# import fitz  # PyMuPDF for PDF reading
# import os
# import re
# import pandas as pd
# import joblib  # For loading the trained ML model

# # Initialize Flask app
# app = Flask(__name__)
# app.config['UPLOAD_FOLDER'] = 'uploads'
# os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# # Load the trained ML model
# model = joblib.load("diet_recommendation_model.pkl")

# def extract_text_from_pdf(pdf_path):
#     """Extracts text from a PDF file."""
#     try:
#         doc = fitz.open(pdf_path)
#         text = "\n".join([page.get_text("text") for page in doc])
#         return text.strip()
#     except Exception as e:
#         print(f"Error reading PDF: {e}")
#         return ""

# def extract_values(text):
#     """Extracts required values using regex patterns."""
#     data = {}

#     patterns = {
#         "Name": [
#             r"Mr\.?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
#             r"Name[:\s]+(?:Mr\.|Mrs\.|Ms\.|Dr\.)?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
#         ],
#         "Age": [
#             r"(\d{1,3})\s*(?:Years|Yr|Yrs)?",
#             r"Age[:\s]+(\d+)"
#         ],
#         "Gender": [
#             r"(Male|Female|Other)",
#             r"Gender[:\s]+(Male|Female)"
#         ],
#         "Total Cholesterol": [
#             r"Total Cholesterol[:\s]+(\d+)",
#             r"(\d+)\s*Cholesterol\s*Total"
#         ],
#         "Triglycerides": [
#             r"Triglycerides[:\s]+(\d+)"
#         ],
#         "HDL Cholesterol": [
#             r"HDL Cholesterol[:\s]+(\d+)",
#             r"(\d+)\s*HDL\s*Cholesterol"
#         ],
#         "LDL Cholesterol": [
#             r"LDL Cholesterol[:\s]+(\d+)",
#             r"(\d+)\s*LDL\s*Cholesterol"
#         ]
#     }
    
#     for key, pattern_list in patterns.items():
#         for pattern in pattern_list:
#             match = re.search(pattern, text, re.IGNORECASE)
#             if match:
#                 value = match.group(1).strip()
#                 data[key] = int(value) if value.isdigit() else value
#                 break  # Stop once a match is found
#         else:
#             data[key] = None  # No match found

#     # Convert Gender to numeric format
#     data["Gender"] = 1 if data.get("Gender") == "Male" else 0 if data.get("Gender") == "Female" else None
    
#     return data

# def predict_diet(data, systolic_bp, diastolic_bp, smoking, diabetes, heart_attack):
#     """Uses the trained ML model to predict the diet recommendation."""
#     if None in data.values():
#         print("Missing data! Please check PDF extraction.")
#         return None

#     if None in [systolic_bp, diastolic_bp, smoking, diabetes, heart_attack]:
#         print("Error in user inputs. Exiting.")
#         return None

#     # Prepare input data for the model
#     input_data = pd.DataFrame([[
#         data["Age"], data["Gender"], data["Total Cholesterol"],
#         data["LDL Cholesterol"], data["HDL Cholesterol"],
#         data["Total Cholesterol"] - data["HDL Cholesterol"],  # Non-HDL Cholesterol
#         systolic_bp, diastolic_bp, smoking, diabetes, heart_attack
#     ]], columns=["age", "sex", "total_cholesterol", "ldl", "hdl", "non_hdl", 
#                  "systolic_bp", "diastolic_bp", "smoking", "diabetes", "heart_attack"])
    
#     # Predict diet
#     predicted_label = model.predict(input_data)[0]
    
#     diet_mapping = {
#         0: "Low-fat, high-fiber diet: Fruits, vegetables, grains, beans, peas, lentils.",
#         1: "Increase healthy fats: Avocados, nuts, seeds, fatty fish, olives.",
#         2: "Heart-healthy Mediterranean diet: Vegetables, fruits, whole grains, beans, nuts, seeds, olive oil.",
#         3: "Balanced diet."
#     }
#     return diet_mapping.get(predicted_label, "No recommendation available")

# @app.route('/', methods=['GET', 'POST'])
# def upload_file():
#     if request.method == 'POST':
#         if 'file' not in request.files:
#             return "No file uploaded."
#         file = request.files['file']
#         if file.filename == '':
#             return "No selected file."
        
#         file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
#         file.save(file_path)
        
#         # Get additional user inputs
#         systolic_bp = int(request.form['sysBP'])
#         diastolic_bp = int(request.form['diaBP'])
#         smoking = int(request.form['smoker'])
#         diabetes = int(request.form['diabetic'])
#         heart_attack = int(request.form['heart_attack'])

#         # Extract text from PDF and extract values
#         pdf_text = extract_text_from_pdf(file_path)
#         extracted_data = extract_values(pdf_text)

#         if extracted_data:
#             diet = predict_diet(extracted_data, systolic_bp, diastolic_bp, smoking, diabetes, heart_attack)

#             # Extract specific values safely
#             total_cholesterol = extracted_data.get("Total Cholesterol", "N/A")
#             ldl = extracted_data.get("LDL Cholesterol", "N/A")
#             hdl = extracted_data.get("HDL Cholesterol", "N/A")

#             return render_template('result.html', text=diet, total_cholesterol=total_cholesterol, ldl=ldl, hdl=hdl)
    
#     return render_template('upload.html')

# if __name__ == '__main__':
#     app.run(debug=True)
