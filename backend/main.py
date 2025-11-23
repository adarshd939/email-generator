import os
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
# Enable CORS to allow requests from your frontend
CORS(app)

# Groq configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL_ID = os.getenv("GROQ_MODEL_ID", "llama-3.1-8b-instant")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


# Serve frontend
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))

@app.route('/')
def serve_index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/<path:filename>')
def serve_static_files(filename):
    return send_from_directory(FRONTEND_DIR, filename)


@app.route('/api/generate-email', methods=['POST'])
def generate_email():
    # 1. Get user inputs from the frontend request
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid input"}), 400

    email_goal = data.get('goal', '').strip()
    recipient = data.get('recipient', '').strip()
    tone = data.get('tone', '').strip()
    key_points = data.get('points', '').strip()

    # Validate Groq API key
    if not GROQ_API_KEY:
        return jsonify({"error": "Missing GROQ_API_KEY. Set it in backend/.env"}), 500

    # Create the prompt for Groq
    prompt = f"""You are an expert email copywriter. Your task is to generate a professional email.
Generate a subject line and an email body based on these requirements:
- **Goal:** {email_goal}
- **Recipient:** {recipient}
- **Tone:** {tone}
- **Key Points to Include:** {key_points}

**Output Format:**
Subject: [Your generated subject line]
---
Body:
[Your generated email body]"""

    # Call Groq API
    try:
        groq_headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        groq_payload = {
            "model": GROQ_MODEL_ID,
            "messages": [
                {"role": "system", "content": "You are an expert email copywriter."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 512,
        }
        resp = requests.post(GROQ_URL, headers=groq_headers, json=groq_payload, timeout=120)
        
        # Better error handling - capture actual Groq error message
        if not resp.ok:
            error_detail = "Unknown error"
            try:
                error_data = resp.json()
                # Groq error format: {"error": {"message": "...", "type": "...", ...}}
                if isinstance(error_data.get('error'), dict):
                    error_detail = error_data['error'].get('message', str(error_data))
                else:
                    error_detail = str(error_data)
                print(f"[ERROR] Groq API Error ({resp.status_code}): {error_data}")
            except:
                error_detail = resp.text
                print(f"[ERROR] Groq API Error ({resp.status_code}): {resp.text}")
            
            return jsonify({
                "error": f"Groq API error ({resp.status_code})",
                "details": error_detail,
                "model_used": GROQ_MODEL_ID,
                "hint": "Check your GROQ_API_KEY and GROQ_MODEL_ID. Valid models: llama-3.1-8b-instant, llama-3.1-70b-versatile, mixtral-8x7b-32768, gemma-2-9b-it"
            }), resp.status_code
        
        data = resp.json()
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
        if not content:
            return jsonify({"error": "Empty response from Groq"}), 502
        return jsonify({"generated_email": content, "model_used": GROQ_MODEL_ID, "provider": "groq"})
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Groq request failed: {e}"}), 502


if __name__ == '__main__':
    # Runs the server on http://127.0.0.1:5000
    app.run(port=5000, debug=True)


