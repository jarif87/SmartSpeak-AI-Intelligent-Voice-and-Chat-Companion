import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
import os
import speech_recognition as sr
import numpy as np
import wave

# Load environment variables from .env file
load_dotenv()

# Configure the Google AI SDK with the API key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Set up the generative model
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    generation_config=generation_config,
)

# Initialize Streamlit session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.set_page_config(page_title="SpeakSmart Intelligent Voice and Chat Assistant", page_icon="🤖")

# Function to get response from the Gemini model
def get_response(query, chat_history):
    history = [{"parts": [{"text": msg['content']}], "role": "user" if msg['type'] == "human" else "model"} for msg in chat_history]
    chat_session = model.start_chat(history=history)
    try:
        response = chat_session.send_message(query)
        return response.text
    except genai.types.StopCandidateException as e:
        return e.candidate.text

# Function to handle voice input using uploaded file and SpeechRecognition
def handle_voice_input(uploaded_file):
    if uploaded_file is not None:
        try:
            with open("temp_audio.wav", "wb") as f:
                f.write(uploaded_file.getbuffer())

            r = sr.Recognizer()
            with sr.AudioFile("temp_audio.wav") as source:
                audio_data = r.record(source)
                user_query = r.recognize_google(audio_data)
            return user_query
        except sr.UnknownValueError:
            st.write("Sorry, I couldn't understand what you said.")
            return None
        except sr.RequestError:
            st.write("Sorry, I'm having trouble accessing the Google API.")
            return None
        except Exception as e:
            st.error(f"Error handling voice input: {e}")
            return None
        finally:
            if os.path.exists("temp_audio.wav"):
                os.remove("temp_audio.wav")

# Conversation rendering
for message in st.session_state.chat_history:
    if message['type'] == "human":
        with st.chat_message("Human"):
            st.markdown(message['content'])
    else:
        with st.chat_message("AI"):
            st.markdown(message['content'])

# User input - handle both text and voice
input_method = st.selectbox("Select input method", ["Text", "Voice"])

user_query = None
if input_method == "Text":
    user_query = st.text_input("Your Message")
    st.write("")  # To clear any previous "Speak now..." message
elif input_method == "Voice":
    uploaded_file = st.file_uploader("Upload your audio file", type=["wav"])
    if uploaded_file is not None:
        user_query = handle_voice_input(uploaded_file)
        st.write("")  # To clear any previous "Speak now..." message

if user_query:
    st.session_state.chat_history.append({"type": "human", "content": user_query})

    with st.chat_message("Human"):
        st.markdown(user_query)

    with st.chat_message("AI"):
        ai_response = get_response(user_query, st.session_state.chat_history)
        st.markdown(ai_response)

    st.session_state.chat_history.append({"type": "ai", "content": ai_response})
