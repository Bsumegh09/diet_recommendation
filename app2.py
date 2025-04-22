# from flask import Flask, request, render_template
# import fitz  # PyMuPDF for text extraction
# import os
# import re
# import pandas as pd
# import joblib  # For loading ML model
# import google.generativeai as genai
# from dotenv import load_dotenv

# # Load environment variables
# load_dotenv()
# genai.configure(api_key=os.getenv("AIzaSyDDBrdOrNh4ODNOsyIIEsSOYkQuzHJODnc"))

# app = Flask(__name__)
# app.config['UPLOAD_FOLDER'] = 'uploads'
# os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# # Load ML model
# diet_model = joblib.load("diet_recommendation_model.pkl")

# # Extract text from PDF
# def extract_text_from_pdf(pdf_path):
#     try:
#         doc = fitz.open(pdf_path)
#         text = "\n".join([page.get_text("text") for page in doc])
#         return text.strip()
#     except Exception as e:
#         print(f"Error reading PDF: {e}")
#         return ""
# available_models = genai.list_models()
# for model in available_models:
#     print(model.name)
# # Extract values using regex
# def extract_values(text):
#     data = {}
#     patterns = {
        # "Total Cholesterol": [r"Cholesterol Total[:\s]+(\d+)",
        #                       r"Total Cholesterol[:\s]+(\d+)",
        #                       r"Cholesterol Total[\s]+(\d+)",
        #                       r"(\d+)\s*Cholesterol\s+",
        #                       r"(\d+)\s*Cholesterol\s*Total"],
        # "Triglycerides": [r"Triglycerides[:\s]+(\d+)",
        #                   r"(\d+)\s*Triglycerides"],
        # "HDL Cholesterol": [r"HDL Cholesterol[:\s]+(\d+)",
        #                      r"(\d+)\s*HDL"],
#         "LDL Cholesterol": [r"LDL Cholesterol[:\s]+(\d+)",
#                              r"(\d+)\s*LDL"],
#         "Age": [r"Age[:\s]+(\d+)" 
#                  r"(\d{1,3})\s*(?:Years|Yr|Yrs)?",
#                  r"Age[:\s]+(\d+)"] ,
#         "Gender": [r"Gender[:\s]+(Male|Female)",
#                    r"Gender[:\s]+(Male|Female)" ,
#                    r"(Male|Female|Other)"]
#     }

#     for key, pattern_list in patterns.items():
#         for pattern in pattern_list:
#             match = re.search(pattern, text, re.IGNORECASE)
#             if match:
#                 value = match.group(1).strip()
#                 data[key] = int(value) if value.isdigit() else value
#                 break
#         else:
#             data[key] = None
#     data["Gender"] = 1 if data.get("Gender") == "Male" else 0 if data.get("Gender") == "Female" else None
#     return data

# # Predict diet recommendation
# def predict_diet(data, systolic_bp, diastolic_bp, smoking, diabetes, heart_attack):
#     if None in data.values():
#         print("❌ Missing data! Check PDF extraction:", data)
#         return "Error: Missing values in input. Please verify extracted data."
#     try:
#         input_data = pd.DataFrame([[
#             data["Age"], data["Gender"], data["Total Cholesterol"],
#             data["LDL Cholesterol"], data["HDL Cholesterol"],
#             data["Total Cholesterol"] - data["HDL Cholesterol"],
#             systolic_bp, diastolic_bp, smoking, diabetes, heart_attack
#         ]], columns=["age", "sex", "total_cholesterol", "ldl", "hdl", "non_hdl",
#                      "systolic_bp", "diastolic_bp", "smoking", "diabetes", "heart_attack"])
        
#         print("📌 Input Data for Prediction:", input_data)
#         predicted_label = diet_model.predict(input_data)[0]
#         print("✅ Predicted Label:", predicted_label)

#         diet_mapping = {
#             0: "Low-fat, high-fiber diet - fruits, vegetables, grains, beans, peas, lentils",
#             1: "Increase healthy fats - avocados, nuts, seeds, fatty fish, olives",
#             2: "Heart-healthy Mediterranean diet - vegetables, fruits, whole grains, beans, nuts, olive oil",
#             3: "Balanced diet"
#         }
        
