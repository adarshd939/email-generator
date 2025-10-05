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

PROVIDER = os.getenv("PROVIDER", "hf").lower()  # "hf" or "groq"

HF_API_TOKEN = os.getenv("HF_API_TOKEN")
HF_MODEL_ID = os.getenv("HF_MODEL_ID", "google/flan-t5-large")
HEADERS = {"Authorization": f"Bearer {HF_API_TOKEN}"} if HF_API_TOKEN else {}

# Comma-separated fallback models (will be tried if the selected model 404s)
FALLBACK_MODELS_ENV = os.getenv(
    "HF_FALLBACK_MODELS",
    ",".join([
        "google/flan-t5-large",
        "google/flan-t5-xl",
        "tiiuae/falcon-7b-instruct",
        "mistralai/Mistral-7B-Instruct-v0.2",
    ])
)
FALLBACK_MODELS = [m.strip() for m in FALLBACK_MODELS_ENV.split(",") if m.strip()]

def _hf_model_url(model_id: str) -> str:
    return f"https://api-inference.huggingface.co/models/{model_id}"

# Groq configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL_ID = os.getenv("GROQ_MODEL_ID", "llama3-8b-8192")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


# Serve frontend
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))

@app.route('/')
def serve_index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/<path:filename>')
def serve_static_files(filename):
    return send_from_directory(FRONTEND_DIR, filename)


def _build_prompt_for_type(content_type: str, data: dict) -> str:
    """Build an instruction-style prompt for the requested content type.

    Supported content types: email, essay, story, speech
    """
    ct = (content_type or '').strip().lower()
    if ct == 'email':
        email_goal = data.get('goal', '').strip()
        recipient = data.get('recipient', '').strip()
        tone = data.get('tone', '').strip()
        key_points = data.get('points', '').strip()
        return f"""
    [INST]
    You are an expert email copywriter. Your task is to generate a professional email.
    Generate a subject line and an email body based on these requirements:
    - **Goal:** {email_goal}
    - **Recipient:** {recipient}
    - **Tone:** {tone}
    - **Key Points to Include:** {key_points}

    **Output Format:**
    Subject: [Your generated subject line]
    ---
    Body:
    [Your generated email body]
    [/INST]
    """
    if ct == 'essay':
        topic = data.get('topic', '').strip()
        tone = data.get('tone', '').strip()
        length_words = data.get('length_words', '')
        key_points = data.get('points', '').strip()
        return f"""
    [INST]
    You are a skilled academic writer. Write a coherent, well-structured essay.
    Requirements:
    - **Topic:** {topic}
    - **Tone:** {tone}
    - **Target Length (words):** {length_words}
    - **Arguments/Key Points:** {key_points}

    **Output Format:**
    Title: [Concise essay title]
    ---
    Essay:
    [Well-structured essay with introduction, body paragraphs, and conclusion]
    [/INST]
    """
    if ct == 'story':
        genre = data.get('genre', '').strip()
        setting = data.get('setting', '').strip()
        characters = data.get('characters', '').strip()
        tone = data.get('tone', '').strip()
        length_words = data.get('length_words', '')
        plot_points = data.get('points', '').strip()
        return f"""
    [INST]
    You are a creative fiction author. Write an engaging short story.
    Requirements:
    - **Genre:** {genre}
    - **Setting:** {setting}
    - **Main Characters:** {characters}
    - **Tone:** {tone}
    - **Target Length (words):** {length_words}
    - **Plot Prompts/Beats:** {plot_points}

    **Output Format:**
    Title: [Story title]
    ---
    Story:
    [Narrative with clear beginning, middle, and end]
    [/INST]
    """
    if ct == 'speech':
        occasion = data.get('occasion', '').strip()
        audience = data.get('audience', '').strip()
        tone = data.get('tone', '').strip()
        duration_minutes = data.get('duration_minutes', '')
        key_points = data.get('points', '').strip()
        return f"""
    [INST]
    You are an expert speechwriter. Draft a compelling speech suitable for delivery.
    Requirements:
    - **Occasion:** {occasion}
    - **Audience:** {audience}
    - **Tone:** {tone}
    - **Target Duration (minutes):** {duration_minutes}
    - **Key Points/Themes:** {key_points}

    **Output Format:**
    Title: [Speech title]
    ---
    Speech:
    [Speech with opening, key points, transitions, and strong closing]
    [/INST]
    """
    # Default fall back to email schema if unsupported type
    return _build_prompt_for_type('email', data)


