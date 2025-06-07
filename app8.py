from flask import Flask, request, render_template
from werkzeug.utils import secure_filename
import os
import pandas as pd
import fitz  # PyMuPDF
import re
import pickle
import google.generativeai as genai

# Configure Gemini API (replace with your real key)
genai.configure(api_key="AIzaSyAbK8ICujTGYSmAX4v4Dt4-0UJiIlKk4jg")

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load the trained model (ensure you're loading the correct one)
with open('diet_exercise_model.pkl', 'rb') as f:
    diet_model = pickle.load(f)

# Extract text from PDF
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    return ''.join(page.get_text() for page in doc)

# Extract values from text using regex patterns
def extract_values(text):
    values = {}

    def extract(*patterns):
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1).replace(',', ''))
                except:
                    return None
        return None

    values["Total Cholesterol"] = extract(
        r"Total Cholesterol\s*\n?\s*(\d+\.\d+)",
         r"(\d+\.\d+)\s*Cholesterol\s*Total",
        r"Cholesterol Total[:\s]+(\d+\.\d+)",
        r"Cholesterol Total[:\s]+(\d+)",
        r"(\d+\.\d+)\s*Cholesterol\s*Total",
        r"Cholesterol Total[:\s]+(\d+\.\d+)",
        r"Cholesterol Total[:\s]+(\d+)",
        r"Total Cholesterol[:\s]+(\d+)",
        r"(\d+)\s*Cholesterol\s*Total"
    )
    values["LDL Cholesterol"] = extract(
        r"(\d+\.\d+)\s*LDL Cholesterol",
        r"LDL Cholesterol[:\s]+(\d+\.\d+)",
        r"LDL Cholesterol[:\s]+(\d+)",
        r"(\d+\.\d+)\s*LDL Cholesterol,Calculated",
        r"(\d+)\s*LDL"
    )
    values["HDL Cholesterol"] = extract(
        r"(\d+\.\d+)\s*HDL Cholesterol",
        r"HDL Cholesterol[:\s]+(\d+\.\d+)",
        r"HDL Cholesterol[:\s]+(\d+)",
        r"(\d+\.\d+)\s*HDL Cholesterol,Calculated",
        r"(\d+)\s*HDL"
    )
    values["Triglycerides"] = extract(
        r"(\d+\.\d+)\s*Triglycerides",
        r"Triglycerides[:\s]+(\d+\.\d+)",
        r"Triglycerides[:\s]+(\d+)",
        r"(\d+)\s*Triglycerides"
    )
    values["GlucoseF"] = extract(
    r"Glucose,\s*Fasting.*?(\d{2,3}\.\d{1,2})",
    r"Glucose,?\s*Fasting\s*mg/dL\s*\d{2,3}\.\d{2}\s*-\s*\d{2,3}\.\d{2}\s*(\d{2,3}\.\d{2})",
    r"Glucose,?\s*Fasting.*?(\d{2,3}\.\d{2})",
    r"Fasting Glucose *?(\d{2,3}\.\d{2})",
    r"Glucose\s*,?\s*Fasting\s+(\d+(?:\.\d+)?)"
)


    # CBC and others
    values["Hemoglobin"] = extract(r"Hemoglobin (Colorimetric method)[:\s]+(\d+\.\d+)", r"Hb[:\s]+(\d+\.\d+)")
    values["Total Leukocyte Count"] = extract(r"Total Leukocyte Count[:\s]+(\d+)", r"WBC[:\s]+(\d+)")
    values["Platelet Count"] = extract(r"Platelet Count[:\s]+(\d+)")
    values["Hematocrit"] = extract(r"Hematocrit[:\s]+(\d+\.\d+)", r"HCT[:\s]+(\d+\.\d+)")
    values["RBC Count"] = extract(r"Red Blood Cell Count[:\s]+(\d+\.\d+)", r"RBC[:\s]+(\d+\.\d+)")
    values["MCV"] = extract(r"Mean Corpuscular Volume[:\s]+(\d+\.\d+)", r"MCV[:\s]+(\d+\.\d+)")
    values["MCH"] = extract(r"Mean Corpuscular Hemoglobin[:\s]+(\d+\.\d+)", r"MCH[:\s]+(\d+\.\d+)")
    values["MCHC"] = extract(r"Mean Corpuscular Hemoglobin Concentration[:\s]+(\d+\.\d+)", r"MCHC[:\s]+(\d+\.\d+)")

    # Diabetes
    values["HbA1c"] = extract(r"HbA1c[:\s]+(\d+\.\d+)")
    values["Postprandial Blood Glucose"] = extract(r"Postprandial Blood Glucose[:\s]+(\d+\.\d+)", r"PPBG[:\s]+(\d+\.\d+)")
    values["Random Blood Sugar"] = extract(r"Random Blood Sugar[:\s]+(\d+\.\d+)", r"RBS[:\s]+(\d+\.\d+)")

    # Kidney
    values["Creatinine"] = extract(r"Creatinine[:\s]+(\d+\.\d+)")
    values["BUN"] = extract(r"Blood Urea Nitrogen[:\s]+(\d+\.\d+)",
                            r"Blood Urea Nitrogen[\s]+(\d+\.\d+)")
    values["eGFR"] = extract(r"eGFR[:\s]+(\d+\.\d+)")

    # Liver
    values["SGPT"] = extract(r"SGPT[:\s]+(\d+\.\d+)", r"ALT[:\s]+(\d+\.\d+)")
    values["SGOT"] = extract(r"SGOT[:\s]+(\d+\.\d+)", r"AST[:\s]+(\d+\.\d+)")
    values["Total Bilirubin"] = extract(r"Total Bilirubin[:\s]+(\d+\.\d+)")
    values["ALP"] = extract(r"Alkaline Phosphatase[:\s]+(\d+\.\d+)")
    values["GGT"] = extract(r"GGT[:\s]+(\d+\.\d+)")

    # Thyroid
    values["TSH"] = extract(r"TSH[:\s]+(\d+\.\d+)")
    values["Free T3"] = extract(r"Free T3[:\s]+(\d+\.\d+)")
    values["Free T4"] = extract(r"Free T4[:\s]+(\d+\.\d+)")

    # Vitamins & Minerals
    values["Vitamin D"] = extract(r"Vitamin D[:\s]+(\d+\.\d+)")
    values["Vitamin B12"] = extract(r"Vitamin B12\s+(\d+\.\d+)")

    values["Serum Calcium"] = extract(r"Serum Calcium[:\s]+(\d+\.\d+)")
    values["Serum Iron"] = extract(r"Serum Iron[:\s]+(\d+\.\d+)")
    values["Ferritin"] = extract(r"Ferritin[:\s]+(\d+\.\d+)")
    values["Folate"] = extract(r"Folate[:\s]+(\d+\.\d+)")
    values["Magnesium"] = extract(r"Magnesium[:\s]+(\d+\.\d+)")
    values["Zinc"] = extract(r"Zinc[:\s]+(\d+\.\d+)")

    # Body Composition
    values["Body Fat %"] = extract(r"Body Fat[:\s]+(\d+\.\d+)")
    values["Waist-to-Hip Ratio"] = extract(r"Waist-to-Hip Ratio[:\s]+(\d+\.\d+)")
    values["Visceral Fat"] = extract(r"Visceral Fat[:\s]+(\d+\.\d+)")
    values["Muscle Mass"] = extract(r"Muscle Mass[:\s]+(\d+\.\d+)")
    values["BMR"] = extract(r"Basal Metabolic Rate[:\s]+(\d+\.\d+)", r"BMR[:\s]+(\d+\.\d+)")
    values["Haemoglobin"] = extract(r"Haemoglobin[:\s]+(\d+\.\d+)")
    values["RBC Count"] = extract(r"RBC Count[:\s]+(\d+\.\d+)")
    values["WBC Count"] = extract(r"WBC Count[:\s]+(\d+)")
    values["Blood Urea"] = extract(r"Blood Urea[:\s]+(\d+\.\d+)")
    # Remove None values for use in diet prediction and frontend
    values = {k: v for k, v in values.items() if v is not None}

    return values
