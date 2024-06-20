import streamlit as st
import sounddevice as sd
import numpy as np
import speech_recognition as sr
import os
import wave

# Initialize Streamlit session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Set page title and icon
st.set_page_config(page_title="Voice & Chat AI Companion", page_icon="🎙️")

# Function to handle voice input
def handle_voice_input():
    temp_audio_file = "temp_audio.wav"

    try:
        st.write("Speak now...")
        
        # Query available audio input devices
        devices = sd.query_devices()
        st.write(devices)  # Debugging output
        
        if devices:
            # Use the first available input device
            input_devices = [device for device in devices if device['max_input_channels'] > 0]
            if input_devices:
                device_id = input_devices[0]['index']
                st.write(f"Using audio input device: {input_devices[0]['name']}")
            else:
                st.error("No available audio input devices with input channels found.")
                return None
        else:
            st.error("No audio input devices found.")
            return None
        
        fs = 44100  # Sample rate
        seconds = 5  # Duration of recording
        
        myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=2, device=device_id)
        sd.wait()  # Wait until recording is finished
        
        # Save the audio to a temporary file
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
        with st.container():
            st.write("Human: " + message['content'])
    else:
        with st.container():
            st.write("AI: " + message['content'])

# User input - handle both text and voice
input_method = st.selectbox("Select input method", ["Text", "Voice"])

user_query = None
if input_method == "Text":
    user_query = st.text_input("Your Message")
elif input_method == "Voice":
    user_query = handle_voice_input()

# Process user query and AI response
if user_query:
    st.session_state.chat_history.append({"type": "human", "content": user_query})

    with st.container():
        st.write("Human: " + user_query)

    # Simulate AI response for demonstration purposes
    ai_response = "Hello! I am your AI assistant."
    st.session_state.chat_history.append({"type": "ai", "content": ai_response})

    with st.container():
        st.write("AI: " + ai_response)
