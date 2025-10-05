AI Content Generator (Flask + Hugging Face/Groq)

Backend setup
1) Open a terminal and go to `email-generator/backend`.
2) Create and activate venv (Windows PowerShell):
   - `python -m venv venv`
   - `venv\Scripts\Activate`
   macOS/Linux:
   - `python -m venv venv`
   - `source venv/bin/activate`
3) Install requirements: `pip install -r requirements.txt`
4) Create `.env` in `backend/` with your provider/token/model:
   - `HF_API_TOKEN=hf_XXXXXXXXXXXXXXXXXXXXXXXX`
   - `HF_MODEL_ID=google/flan-t5-large`  (default if not set)
   - Optional: `HF_FALLBACK_MODELS=google/flan-t5-large,google/flan-t5-xl,tiiuae/falcon-7b-instruct,mistralai/Mistral-7B-Instruct-v0.2`
   - Provider switch (optional): `PROVIDER=groq` to use Groq instead of HF
   - Groq settings (if using Groq):
     - `GROQ_API_KEY=grq_...`
     - `GROQ_MODEL_ID=llama3-8b-8192` (default)
5) Run the server: `python main.py`
   - App: `http://127.0.0.1:5000` (serves the frontend)
   - APIs:
     - `POST /api/generate` (new, generic) → body: `{ "type": "email|essay|story|speech", ... }`
     - `POST /api/generate-email` (legacy) → body: `{ goal, recipient, tone, points }`

Frontend
Open `http://127.0.0.1:5000` in your browser. The Flask server serves the frontend and the API on the same origin.

Notes
- If you see CORS errors, ensure the backend is running and reachable.
- You can switch models by setting `HF_MODEL_ID` or `PROVIDER=groq` in `.env`.
 - Or set `HF_MODEL_ID` in `.env` (e.g., `mistralai/Mistral-7B-Instruct-v0.2` if you have access).
 - If you get 404 from Hugging Face, the model is misspelled or gated; choose another or request access.
 - The backend will automatically try fallback models from `HF_FALLBACK_MODELS` if the primary fails.
 - Alternatively set `PROVIDER=groq` for a free tier; get a key at `https://console.groq.com/keys`.