# Predict diet recommendation based on extracted values and BMI
def predict_diet_with_bmi(data, bmi, systolic_bp, diastolic_bp, smoking, diabetes, heart_attack):
    if None in data.values():
        missing = [key for key, value in data.items() if value is None]
        return f"Missing values: {', '.join(missing)}. Please check your uploaded report."
    try:
        df = pd.DataFrame([[data["Age"], data["Gender"], data["Total Cholesterol"],
                    data["LDL Cholesterol"], data["HDL Cholesterol"],
                    bmi, systolic_bp, diastolic_bp, smoking, diabetes]], 
                  columns=["age", "sex", "total_cholesterol", "ldl", "hdl", 
                           "bmi", "systolic_bp", "diastolic_bp", 
                           "smoking", "diabetes"])

        
        # Perform prediction
        label = diet_model.predict(df)[0]  # Use model.predict here
        return {
            0: "Low-fat, high-fiber diet (fruits, vegetables, grains, beans, peas, lentils)",
            1: "Increase healthy fats - avocados, nuts, seeds, fatty fish, olives",
            2: "Heart-healthy Mediterranean diet - vegetables, fruits, whole grains, beans, nuts, olive oil",
            3: "Balanced diet"
        }.get(label, "No recommendation available")
    except Exception as e:
        print("Prediction error:", e)
        return "Eat Healthy Food Don't Consume Junk Food"