def _call_hf_or_groq(prompt: str):
    """Call the configured provider (HF or Groq) with a given prompt.

    Returns (content, meta_dict) or (None, error_response, status_code)
    """
    if not HF_API_TOKEN and PROVIDER != 'groq':
        return None, jsonify({"error": "Missing HF_API_TOKEN. Set it in backend/.env"}), 500

    payload_hf = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 512, "temperature": 0.7, "return_full_text": False},
        "options": {"wait_for_model": True}
    }

    def _extract_text(result_obj):
        if isinstance(result_obj, list) and result_obj:
            first = result_obj[0]
            if isinstance(first, dict):
                if 'generated_text' in first:
                    return first.get('generated_text', '')
                if 'summary_text' in first:
                    return first.get('summary_text', '')
        if isinstance(result_obj, dict) and 'generated_text' in result_obj:
            return result_obj.get('generated_text', '')
        return ''

    def try_infer_hf(model_id: str):
        try:
            response = requests.post(_hf_model_url(model_id), headers=HEADERS, json=payload_hf, timeout=120)
            response.raise_for_status()
            result = response.json()
            if isinstance(result, dict) and result.get("error"):
                return None, result.get("error")
            generated_text = _extract_text(result)
            if not generated_text:
                return None, "Empty response from model"
            return generated_text, None
        except requests.exceptions.HTTPError as http_err:
            status_code = getattr(http_err.response, 'status_code', 500)
            if status_code == 404:
                return None, f"Model not found (404) for {model_id}"
            return None, f"HTTP error from HF for {model_id}: {http_err}"
        except requests.exceptions.RequestException as e:
            return None, f"Request error for {model_id}: {e}"

    if PROVIDER == 'groq':
        if not GROQ_API_KEY:
            return None, jsonify({"error": "Missing GROQ_API_KEY. Set it in backend/.env"}), 500
        try:
            groq_headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            }
            groq_payload = {
                "model": GROQ_MODEL_ID,
                "messages": [
                    {"role": "system", "content": "You are an expert writer and editor."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.7,
                "max_tokens": 512,
            }
            resp = requests.post(GROQ_URL, headers=groq_headers, json=groq_payload, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
            if not content:
                return None, jsonify({"error": "Empty response from Groq"}), 502
            return content, {"model_used": GROQ_MODEL_ID, "provider": "groq"}, None
        except requests.exceptions.RequestException as e:
            return None, jsonify({"error": f"Groq request failed: {e}"}), 502

    # Default: HF flow with fallbacks
    tried = [HF_MODEL_ID] + [m for m in FALLBACK_MODELS if m != HF_MODEL_ID]
    errors = []
    for model_id in tried:
        text, err = try_infer_hf(model_id)
        if text:
            return text, {"model_used": model_id, "provider": "hf"}, None
        errors.append(err)

    return None, jsonify({
        "error": "All models failed",
        "details": errors,
        "tried_models": tried,
        "hint": "Set HF_MODEL_ID or switch PROVIDER=groq in backend/.env",
    }), 502


@app.route('/api/generate', methods=['POST'])
def generate_generic():
    data = request.get_json(silent=True) or {}
    content_type = data.get('type')
    if not content_type:
        return jsonify({"error": "Missing 'type'. Use one of: email, essay, story, speech"}), 400

    prompt = _build_prompt_for_type(content_type, data)
    content, meta_or_err, maybe_status = _call_hf_or_groq(prompt)
    if content is None:
        # meta_or_err is a Flask response, maybe_status is status code
        return meta_or_err, maybe_status
    meta = meta_or_err or {}
    return jsonify({
        "generated_text": content,
        "type": content_type,
        **meta
    })

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

    if not HF_API_TOKEN:
        return jsonify({"error": "Missing HF_API_TOKEN. Set it in backend/.env"}), 500

    # 2. Engineer the prompt for the model
    prompt = f"""
    [INST]
    You are an expert email copywriter. Your task is to generate a professional email.
    Generate a subject line and an email body based on these requirements:
    - **Goal:** {email_goal}
    - **Recipient:** {recipient}
    - **Tone:** {tone}
    - **Key Points to Include:** {key_points}

    **Output Format:**
    Subject: [Your generated subject line]
    ---
    Body:
    [Your generated email body]
    [/INST]
    """

    # 3. Call the provider API
    payload_hf = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 512, "temperature": 0.7, "return_full_text": False},
        "options": {"wait_for_model": True}
    }

    def _extract_text(result_obj):
        # Result can be list[{'generated_text': '...'}] or list[{'summary_text': '...'}]
        if isinstance(result_obj, list) and result_obj:
            first = result_obj[0]
            if isinstance(first, dict):
                if 'generated_text' in first:
                    return first.get('generated_text', '')
                if 'summary_text' in first:
                    return first.get('summary_text', '')
        # Some endpoints may return dict with 'generated_text'
        if isinstance(result_obj, dict) and 'generated_text' in result_obj:
            return result_obj.get('generated_text', '')
        return ''

    def try_infer_hf(model_id: str):
        try:
            response = requests.post(_hf_model_url(model_id), headers=HEADERS, json=payload_hf, timeout=120)
            response.raise_for_status()
            result = response.json()
            if isinstance(result, dict) and result.get("error"):
                return None, result.get("error")
            generated_text = _extract_text(result)
            if not generated_text:
                return None, "Empty response from model"
            return generated_text, None
        except requests.exceptions.HTTPError as http_err:
            status_code = getattr(http_err.response, 'status_code', 500)
            if status_code == 404:
                return None, f"Model not found (404) for {model_id}"
            return None, f"HTTP error from HF for {model_id}: {http_err}"
        except requests.exceptions.RequestException as e:
            return None, f"Request error for {model_id}: {e}"

    if PROVIDER == 'groq':
        if not GROQ_API_KEY:
            return jsonify({"error": "Missing GROQ_API_KEY. Set it in backend/.env"}), 500
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
            resp.raise_for_status()
            data = resp.json()
            content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
            if not content:
                return jsonify({"error": "Empty response from Groq"}), 502
            return jsonify({"generated_email": content, "model_used": GROQ_MODEL_ID, "provider": "groq"})
        except requests.exceptions.RequestException as e:
            return jsonify({"error": f"Groq request failed: {e}"}), 502

    # Default: Hugging Face flow with fallbacks
    tried = [HF_MODEL_ID] + [m for m in FALLBACK_MODELS if m != HF_MODEL_ID]
    errors = []
    for model_id in tried:
        text, err = try_infer_hf(model_id)
        if text:
            return jsonify({"generated_email": text, "model_used": model_id, "provider": "hf"})
        errors.append(err)

    return jsonify({
        "error": "All models failed",
        "details": errors,
        "tried_models": tried,
        "hint": "Set HF_MODEL_ID or switch PROVIDER=groq in backend/.env",
    }), 502


if __name__ == '__main__':
    # Runs the server on http://127.0.0.1:5000
    app.run(port=5000, debug=True)


