
import os
import requests
import streamlit as st

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

st.set_page_config(
    page_title="Vidya AI Assistant",
    page_icon="🎓",
    layout="centered"
)


# =====================================
# CONFIGURATION
# =====================================

def get_setting(name, default=""):
    try:
        return st.secrets.get(
            name,
            os.getenv(name, default)
        )
    except Exception:
        return os.getenv(name, default)


SUPABASE_URL = get_setting("SUPABASE_URL")
SUPABASE_KEY = get_setting("SUPABASE_ANON_KEY")

GROQ_API_KEY = get_setting("GROQ_API_KEY")
GROQ_MODEL = get_setting(
    "GROQ_MODEL",
    "llama-3.3-70b-versatile"
)

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


# =====================================
# STYLING
# =====================================

st.markdown("""
<style>
.block-container {
    max-width: 850px;
    padding-top: 2rem;
}
[data-testid="stSidebar"] {
    display: none;
}
.vidya-head {
    font-size: 2rem;
    font-weight: 800;
    letter-spacing: -1px;
}
.subtle {
    color: #8b93a1;
}
</style>
""", unsafe_allow_html=True)


# =====================================
# SESSION STATE
# =====================================

if "session" not in st.session_state:
    st.session_state.session = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "user_email" not in st.session_state:
    st.session_state.user_email = ""


# =====================================
# GROQ AI FUNCTION
# =====================================

def ask_groq(prompt, history):

    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY missing in secrets.toml."
        )

    messages = [
        {
            "role": "system",
            "content": (
                "You are Vidya, a friendly AI learning assistant. "
                "Your purpose is to help students learn effectively. "
                "Explain academic concepts in simple language. "
                "Use examples, step-by-step explanations and "
                "clear formatting when useful. "
                "Give accurate answers. "
                "If you are unsure, say so instead of inventing facts. "
                "Respond in the language used by the student."
            )
        }
    ]

    # Include recent conversation history
    for msg in history[-12:]:

        if msg["role"] in ("user", "assistant"):

            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

    # Current user question
    messages.append({
        "role": "user",
        "content": prompt
    })

    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": 0.5,
        "max_tokens": 2048
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    try:

        response = requests.post(
            GROQ_URL,
            headers=headers,
            json=payload,
            timeout=(10, 60)
        )

    except requests.Timeout:
        raise RuntimeError(
            "Groq API timed out. Please try again."
        )

    except requests.ConnectionError:
        raise RuntimeError(
            "Cannot connect to Groq API. "
            "Check your internet connection."
        )

    except requests.RequestException as exc:
        raise RuntimeError(
            f"Network error: {exc}"
        )

    # Parse API response
    try:
        data = response.json()

    except ValueError:
        raise RuntimeError(
            "Groq returned an invalid response."
        )

    # Handle API errors
    if not response.ok:

        error = data.get("error", {})

        if isinstance(error, dict):
            message = error.get(
                "message",
                f"Groq API error: HTTP {response.status_code}"
            )
        else:
            message = str(error)

        raise RuntimeError(message)

    # Extract AI answer
    choices = data.get("choices", [])

    if not choices:
        raise RuntimeError(
            "Groq did not return an answer."
        )

    answer = (
        choices[0]
        .get("message", {})
        .get("content", "")
    )

    if not isinstance(answer, str) or not answer.strip():
        raise RuntimeError(
            "Groq returned an empty answer."
        )

    return answer.strip()


# =====================================
# HEADER
# =====================================

st.markdown(
    '<div class="vidya-head">🎓 VIDYA</div>'
    '<div class="subtle">'
    'AI Learning Assistant · Learn smarter. Grow better.'
    '</div>',
    unsafe_allow_html=True
)

st.divider()


# =====================================
# CONFIGURATION CHECK
# =====================================

if not SUPABASE_URL or not SUPABASE_KEY:

    st.error(
        "Supabase settings missing in secrets.toml."
    )
    st.stop()

if not GROQ_API_KEY:

    st.error(
        "Groq API key missing. "
        "Add GROQ_API_KEY to secrets.toml."
    )
    st.stop()


# =====================================
# LOGIN
# =====================================

if not st.session_state.session:

    st.title("Welcome to Vidya")

    st.caption(
        "Sign in using your existing Vidya account."
    )

    with st.form("login_form"):

        email = st.text_input(
            "Email",
            placeholder="Enter your email"
        )

        password = st.text_input(
            "Password",
            type="password"
        )

        submit = st.form_submit_button(
            "Sign in",
            type="primary",
            use_container_width=True
        )

    if submit:

        if not email.strip() or not password:

            st.warning(
                "Please enter email and password."
            )

        else:

            try:

                client = create_client(
                    SUPABASE_URL,
                    SUPABASE_KEY
                )

                result = client.auth.sign_in_with_password({
                    "email": email.strip(),
                    "password": password
                })

                st.session_state.session = result.session

                st.session_state.user_email = (
                    result.user.email
                )

                st.rerun()

            except Exception as exc:

                st.error(
                    f"Login failed: {exc}"
                )

    st.stop()


# =====================================
# LOGGED-IN USER
# =====================================

left, right = st.columns([4, 1])

left.caption(
    f"Signed in as {st.session_state.user_email}"
)

if right.button("Sign out"):

    st.session_state.session = None
    st.session_state.user_email = ""
    st.session_state.messages = []

    st.rerun()


# =====================================
# CHAT HEADER
# =====================================

st.subheader("💬 Ask Vidya AI")

st.caption(
    "Your personal AI learning assistant, powered by Groq."
)


# =====================================
# CLEAR CHAT
# =====================================

if st.button("🗑️ Clear Chat"):

    st.session_state.messages = []

    st.rerun()


# =====================================
# DISPLAY CHAT HISTORY
# =====================================

for msg in st.session_state.messages:

    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# =====================================
# CHAT INPUT
# =====================================

prompt = st.chat_input(
    "Ask Vidya anything..."
)


if prompt:

    # Save user question
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate AI answer
    with st.chat_message("assistant"):

        try:

            with st.spinner(
                "Vidya AI is thinking..."
            ):

                history = st.session_state.messages[:-1]

                answer = ask_groq(
                    prompt,
                    history
                )

            st.markdown(answer)

            st.session_state.messages.append({
                "role": "assistant",
                "content": answer
            })

        except Exception as exc:

            st.error(
                f"AI response failed: {exc}"
            )


# =====================================
# FOOTER
# =====================================

st.divider()

st.caption(
    f"Vidya AI · Powered by Groq · {GROQ_MODEL}"
)