# Generate a personalized 7-day meal and exercise plan using Gemini API
def get_meal_plan(name, age, gender, data, bmi):
    total_chol = data.get("Total Cholesterol", "unknown")
    ldl = data.get("LDL Cholesterol", "unknown")
    hdl = data.get("HDL Cholesterol", "unknown")
    triglycerides = data.get("Triglycerides", "unknown")
    glucosef = data.get("GlucoseF", "unknown")
    food = data.get("food", "unknown")
    vitaminB12=data.get("Vitamin B12","unknown")
    Haemoglobin=data.get("Haemoglobin","unknown")
    WBCCount=data.get("WBC Count","unknown")
    RBCCount=data.get("RBC Count","unknown")
    BloodUrea=data.get("Blood Urea","unknown")
    gender_text = "male" if gender == 1 else "female"
    
    prompt = f"""
    Create a **7-day personalized meal and exercise plan** for the following individual:
    
    - Name: {name}
    - Age: {age}
    - Gender: {gender_text}
    - BMI: {bmi}
    - Total Cholesterol: {total_chol}
    - LDL: {ldl}
    - HDL: {hdl}
    - Triglycerides: {triglycerides}
    - Glucose: {glucosef}
    - Food:{food}
    - Vitamin:{vitaminB12}
    - RBC:{RBCCount}
    - WBC:{WBCCount}
    - Haemoglobin:{Haemoglobin}
    - BloodUrea:{BloodUrea}
    
    The plan should be:
    - Tailored to heart health and lipid management.
    - Include daily: Breakfast, Lunch, Dinner, 2 healthy snacks.
    - Include light to moderate exercises (15–30 min) depending on BMI.
    - Include water intake recommendations and portion size guidance.
    - Keep meals culturally neutral, practical and easily available in urban India.
    - Include only {food} meals.
    - Suggest Indian Diet With Indian Nomenclature 
- The suggestions should be based on general health guidelines and publicly available diet practices, without impersonating any organization.
    - While suggesting diet please consider the Vitamin:{vitaminB12} , WBC:{WBCCount} ,RBC:{RBCCount}, Haemoglobin:{Haemoglobin} , BloodUrea:{BloodUrea} if this values are null or 0 please suggest diet based on above profile 
    
    Format output as:
    Day 1:
    - Breakfast: ...
    - Snack: ...
    - Lunch: ...
    - Snack: ...
    - Dinner: ...
    - Exercise: ...
    (Repeat for Day 2 to Day 7)
    """
    try:
        # model = genai.GenerativeModel("gemini-1.5-pro-latest")gemini-2.0-flash
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        
        if response and hasattr(response, 'text'):
            return re.sub(r'[*#]', '', response.text.strip())
        else:
            print("Error Occurred while fetching Data")
            return "Meal plan generation failed. Please try again later."
    except Exception as e:
        print("Gemini error:", e)
        return "Could not generate a meal plan at the moment. Please check the API configuration or try again later."

# Handle file upload and form submission
@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files.get('file')
        if not file or file.filename == '':
            return "No file selected."

        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        try:
            name = request.form['name']
            age = int(request.form['age'])
            gender = int(request.form['gender'])
            weight = float(request.form['weight'])
            height_cm = float(request.form['height'])
            bmi = round(weight / ((height_cm / 100) ** 2), 2)

            systolic_bp = int(request.form['sysBP'])
            diastolic_bp = int(request.form['diaBP'])
            smoking = int(request.form['smoker'])
            diabetes = int(request.form['diabetic'])
            heart_attack = int(request.form['heart_attack'])
            food = request.form['food']
        except ValueError:
            return "Invalid input values."

        text = extract_text_from_pdf(file_path)
        extracted_data = extract_values(text)
        extracted_data["Age"] = age
        extracted_data["Gender"] = gender
        extracted_data["food"] = food

        # Predict diet and generate meal plan
        diet = predict_diet_with_bmi(extracted_data, bmi, systolic_bp, diastolic_bp, smoking, diabetes, heart_attack)
        meal_plan = get_meal_plan(name, age, gender, extracted_data, bmi)
        print(extracted_data)


        return render_template('result1.html', 
                               text=diet,
                               total_cholesterol=extracted_data.get("Total Cholesterol"),
                               ldl=extracted_data.get("LDL Cholesterol"),
                               hdl=extracted_data.get("HDL Cholesterol"),
                               triglycerides=extracted_data.get("Triglycerides"),
                               glucosef=extracted_data.get("GlucoseF"),
                               bmi=bmi,
                               meal_plan=meal_plan)

    return render_template('upload1.html')

if __name__ == '__main__':
    app.run(debug=True)
