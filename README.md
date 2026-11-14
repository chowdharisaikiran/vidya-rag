# Vidya Simple RAG UI

A minimal Streamlit UI for the existing Vidya Express backend.

## Setup

1. Create/activate your Python virtual environment.
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`.
4. Set your Supabase project URL, publishable/anon key, and the actual Express backend base URL.
5. Start the Streamlit UI: `streamlit run app.py`.

The backend URL must be the base URL where the existing Express `server.ts` is actually running. Do not assume port 8000; check the backend's listen configuration.

## Backend compatibility and security note

This UI calls `POST /api/ai/chat` and `POST /api/rag/upload`. The supplied `server.ts` code showed the chat route and a JSON upload route that expects `title`, `content`, and `subject`.

Before using real institutional data, the existing backend must be reviewed and fixed for tenant isolation. The supplied code showed a hard-coded institution filter in chat and unscoped document listing/usage/preview routes. Do not expose this backend publicly or use production student/institution data until those access controls are corrected and tested.
