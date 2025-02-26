import streamlit as st
import httpx


st.set_page_config("Nabu Audio Notes", page_icon="🪄")


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

new_tab, notes_tab = st.tabs(["🎤 New note", "🗒️ My notes"])

with new_tab:
    upload = st.toggle("Upload existing audio")

    if upload:
        audio = st.file_uploader(
            "Upload audio file", ["wav", "mp3", "aac", "ogg", "m4a"]
        )
    else:
        audio = st.audio_input("Record new audio note")

    if audio and st.button("Create note", icon="📝"):
        with st.spinner("Transcribing..."):
            transcription = transcribe(email=username, token=token, file=audio.read())
            st.toast("Note created successfully")

with notes_tab:
    notes = get("/notes", email=username, token=token)

    for note in notes:
        with st.expander(note["title"]):
            if st.toggle("Raw mode", key=note["id"] + "_raw"):
                st.code(note["content"], wrap_lines=True, language="markdown")
            else:
                st.write(note["content"])

            if st.button("Delete", key=note["id"] + "_delete", icon="🗑️"):
                delete("/note/" + note["id"], email=username, token=token)
                st.rerun()


def logout():
    st.session_state.pop("status")
    st.session_state.pop("username")
    st.session_state.pop("token")


with st.sidebar:
    st.button("Logout", icon="🚪", on_click=logout, use_container_width=True)

    credits = get("/credits", email=username, token=token)
    st.write(f"## **Credits**: {credits['remaining']}")

    st.write("### Add credits")

    pack = st.selectbox(
        "Pack", ["100 Credits", "250 Credits", "500 Credits", "1000 Credits", "10000 Credits"], index=0
    )

    st.link_button(
        f"Buy a {pack} Pack",
        f"https://apiad.gumroad.com/l/nabu-{pack.split()[0]}",
        icon="💸",
    )

    st.write(f"#### Enter your {pack} Pack info")

    key = st.text_input("Key", type="password")

    if st.button(f"Add {pack}", icon="💸"):
        add_credits = post(
            "/credits",
            email=username,
            token=token,
            pack=pack,
            key=key,
        )

        try:
            if add_credits['status'] == "accepted":
                st.success("Credits added successfully!")
        except:
            st.error(add_credits['detail'])
