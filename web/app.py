import streamlit as st


st.set_page_config("Nabu Audio Notes", page_icon="🔊")

audio = st.audio_input("Record audio")

if not audio:
    st.info("Record an audio to create a new note.")
    st.stop()

if st.button("Create note", icon="📝"):
    st.info("Gotcha!")