#         return diet_mapping.get(predicted_label, "No recommendation available")
#     except Exception as e:
#         print(f"⚠️ Error in diet prediction: {e}")
#         return "Error: Could not generate diet recommendation."

# # Generate meal plan using Gemini API
# def get_meal_plan(extracted_data):
#     prompt = f"""
#     Generate a 7-day Heart-Healthy & Diabetes-Friendly Meal Plan based on the following lipid profile:
    
#     - Age: {extracted_data.get('Age', 'Unknown')}
#     - Gender: {'Male' if extracted_data.get('Gender') == 1 else 'Female'}
#     - Total Cholesterol: {extracted_data.get('Total Cholesterol', 'Unknown')} mg/dL
#     - LDL Cholesterol: {extracted_data.get('LDL Cholesterol', 'Unknown')} mg/dL
#     - HDL Cholesterol: {extracted_data.get('HDL Cholesterol', 'Unknown')} mg/dL
#     - Triglycerides: {extracted_data.get('Triglycerides', 'Unknown')} mg/dL
    
#     Provide a structured plan including breakfast, lunch, dinner, snacks, and a 6-day workout plan.
#     """
#     try:
#         print("📡 Sending Request to Gemini API...")

#         # ✅ Use a valid model
#         model = genai.GenerativeModel("gemini-1.5-pro-latest")
#         response = model.generate_content(prompt)

#         if not response or not hasattr(response, 'text'):
#             print("❌ Gemini API returned an empty response.")
#             return "Error: Meal plan generation failed."

#         print("✅ Gemini API Response Received.")
#         return response.text.strip()
#     except Exception as e:
#         print(f"⚠️ Error fetching meal plan from Gemini API: {e}")
#         return "Error: Could not generate meal plan."


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
        
#         try:
#             systolic_bp = int(request.form['sysBP'])
#             diastolic_bp = int(request.form['diaBP'])
#             smoking = int(request.form['smoker'])
#             diabetes = int(request.form['diabetic'])
#             heart_attack = int(request.form['heart_attack'])
#         except ValueError:
#             return "Error: Invalid input. Please enter numbers only."

#         pdf_text = extract_text_from_pdf(file_path)
#         extracted_data = extract_values(pdf_text)
#         print("📄 Extracted Data from PDF:", extracted_data)
        
#         if extracted_data:
#             diet = predict_diet(extracted_data, systolic_bp, diastolic_bp, smoking, diabetes, heart_attack)
#             meal_plan = get_meal_plan(extracted_data)
            
#             return render_template(
#                 'result.html', 
#                 text=diet, 
#                 total_cholesterol=extracted_data.get("Total Cholesterol", "N/A"),
#                 ldl=extracted_data.get("LDL Cholesterol", "N/A"),
#                 hdl=extracted_data.get("HDL Cholesterol", "N/A"),
#                 meal_plan=meal_plan
#             )
    
#     return render_template('upload.html')

# if __name__ == '__main__':
#     app.run(debug=True)
# from flask import Flask, request, render_template
# import fitz  # PyMuPDF for text extraction
# import os
# import re
# import pandas as pd
# import joblib  # For loading ML model
# import google.generativeai as genai
# from dotenv import load_dotenv

# # Load environment variables
# load_dotenv()
# genai.configure(api_key=os.getenv("YOUR_GEMINI_API_KEY"))

# app = Flask(__name__)
# app.config['UPLOAD_FOLDER'] = 'uploads'
# os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# # Load ML model
# diet_model = joblib.load("diet_recommendation_model.pkl")

# # Extract text from PDF
# def extract_text_from_pdf(pdf_path):
#     try:
#         doc = fitz.open(pdf_path)
#         text = "\n".join([page.get_text("text") for page in doc])
#         return text.strip()
#     except Exception as e:
#         print(f"Error reading PDF: {e}")
#         return ""

