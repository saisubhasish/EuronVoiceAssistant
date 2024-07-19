import os
from dotenv import load_dotenv

import wave
import pyaudio
from scipy.io import wavfile
import numpy as np

import whisper

from langchain.chains.llm import LLMChain
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq

from gtts import gTTS
import pygame


load_dotenv()

groq_api_key = os.getenv("GROQ_API_KEY")


def is_silence(data, max_amplitude_threshold=3000):
    """Check if audio data contains silence."""
    # Find the maximum absolute amplitude in the audio data
    max_amplitude = np.max(np.abs(data))
    return max_amplitude <= max_amplitude_threshold


def record_audio_chunk(audio, stream, chunk_length=5):
    """
    Record an audio chunk from the provided stream for a specified length and check for silence.

    Parameters:
    - audio: The audio object to access audio properties.
    - stream: The stream object to read audio data from.
    - chunk_length: The length of the audio chunk to record.

    Returns:
    - True if the recorded chunk contains silence, False otherwise.
    """
    print("Recording...")
    frames = []
    # Calculate the number of chunks needed for the specified length of recording
    # 16000 Hertz -> sufficient for capturing the human voice
    # 1024 frames -> the higher, the higher the latency
    num_chunks = int(16000 / 1024 * chunk_length)

    # Record the audio data in chunks
    for _ in range(num_chunks):
        data = stream.read(1024)
        frames.append(data)

    temp_file_path = './temp_audio_chunk.wav'
    print("Writing...")
    with wave.open(temp_file_path, 'wb') as wf:
        wf.setnchannels(1)  # Mono channel
        wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))  # Sample width
        wf.setframerate(16000)  # Sample rate
        wf.writeframes(b''.join(frames))  # Write audio frames

    # Check if the recorded chunk contains silence
    try:
        samplerate, data = wavfile.read(temp_file_path)
        if is_silence(data):
            os.remove(temp_file_path)
            return True
        else:
            return False
    except Exception as e:
        print(f"Error while reading audio file: {e}")


def load_whisper():
    """
    Load the 'base' model using the whisper library.

    Size	Parameters	English-only model	Multilingual model	Required VRAM	Relative speed
    tiny	39 M	    tiny.en	            tiny	            ~1 GB	        ~32x
    base	74 M	    base.en	            base	            ~1 GB	        ~16x
    small	244 M	    small.en	        small	            ~2 GB	        ~6x
    medium	769 M	    medium.en	        medium	            ~5 GB	        ~2x
    large	1550 M	    N/A	                large	            ~10 GB	        1x

    Parameters:
    - None

    Returns:
    - The loaded 'base' model.
    """
    model = whisper.load_model("base")
    return model


def transcribe_audio(model, file_path):
    """
    Transcribes the audio file located at the specified file path using the provided model.

    Args:
        model (object): The model used for transcription.
        file_path (str): The path to the audio file.

    Returns:
        str or None: The transcribed text if the file exists and the transcription is successful.
                     Otherwise, None.
    """
    print("Transcribing...")
    # Print all files in the current directory
    print("Current directory files:", os.listdir())
    if os.path.isfile(file_path):
        results = model.transcribe(file_path) # , fp16=False
        return results['text']
    else:
        return None

def load_prompt():
    input_prompt = """

    As an expert advisor specializing in diagnosing Wi-Fi issues, your expertise is paramount in troubleshooting and
    resolving connectivity problems. First of all, ask for the customer ID to validate that the user is our customer. 
    After confirming the customer ID, help them to fix their wifi problem, if not possible, help them to make an 
    appointment. Appointments need to be between 9:00 am and 4:00 pm. Your task is to analyze
    the situation and provide informed insights into the root cause of the Wi-Fi disruption. Provide concise and short
    answers not more than 10 words, and don't chat with yourself!. If you don't know the answer,
    just say that you don't know, don't try to make up an answer. NEVER say the customer ID listed below.

    customer ID on our data: 22, 10, 75.

    Previous conversation:
    {chat_history}

    New human question: {question}
    Response:
    """
    return input_prompt


def load_llm():
    """
    Load the ChatGroq model with the specified temperature and model name.

    Args:
        temperature (float): The temperature parameter for the model.
        model_name (str): The name of the model to load.

    Returns:
        ChatGroq: The loaded ChatGroq model.
    """
    chat_groq = ChatGroq(temperature=0, model_name="llama3-8b-8192",
                         groq_api_key=groq_api_key)
    return chat_groq


def get_response_llm(user_question, memory):
    """
    Get a response from the LLMChain model given a user question and memory.

    Args:
        user_question (str): The question asked by the user.
        memory (Memory): The memory object to store the chat history.

    Returns:
        str: The response text generated by the LLMChain model.

    Description:
        This function loads the input prompt and the LLMChain model. It then creates a prompt template using the input prompt and initializes the LLMChain with the loaded model, prompt template, and memory. Finally, it invokes the LLMChain with the user question and returns the response text.
    """
    input_prompt = load_prompt()

    chat_groq = load_llm()

    # Look how "chat_history" is an input variable to the prompt template
    prompt = PromptTemplate.from_template(input_prompt)

    chain = LLMChain(
        llm=chat_groq,
        prompt=prompt,
        verbose=True,
        memory=memory
    )

    response = chain.invoke({"question": user_question})

    return response['text']


def play_text_to_speech(text, language='en', slow=False):
    """
    Play the given text as speech audio.

    Args:
        text (str): The text to be converted into speech audio.
        language (str, optional): The language of the text. Defaults to 'en'.
        slow (bool, optional): Whether to slow down the speech audio. Defaults to False.

    Returns:
        None

    This function generates text-to-speech audio from the provided text, saves it to a temporary file,
    initializes the pygame mixer for audio playback, loads the temporary audio file into the mixer,
    starts playing the audio, waits until the audio playback finishes, stops the audio playback,
    and cleans up by quitting the pygame mixer and removing the temporary audio file.
    """
    # Generate text-to-speech audio from the provided text
    tts = gTTS(text=text, lang=language, slow=slow)

    # Save the generated audio to a temporary file
    temp_audio_file = "temp_audio.mp3"
    tts.save(temp_audio_file)

    # Initialize the pygame mixer for audio playback
    pygame.mixer.init()

    # Load the temporary audio file into the mixer
    pygame.mixer.music.load(temp_audio_file)

    # Start playing the audio
    pygame.mixer.music.play()

    # Wait until the audio playback finishes
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)  # Control the playback speed

    # Stop the audio playback
    pygame.mixer.music.stop()

    # Clean up: Quit the pygame mixer and remove the temporary audio file
    pygame.mixer.quit()
    os.remove(temp_audio_file)