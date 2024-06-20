import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, WebRtcMode
import speech_recognition as sr
import os
from dotenv import load_dotenv
import google.generativeai as genai


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

class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.audio_data = None

    def recv(self, frame):
        audio = frame.to_ndarray()
        try:
            audio = sr.AudioData(audio.tobytes(), frame.sampling_rate, frame.sample_width)
            user_query = self.recognizer.recognize_google(audio)
            st.session_state.chat_history.append({"type": "human", "content": user_query})
            ai_response = get_response(user_query, st.session_state.chat_history)
            st.session_state.chat_history.append({"type": "ai", "content": ai_response})
            st.experimental_rerun()
        except sr.UnknownValueError:
            st.write("Sorry, I couldn't understand what you said.")
        except sr.RequestError:
            st.write("Sorry, I'm having trouble accessing the Google API.")
        except Exception as e:
            st.error(f"Error handling voice input: {e}")
        return frame

# Conversation rendering
for message in st.session_state.chat_history:
    if message['type'] == "human":
        with st.chat_message("Human"):
            st.markdown(message['content'])
    else:
        with st.chat_message("AI"):
            st.markdown(message['content'])

# WebRTC for real-time voice input
webrtc_streamer(key="voice_input", mode=WebRtcMode.SENDRECV, audio_processor_factory=AudioProcessor)

# User input - handle text input
user_query = st.text_input("Your Message")
if user_query:
    st.session_state.chat_history.append({"type": "human", "content": user_query})
    ai_response = get_response(user_query, st.session_state.chat_history)
    st.session_state.chat_history.append({"type": "ai", "content": ai_response})
    st.experimental_rerun()
