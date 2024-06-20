import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, WebRtcMode
import numpy as np
import speech_recognition as sr
import os
import wave
import asyncio

# Initialize Streamlit session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Set page title and icon
st.set_page_config(page_title="Voice & Chat AI Companion", page_icon="🎙️")

# Function to get audio from WebRTC
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.recorder = sr.Recognizer()
        self.temp_audio_file = "temp_audio.wav"
        self.user_query = None

    def recv(self, frame: np.ndarray) -> np.ndarray:
        try:
            st.write("Processing audio...")
            # Save the audio to a temporary file
            self.write_audio(self.temp_audio_file, frame)
            
            # Use SpeechRecognition to recognize speech from the temporary file
            with sr.AudioFile(self.temp_audio_file) as source:
                audio_data = self.recorder.record(source)
                self.user_query = self.recorder.recognize_google(audio_data)
            st.write(f"Recognized speech: {self.user_query}")
            return frame
        except sr.UnknownValueError:
            st.write("Sorry, I couldn't understand what you said.")
            return frame
        except sr.RequestError:
            st.write("Sorry, I'm having trouble accessing the Google API.")
            return frame
        except PermissionError:
            st.error("Permission error accessing audio device.")
            return frame
        except Exception as e:
            st.error(f"Error handling voice input: {e}")
            return frame
        finally:
            # Delete the temporary audio file if it exists
            if os.path.exists(self.temp_audio_file):
                os.remove(self.temp_audio_file)

    def write_audio(self, filename, data):
        try:
            data = (data * np.iinfo(np.int16).max).astype(np.int16)
            wf = wave.open(filename, 'wb')
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(44100)
            wf.writeframes(data.tobytes())
            wf.close()
        except Exception as e:
            st.error(f"Error writing audio: {e}")

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

user_query = None
if input_method == "Text":
    user_query = st.text_input("Your Message")
elif input_method == "Voice":
    webrtc_ctx = webrtc_streamer(
        key="speech-to-text",
        mode=WebRtcMode.SENDRECV,
        audio_processor_factory=AudioProcessor,
        media_stream_constraints={"audio": True, "video": False},
        async_processing=True,
    )

    # Check if audio has been processed
    if webrtc_ctx.state.playing:
        if webrtc_ctx.audio_processor:
            user_query = webrtc_ctx.audio_processor.user_query
            st.write(f"Captured query: {user_query}")

# Process user query and AI response
if user_query:
    st.session_state.chat_history.append({"type": "human", "content": user_query})

    with st.container():
        st.write("🙂 Human: " + user_query)

    # Simulate AI response for demonstration purposes
    ai_response = "Hello! I am your AI assistant."
    st.session_state.chat_history.append({"type": "ai", "content": ai_response})

    with st.container():
        st.write("🤖 AI: " + ai_response)
