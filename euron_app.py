import os
import base64   # Display image to base64
import logging
import pyaudio  # To play and record audio
import streamlit as st
from langchain.memory import ConversationBufferMemory   # To store messages and extracts messages from a variable

from src.logger import logger
from utils import record_audio_chunk, transcribe_audio, get_response_llm, play_text_to_speech, load_whisper


chunk_file = 'temp_audio_chunk.wav'
model = load_whisper()

logging.basicConfig(level=logging.INFO)

# Streamlit Page Configuration
st.set_page_config(
    page_title="Euron Bot - An Intelligent Streamlit Assistant",
    page_icon="images/euron_bot.png",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": """
            ## Euron Voice Assistant
            
            **GitHub**: https://github.com/saisubhasish/EuronVoiceAssistant
            
            The AI Assistant aims to help users manage daily tasks, set reminders, 
            control smart home devices, and provide information on demand. This versatile 
            voice assistant has been designed to integrate seamlessly with smart home devices 
            and calendar apps, ensuring efficient task management and accurate, timely information 
            for users. The assistant is trained on the latest updates and documentation relevant to 
            smart home technology and task management applications.
        """
    }
)

# Streamlit Updates and Expanders
st.title("Euron Voice Assistant")

def img_to_base64(image_path):
    """Convert image to base64"""
    with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()

def main():
    """
    Display Streamlit updates and handle the chat interface.
    """
    
    # Inject custom CSS for glowing border effect
    st.markdown(
        """
        <style>
        .cover-glow {
            width: 100%;
            height: auto;
            padding: 3px;
            box-shadow: 
                0 0 5px #330000,
                0 0 10px #660000,
                0 0 15px #990000,
                0 0 20px #CC0000,
                0 0 25px #FF0000,
                0 0 30px #FF3333,
                0 0 35px #FF6666;
            position: relative;
            z-index: -1;
            border-radius: 30px;  /* Rounded corners */
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Function to convert image to base64
    def img_to_base64(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()

    # Load and display sidebar image with glowing effect
    img_path = "images/euron_bot.png"
    img_base64 = img_to_base64(img_path)
    st.sidebar.markdown(
        f'<img src="data:image/png;base64,{img_base64}" class="cover-glow">',
        unsafe_allow_html=True,
    )
    st.sidebar.markdown("---")
    
    # Sidebar for Mode Selection
    mode = st.sidebar.radio("Select Mode:", options=["Talk with Euron Assistant"], index=0)
    st.sidebar.markdown("---")
    # Toggle checkbox in the sidebar for basic interactions
    show_basic_info = st.sidebar.toggle("Show Basic Interactions", value=True)

    # Display the st.info box if the checkbox is checked
    if show_basic_info:
        st.sidebar.markdown("""
        ### Basic Interactions
        - **Ask About Streamlit**: Ask your questions about Streamlit's latest updates, features, or issues.
        - **Search for Code**: Use keywords like 'code example', 'syntax', or 'how-to' to get relevant code snippets.
        - **Navigate Updates**: Switch to 'Updates' mode to browse the latest Streamlit updates in detail.
        """)

    # Add another toggle checkbox in the sidebar for advanced interactions
    show_advanced_info = st.sidebar.toggle("Show Advanced Interactions", value=False)

    # Display the st.info box if the checkbox is checked
    if show_advanced_info:
        st.sidebar.markdown("""
        ### Advanced Interactions
        - **Generate an App**: Use keywords like **generate app**, **create app** to get a basic Streamlit app code.
        - **Code Explanation**: Ask for **code explanation**, **walk me through the code** to understand the underlying logic of Streamlit code snippets.
        - **Project Analysis**: Use **analyze my project**, **technical feedback** to get insights and recommendations on your current Streamlit project.
        - **Debug Assistance**: Use **debug this**, **fix this error** to get help with troubleshooting issues in your Streamlit app.
        """)

    st.sidebar.markdown("---")
    # Load image and convert to base64
    img_path = "images/euron.png"  # Replace with the actual image path
    img_base64 = img_to_base64(img_path)



    # Display image with custom CSS class for glowing effect
    st.sidebar.markdown(
        f'<img src="data:image/png;base64,{img_base64}" class="cover-glow">',
        unsafe_allow_html=True,
    )
    
    # Handle Chat and Update Modes
    if mode == "Talk with Euron Assistant":
        memory = ConversationBufferMemory(memory_key="chat_history")

        if st.button("Start Recording"):
            while True:
                # Audio Stream Initialization
                audio = pyaudio.PyAudio()
                stream = audio.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)

                # Record and save audio chunk
                record_audio_chunk(audio, stream)

                text = transcribe_audio(model, chunk_file)

                if text is not None:
                    st.markdown(
                        f'<div style="background-color: #f0f0f0; padding: 10px; border-radius: 5px;">Customer 👤: {text}</div>',
                        unsafe_allow_html=True)
                    logger.info(f"User Question: {text}")

                    os.remove(chunk_file)

                    response_llm = get_response_llm(user_question=text, memory=memory)
                    st.markdown(
                        f'<div style="background-color: #f0f0f0; padding: 10px; border-radius: 5px;">AI Assistant 🤖: {response_llm}</div>',
                        unsafe_allow_html=True)

                    logger.info(f"AI Response: {response_llm}\n")

                    play_text_to_speech(text=response_llm)
                else:
                    stream.stop_stream()
                    stream.close()
                    audio.terminate()
                    logger.info("End Audio Stream as user did not say anything")
                    break  # Exit the while loop
            logger.info("End Conversation")


if __name__ == "__main__":
    main()