# # Extract values using regex
# def extract_values(text):
#     data = {}
#     patterns = {
#         "Total Cholesterol": [r"Cholesterol Total[:\s]+(\d+)",
#                               r"Total Cholesterol[:\s]+(\d+)",
#                               r"Total Cholesterol[:\s]+(\d+)",
#             r"(\d+)\s*Cholesterol\s*Total",
#             r"(\d+)\s*Cholesterol\s+"],
#         "Triglycerides": [r"Triglycerides[:\s]+(\d+)", r"(\d+)\s*Triglycerides"],
#         "HDL Cholesterol": [r"HDL Cholesterol[:\s]+(\d+)", r"(\d+)\s*HDL"],
#         "LDL Cholesterol": [r"LDL Cholesterol[:\s]+(\d+)", r"(\d+)\s*LDL"],
#         "Age": [r"(\d{1,3})\s*(?:Years|Yr|Yrs)?",
#             r"Age[:\s]+(\d+)"
#                 ],
#         "Gender": [r"Gender[:\s]+(Male|Female)", r"(Male|Female|Other)"],
#     }

#     for key, pattern_list in patterns.items():
#         for pattern in pattern_list:
#             match = re.search(pattern, text, re.IGNORECASE)
#             if match:
#                 data[key] = int(match.group(1)) if match.group(1).isdigit() else match.group(1)
#                 break
#         else:
#             data[key] = None

#     # Convert Gender: Male -> 1, Female -> 0
#     data["Gender"] = 1 if data.get("Gender", "").lower() == "male" else 0 if data.get("Gender", "").lower() == "female" else None
    
#     return data

# # Predict diet recommendation
# def predict_diet(data, systolic_bp, diastolic_bp, smoking, diabetes, heart_attack):
#     if None in data.values():
#         return "Error: Missing values in input. Please verify extracted data."
    
#     try:
#         input_data = pd.DataFrame([[data["Age"], data["Gender"], data["Total Cholesterol"],
#                                     data["LDL Cholesterol"], data["HDL Cholesterol"],
#                                     data["Total Cholesterol"] - data["HDL Cholesterol"],
#                                     systolic_bp, diastolic_bp, smoking, diabetes, heart_attack]],
#                                   columns=["age", "sex", "total_cholesterol", "ldl", "hdl", 
#                                            "non_hdl", "systolic_bp", "diastolic_bp", "smoking", 
#                                            "diabetes", "heart_attack"])
        
#         print("📌 Input Data for Prediction:", input_data)
#         predicted_label = diet_model.predict(input_data)[0]

#         diet_mapping = {
#             0: "Low-fat, high-fiber diet (fruits, vegetables, grains, beans, peas, lentils)",
#             1: "Increase healthy fats - avocados, nuts, seeds, fatty fish, olives",
#             2: "Heart-healthy Mediterranean diet - vegetables, fruits, whole grains, beans, nuts, olive oil",
#             3: "Balanced diet"
#         }

#         return diet_mapping.get(predicted_label, "No recommendation available")
#     except Exception as e:
#         print(f"⚠️ Error in diet prediction: {e}")
#         return "Error: Could not generate diet recommendation."

# # Generate meal plan using Gemini API
# def get_meal_plan(name, age, gender, extracted_data):
#     prompt = f"""
#     Generate a 7-day Heart-Healthy & Diabetes-Friendly Meal Plan for:
#     - Name: {name}
#     - Age: {age}
#     - Gender: {'Male' if gender == 1 else 'Female'}
#     - Total Cholesterol: {extracted_data.get('Total Cholesterol', 'Unknown')} mg/dL
#     - LDL Cholesterol: {extracted_data.get('LDL Cholesterol', 'Unknown')} mg/dL
#     - HDL Cholesterol: {extracted_data.get('HDL Cholesterol', 'Unknown')} mg/dL
#     - Triglycerides: {extracted_data.get('Triglycerides', 'Unknown')} mg/dL
    
#     Provide a structured meal plan including breakfast, lunch, dinner, snacks, and workouts.
#     """
#     try:
#         model = genai.GenerativeModel("gemini-1.5-pro-latest")
#         response = model.generate_content(prompt)
#         return response.text.strip() if response and hasattr(response, 'text') else "Error: Meal plan generation failed."
#     except Exception as e:
#         print(f"⚠️ Error fetching meal plan: {e}")
#         return "Error: Could not generate meal plan."

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

