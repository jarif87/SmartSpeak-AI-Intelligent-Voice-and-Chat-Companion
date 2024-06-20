import streamlit as st
import os
import sounddevice as sd
import numpy as np
import speech_recognition as sr
import wave

# Initialize Streamlit session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.set_page_config(page_title="Voice & Chat AI Companion", page_icon=":dragon:")
st.title("SpeakSmart Intelligent Voice and Chat Assistant")

# Function to handle voice input using sounddevice and SpeechRecognition
def handle_voice_input():
    temp_audio_file = "temp_audio.wav"

    try:
        st.write("Speak now...")
        fs = 44100  # Sample rate
        seconds = 5  # Duration of recording

        # Ensure the selected audio device is available and accessible
        devices = sd.query_devices()
        st.write(devices)  # Debugging output

        if devices:
            device_id = devices[0]['index']  # Use the first available device (modify as needed)
        else:
            st.error("No audio input devices found.")
            return None

        myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=2, device=device_id)
        sd.wait()  # Wait until recording is finished

        # Save the audio to the temporary file
        write_audio(temp_audio_file, myrecording, fs)

        # Use SpeechRecognition to recognize speech from the temporary file
        r = sr.Recognizer()
        with sr.AudioFile(temp_audio_file) as source:
            audio_data = r.record(source)  # Read the entire audio file
            user_query = r.recognize_google(audio_data)
        return user_query
    except sr.UnknownValueError:
        st.write("Sorry, I couldn't understand what you said.")
        return None
    except sr.RequestError:
        st.write("Sorry, I'm having trouble accessing the Google API.")
        return None
    except PermissionError:
        st.error("Permission error accessing audio device.")
        return None
    except Exception as e:
        st.error(f"Error handling voice input: {e}")
        return None
    finally:
        # Delete the temporary audio file if it exists
        if os.path.exists(temp_audio_file):
            os.remove(temp_audio_file)

# Helper function to write audio to file using wave module
def write_audio(filename, data, fs):
    try:
        # Ensure data is in the correct format
        if data.dtype != np.int16:
            data = (data * np.iinfo(np.int16).max).astype(np.int16)

        # Write NumPy array to WAV file
        wf = wave.open(filename, 'wb')
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(fs)
        wf.writeframes(data.tobytes())
        wf.close()
    except Exception as e:
        st.error(f"Error writing audio: {e}")

# Render conversation history
for message in st.session_state.chat_history:
    if message['type'] == "human":
        with st.chat_message("Human"):
            st.markdown(message['content'])
    else:
        with st.chat_message("AI"):
            st.markdown(message['content'])

# User input - handle both text and voice
input_method = st.selectbox("Select input Text or Voice method", ["Text", "Voice"])

user_query = None
if input_method == "Text":
    user_query = st.text_input("Your Message")
    st.write("")  # Clear any previous "Speak now..." message
elif input_method == "Voice":
    user_query = handle_voice_input()
    st.write("")  # Clear any previous "Speak now..." message

# Display voice icon if voice input is selected
if input_method == "Voice":
    st.write("🎤 Voice Input")

# Process user query and AI response
if user_query:
    st.session_state.chat_history.append({"type": "human", "content": user_query})

    with st.chat_message("Human"):
        st.markdown(user_query)

    # Mock AI response for demonstration
    ai_response = "Hello! I am your AI assistant."
    st.session_state.chat_history.append({"type": "ai", "content": ai_response})

    with st.chat_message("AI"):
        st.markdown(ai_response)
