import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, WebRtcMode
import numpy as np
import speech_recognition as sr
import queue

# Initialize Streamlit session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Set page title and icon
st.set_page_config(page_title="Voice & Chat AI Companion", page_icon="🎙️")

# Class to handle audio processing
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        super().__init__()
        self.recognizer = sr.Recognizer()
        self.q = queue.Queue()

    def recv(self, frame: np.ndarray) -> np.ndarray:
        try:
            # Convert frame to audio data
            audio_data = frame.flatten().astype(np.int16)

            # Recognize speech from the audio data
            with sr.AudioData(audio_data, 44100) as source:
                audio_text = self.recognizer.recognize_google(source)
                self.q.put(audio_text)
                st.write(f"Recognized speech: {audio_text}")  # Debugging output

            return frame

        except sr.UnknownValueError:
            st.warning("Sorry, I couldn't understand what you said.")
            return frame
        except sr.RequestError:
            st.error("Sorry, I'm having trouble accessing the Google API.")
            return frame
        except Exception as e:
            st.error(f"Error handling voice input: {e}")
            return frame

# Render conversation history
for message in st.session_state.chat_history:
    if message['type'] == "human":
        with st.container():
            st.write("🙂 Human: " + message['content'])
    else:
        with st.container():
            st.write("🤖 AI: " + message['content'])

# User input - handle both text and voice
input_method = st.selectbox("Select input method", ["Text", "Voice"])

if input_method == "Text":
    user_query = st.text_input("Your Message")
    if user_query:
        st.session_state.chat_history.append({"type": "human", "content": user_query})
        with st.container():
            st.write("🙂 Human: " + user_query)
elif input_method == "Voice":
    webrtc_ctx = webrtc_streamer(
        key="speech-to-text",
        mode=WebRtcMode.SENDRECV,
        audio_processor_factory=AudioProcessor,
        async_processing=True,
    )

    if webrtc_ctx.audio_processor and not webrtc_ctx.audio_processor.q.empty():
        user_query = webrtc_ctx.audio_processor.q.get()
        if user_query:
            st.session_state.chat_history.append({"type": "human", "content": user_query})
            with st.container():
                st.write("🙂 Human: " + user_query)

# Simulate AI response for demonstration purposes
ai_response = "Hello! I am your AI assistant."
st.session_state.chat_history.append({"type": "ai", "content": ai_response})
with st.container():
    st.write("🤖 AI: " + ai_response)
