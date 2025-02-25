import streamlit as st
import httpx


st.set_page_config("Nabu Audio Notes", page_icon="🔊")


def post(path, **kwargs):
    api_url = st.secrets.get("api_url")

    with httpx.Client(base_url=api_url, timeout=30) as client:
        response = client.post(path, params=kwargs)
        return response.json()


def transcribe(file, **kwargs):
    api_url = st.secrets.get("api_url")

    with httpx.Client(base_url=api_url, timeout=300) as client:
        response = client.post(
            "/transcribe",
            params=kwargs,
            files=dict(file=("note.wav", file, "audio/wav")),
        )
        return response.json()


def login():
    email = st.text_input("Email")

    if st.button("Login", icon="🔑"):
        msg = post("/login", email=email)
        st.session_state.username = email
        st.session_state.status = "otp"
    else:
        st.stop()


def verify():
    email = st.session_state.username
    otp = st.text_input("OTP")

    if st.button("Verify", icon="🔑"):
        msg = post("/verify", email=email, otp=otp)
        st.session_state.token = msg.get("token")
        st.session_state.status = "logged"
    else:
        st.stop()


status = st.session_state.get("status", "unknown")


if status == "unknown":
    login()
    st.rerun()


if status == "otp":
    verify()
    st.rerun()


if status != "logged":
    raise ValueError(status)


username = st.session_state.get("username")
token = st.session_state.get("token")

audio = st.audio_input("Record audio")

if not audio:
    st.info("Record an audio to create a new note.")
    st.stop()

if st.button("Create note", icon="📝"):
    with st.spinner("Transcribing..."):
        transcription = transcribe(email=username, token=token, file=audio.read())
        st.success(transcription)
