import streamlit as st
import httpx


st.set_page_config("Nabu Audio Notes", page_icon="🔊")


def post(path, **kwargs):
    api_url = st.secrets.get("api_url")

    with httpx.Client(base_url=api_url, timeout=30) as client:
        response = client.post(path, params=kwargs)
        return response.json()


def get(path, **kwargs):
    api_url = st.secrets.get("api_url")

    with httpx.Client(base_url=api_url, timeout=30) as client:
        response = client.get(path, params=kwargs)
        return response.json()


def delete(path, **kwargs):
    api_url = st.secrets.get("api_url")

    with httpx.Client(base_url=api_url, timeout=30) as client:
        response = client.delete(path, params=kwargs)
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


def _login(email):
    post("/login", email=email)
    st.session_state.username = email
    st.session_state.status = "otp"


def login():
    email = st.text_input("Email")

    if email:
        st.button("Login", icon="🔑", on_click=_login, args=(email,))

    st.stop()


def _verify(otp):
    msg = post("/verify", email=st.session_state.username, otp=otp)
    st.session_state.token = msg.get("token")
    st.session_state.status = "logged"


def verify():
    email = st.session_state.username
    otp = st.text_input("OTP")

    if otp:
        st.button("Verify", icon="🔑", on_click=_verify, args=(otp,))

    st.stop()


status = st.session_state.get("status", "unknown")


if status == "unknown":
    login()

if status == "otp":
    verify()

if status != "logged":
    raise ValueError(status)


username = st.session_state.get("username")
token = st.session_state.get("token")

upload = st.toggle("Upload audio")

if upload:
    audio = st.file_uploader("Upload audio file", ["wav", "mp3", "aac", "ogg", "m4a"])
else:
    audio = st.audio_input("Record audio")

if audio and st.button("Create note", icon="📝"):
    with st.spinner("Transcribing..."):
        transcription = transcribe(email=username, token=token, file=audio.read())
        st.success("Note created successfully")

notes = get("/notes", email=username, token=token)

for note in notes:
    with st.expander(note['title']):
        st.write(note['content'])

        if st.button("Delete", key=note['id'], icon="🗑️"):
            delete("/note/" + note['id'], email=username, token=token)
            st.rerun()
