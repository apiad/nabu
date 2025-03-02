import streamlit as st
import time
import httpx


st.set_page_config("Nabu - Voice Notes", page_icon="🪄")


from streamlit_cookies_manager import CookieManager


def post(path, json=None, **kwargs):
    api_url = st.secrets.get("api_url")

    with httpx.Client(base_url=api_url, timeout=30) as client:
        response = client.post(path, params=kwargs, json=json)
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


def process(file, **kwargs):
    api_url = st.secrets.get("api_url")

    with httpx.Client(base_url=api_url, timeout=300) as client:
        response = client.post(
            "/process",
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

    st.info(
        f"An OTP code was sent to **{st.session_state.username}**. Check your email and paste the code here. Double check in your SPAM folder if you can't find it."
    )

    if otp:
        st.button("Verify", icon="🔑", on_click=_verify, args=(otp,))

    st.stop()


st.title("🪄 Nabu - Voice Notes")


cookies = CookieManager()


while not cookies.ready():
    time.sleep(1)


if cookies.get("token"):
    st.session_state.token = cookies.get("token")
    st.session_state.username = cookies.get("username")
    st.session_state.status = "logged"


status = st.session_state.get("status", "unknown")


if status == "unknown":
    login()

if status == "otp":
    verify()

if status != "logged":
    raise ValueError(status)


username = st.session_state.get("username")
token = st.session_state.get("token")

cookies.update(username=username, token=token, status="logged")
cookies.save()

notes = get("/notes", email=username, token=token)

new_tab, notes_tab, config_tab = st.tabs(
    ["🎤 New note", f"🗒️ My notes **`{len(notes)}`**", "⚙️ Config"]
)

config = get("/config", email=username, token=token)

with config_tab:
    with st.expander("Token (for debug purposes only, do not share!)"):
        st.code(token, language="text")

    with st.expander("Styles"):
        st.write("These are possible styles for the note transcription.")

        config["styles"] = st.data_editor(
            config["styles"], num_rows="dynamic", use_container_width=True, column_config={
                "name": st.column_config.TextColumn("Name"),
                "description": st.column_config.TextColumn("Description", width="large", ),
            }
        )

    with st.expander("Processes"):
        st.write(
            "These are post-processing tasks to apply after the note has been transcribed."
        )

        config["process"] = st.data_editor(
            config["processes"], num_rows="dynamic", use_container_width=True, column_config={
                "name": st.column_config.TextColumn("Name"),
                "prompt": st.column_config.TextColumn("Prompt", width="large"),
            }
        )

    if st.button("Save config", icon="💾"):
        post("/config", email=username, token=token, json=config)
        st.toast("Config updated in the server.")

selected_notes = []

with notes_tab:
    for note in notes:
        with st.expander(note["title"]):
            options = st.pills(
                None,
                key=note["id"] + "_options",
                label_visibility="collapsed",
                options=["Raw", "Select"],
                selection_mode="multi",
            )

            if "Raw" in options:
                st.code(note["content"], wrap_lines=True, language="markdown")
            else:
                st.write(note["content"])

            if "Select" in options:
                selected_notes.append(note)

            if st.button("Delete", key=note["id"] + "_delete", icon="🗑️"):
                delete("/note/" + note["id"], email=username, token=token)
                st.rerun()

with new_tab:
    upload = st.toggle("Upload existing audio")

    if upload:
        audio = st.file_uploader(
            "Upload audio file", ["wav", "mp3", "aac", "ogg", "m4a"]
        )
    else:
        audio = st.audio_input("Record new audio note")

    with st.expander("Configure note processing options"):
        mode = st.pills(
            "Mode",
            ["Transcription", "Instruction"],
            default="Transcription",
            help="Use **Transcription** to get a cleaned up transcription of the audio, or **Instruction** to get a response to a specific prompt.",
        )
        style = st.pills(
            "Style",
            [s["name"] for s in config["styles"]],
            default="Plain",
            help="Select one style for the generated note. Define styles in the **Config** tab.",
        )
        processing = st.pills(
            "Processing",
            [p["name"] for p in config["processes"]],
            selection_mode="multi",
            help="Apply one or more post-processing to the note. Define them in the **Config** tab.",
        )

        if selected_notes:
            st.info(f"Using {len(selected_notes)} additional notes for context.")

    if audio and st.button("Create note", icon="📝"):
        with st.spinner("Transcribing..."):
            transcription = process(
                email=username,
                token=token,
                style=style,
                mode=mode.lower(),
                processes=",".join(processing),
                file=audio.read(),
            )

            st.success(
                "The note has been created. You can review it below, or recreate (a new note) in a different style or with additional processing."
            )

            with st.container(border=True):
                st.write("### " + transcription["title"])
                st.write(transcription["content"])
                st.toast("Note created successfully")


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
        "Pack",
        ["100 Credits", "250 Credits", "500 Credits", "1000 Credits", "10000 Credits"],
        index=0,
    )

    st.link_button(
        f"Buy a {pack} Pack",
        f"https://apiad.gumroad.com/l/nabu-{pack.split()[0]}?wanted=true",
        icon="💸",
    )

    st.write(f"#### Enter your {pack} Pack info")

    key = st.text_input("License Key")

    if st.button(f"Add {pack}", icon="💸"):
        add_credits = post(
            "/credits",
            email=username,
            token=token,
            pack=pack,
            key=key,
        )

        try:
            if add_credits["status"] == "accepted":
                st.success("Credits added successfully!")
        except:
            st.error(add_credits["detail"])
