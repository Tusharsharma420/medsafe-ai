import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Configure Google Gen AI
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# We use gemini-2.5-flash for fast text generation
generation_model = genai.GenerativeModel('gemini-2.5-flash')

def summarize_interaction(med1, med2, severity, description):
    """
    Generates a patient-friendly summary of a drug interaction using Gemini.
    """
    if not api_key:
        return "API Key not configured. Unable to generate AI summary."
        
    prompt = f"""
    You are MedSafe AI, a helpful, educational, and non-diagnostic healthcare assistant.
    Explain the potential interaction between {med1} and {med2} to a patient in simple, reassuring terms.
    The known severity is '{severity}' and the medical description is '{description}'.
    
    Structure your response appropriately and keep it under 3-4 sentences.
    Always include a disclaimer that this is educational and not medical advice, advising them to consult a doctor.
    """
    try:
        response = generation_model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating summary: {e}"

def get_symptom_guidance(age, gender, medicines, experience):
    """
    Generates educational guidance on symptoms or side-effects based on user input.
    """
    if not api_key:
        return "API Key not configured. Unable to generate AI guidance.", "Unknown"
        
    prompt = f"""
    You are MedSafe AI, a healthcare assistant. Determine how to educate a user based on their experience.
    
    User Profile: Age {age}, {gender}
    Recently taken medicines: {medicines}
    Reported Symptoms/Experience: {experience}
    
    Provide two things:
    1. A short, educational response highlighting possible contributing factors, home remedies or lifestyle tips, and warning signs. Remain informative and non-diagnostic. Do not induce panic.
    2. Suggest an Emergency Risk Level (Low, Medium, or High) based solely on common medical triaging for the described symptoms.

    Output exact format:
    RISK_LEVEL: [Low/Medium/High]
    GUIDANCE:
    [Your educational response here]
    """
    try:
        response = generation_model.generate_content(prompt)
        text = response.text
        
        # Parse output
        risk_level = "Unknown"
        guidance = text
        if "RISK_LEVEL:" in text:
            lines = text.split('\n')
            for line in lines:
                if line.startswith("RISK_LEVEL:"):
                    risk_level = line.replace("RISK_LEVEL:", "").strip()
            # extract guidance part
            try:
                guidance_split = text.split("GUIDANCE:")
                if len(guidance_split) > 1:
                    guidance = guidance_split[1].strip()
            except Exception:
                pass
                
        return guidance, risk_level
    except Exception as e:
        return f"Error generating guidance: {e}", "Unknown"
