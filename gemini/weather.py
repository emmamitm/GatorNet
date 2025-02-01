import os
import google.generativeai as genai

# Load API key from environment variable
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("Error: Please set your GEMINI_API_KEY as an environment variable.")
    exit()

# Configure Gemini API
genai.configure(api_key=API_KEY)

# Function to generate text using Gemini
def analyze_text_with_gemini(prompt):
    model = genai.GenerativeModel("gemini-pro")  # Free model version
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {e}"

# Example usage
if __name__ == "__main__":
    prompt = "Summarize the current weather conditions in Gainesville, Florida."
    summary = analyze_text_with_gemini(prompt)
    print("\nGemini AI Summary:\n")
    print(summary)
