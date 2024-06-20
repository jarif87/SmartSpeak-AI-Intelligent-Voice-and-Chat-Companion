import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, WebRtcMode
import numpy as np
import speech_recognition as sr
import os
import wave
import queue

# Initialize Streamlit session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Set page title and icon
st.set_page_config(page_title="Voice & Chat AI Companion", page_icon="🎙️")

# Class to handle audio processing
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.recorder = sr.Recognizer()
        self.temp_audio_file = "temp_audio.wav"
        self.q = queue.Queue()

    def recv(self, frame: np.ndarray) -> np.ndarray:
        try:
            # Convert frame to audio data
            audio_data = frame.tobytes()

            # Save the audio to a temporary file
            with wave.open(self.temp_audio_file, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(44100)
                wf.writeframes(audio_data)

            # Use SpeechRecognition to recognize speech from the temporary file
            with sr.AudioFile(self.temp_audio_file) as source:
                audio_data = self.recorder.record(source)
                user_query = self.recorder.recognize_google(audio_data)
                self.q.put(user_query)
                st.write(f"Recognized speech: {user_query}")  # Debugging output
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

# Function to process user query and generate AI response
def process_user_query(user_query):
    st.session_state.chat_history.append({"type": "human", "content": user_query})
    with st.container():
        st.write("🙂 Human: " + user_query)
    ai_response = "Hello! I am your AI assistant."
    st.session_state.chat_history.append({"type": "ai", "content": ai_response})
    with st.container():
        st.write("🤖 AI: " + ai_response)

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
        process_user_query(user_query)
elif input_method == "Voice":
    webrtc_ctx = webrtc_streamer(
        key="speech-to-text",
        mode=WebRtcMode.SENDRECV,
        audio_processor_factory=AudioProcessor,
        media_stream_constraints={"audio": True, "video": False},
        async_processing=True,
    )
    if webrtc_ctx.state.playing:
        st.write("Speak now...")  # Inform the user to speak
        if webrtc_ctx.audio_processor and not webrtc_ctx.audio_processor.q.empty():
            user_query = webrtc_ctx.audio_processor.q.get()
            if user_query:
                st.write(f"Captured query: {user_query}")  # Debugging output
                process_user_query(user_query)
            else:
                st.write("No query captured")  # Debugging output
        else:
            st.write("Audio processor not initialized or queue is empty")  # Debugging output

# Ensuring queue check for user query after speech recognition
if input_method == "Voice" and webrtc_ctx.state.playing:
    if webrtc_ctx.audio_processor and not webrtc_ctx.audio_processor.q.empty():
        user_query = webrtc_ctx.audio_processor.q.get()
        if user_query:
            st.write(f"Captured query: {user_query}")
            process_user_query(user_query)