#         try:
#             systolic_bp = int(request.form['sysBP'])
#             diastolic_bp = int(request.form['diaBP'])
#             smoking = int(request.form['smoker'])
#             diabetes = int(request.form['diabetic'])
#             heart_attack = int(request.form['heart_attack'])
#             name = request.form['name']
#         except ValueError:
#             return "Error: Invalid input. Please enter numbers only."

#         pdf_text = extract_text_from_pdf(file_path)
#         extracted_data = extract_values(pdf_text)
#         print("📄 Extracted Data:", extracted_data)

#         if extracted_data:
#             diet = predict_diet(extracted_data, systolic_bp, diastolic_bp, smoking, diabetes, heart_attack)
#             meal_plan = get_meal_plan(name, extracted_data.get("Age", "Unknown"), extracted_data.get("Gender", "Unknown"), extracted_data)
#             return render_template('result.html', 
#                                    text=diet, 
#                                    meal_plan=meal_plan,
#                                    total_cholesterol=extracted_data.get("Total Cholesterol", "N/A"),
#                                    ldl=extracted_data.get("LDL Cholesterol", "N/A"),
#                                    hdl=extracted_data.get("HDL Cholesterol", "N/A"),)

#     return render_template('upload.html')

# if __name__ == '__main__':
#     app.run(debug=True)



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
        "Total Cholesterol": [r"Cholesterol Total[:\s]+(\d+)",
                              r"Total Cholesterol[:\s]+(\d+)",
                              r"(\d+)\s*Cholesterol\s*Total",
                              r"(\d+)\s*Cholesterol\s+",
                              r"Cholesterol Total[:\s]+(\d+)",
                              r"Total Cholesterol[:\s]+(\d+)"],
        "Triglycerides": [r"Triglycerides[:\s]+(\d+)",
                          r"(\d+)\s*Triglycerides"],
        "HDL Cholesterol": [r"HDL Cholesterol[:\s]+(\d+)", r"(\d+)\s*HDL"],
        "LDL Cholesterol": [r"LDL Cholesterol[:\s]+(\d+)", r"(\d+)\s*LDL"],
        "Age": [r"(\d{1,3})\s*(?:Years|Yr|Yrs)?",
                r"Age[:\s]+(\d+)"] ,
        "Gender": [r"Gender[:\s]+(Male|Female)", r"(Male|Female|Other)"],
    }

    for key, pattern_list in patterns.items():
        for pattern in pattern_list:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data[key] = int(match.group(1)) if match.group(1).isdigit() else match.group(1)
                break
        else:
            data[key] = None

    # Convert Gender: Male -> 1, Female -> 0
    data["Gender"] = 1 if data.get("Gender", "").lower() == "male" else 0 if data.get("Gender", "").lower() == "female" else None
    
    return data

# Predict diet recommendation
def predict_diet(data, systolic_bp, diastolic_bp, smoking, diabetes, heart_attack):
    if None in data.values():
        return "Error: Missing values in input. Please verify extracted data."
    
    try:
        input_data = pd.DataFrame([[data["Age"], data["Gender"], data["Total Cholesterol"],
                                    data["LDL Cholesterol"], data["HDL Cholesterol"],
                                    data["Total Cholesterol"] - data["HDL Cholesterol"],
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
        return "Error: Could not generate diet recommendation."

# Generate meal plan using Gemini API
def get_meal_plan(name, age, gender, extracted_data):
    prompt = f"""
    Generate a 7-day Heart-Healthy & Diabetes-Friendly Meal Plan for:
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
        
        # Remove * and # from meal plan output
        cleaned_meal_plan = re.sub(r'[*#]', '', meal_plan)
        return cleaned_meal_plan
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
            meal_plan = get_meal_plan(name, extracted_data.get("Age", "Unknown"), extracted_data.get("Gender", "Unknown"), extracted_data)
            return render_template('result.html', text=diet,
                                   total_cholesterol=extracted_data.get("Total Cholesterol", "N/A"),
                                   ldl=extracted_data.get("LDL Cholesterol", "N/A"),
                                   hdl=extracted_data.get("HDL Cholesterol", "N/A"),
                                   meal_plan=meal_plan)
            
    return render_template('upload.html')
   

if __name__ == '__main__':
    app.run(debug=True)
