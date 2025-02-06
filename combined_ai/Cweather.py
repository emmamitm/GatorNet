import os
import requests
import google.generativeai as genai

def get_groq_response(prompt):
    url = "https://api.groq.com/chat"
    headers = {"Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}", "Content-Type": "application/json"}
    data = {"model": "llama3", "messages": [{"role": "user", "content": prompt}]}
    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        json_response = response.json()
        print("Groq API Response:", json_response)  # Debugging
        return json_response.get("choices", [{}])[0].get("message", {}).get("content", "No valid response")
    except requests.exceptions.RequestException as e:
        return f"Groq API Error: {e}"

def get_mistral_response(prompt):
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {os.getenv('MISTRAL_API_KEY')}", "Content-Type": "application/json"}
    data = {
        "model": "mistral-small-latest",  # Corrected model name
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,  # Adjusted optional parameter for more natural responses
        "max_tokens": 200  # Set limit to avoid excessive usage
    }
    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        json_response = response.json()
        print("Mistral API Response:", json_response)  # Debugging
        return json_response.get("choices", [{}])[0].get("message", {}).get("content", "No valid response")
    except requests.exceptions.RequestException as e:
        print("Mistral API Error Details:", e.response.text if e.response else e)
        return f"Mistral API Error: {e}"

def analyze_weather_with_ai(prompt):
    if "quick" in prompt.lower():
        return get_groq_response(prompt)
    else:
        return get_mistral_response(prompt)

if __name__ == "__main__":
    prompt = "What events are happening at UF today?"
    response = analyze_weather_with_ai(prompt)
    print("\nAI Chatbot Response:\n")
    print(response)
