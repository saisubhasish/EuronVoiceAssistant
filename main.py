import uvicorn
from pydantic import BaseModel
from utils import get_response_llm
from fastapi import FastAPI, HTTPException
from langchain.memory import ConversationBufferMemory

app = FastAPI()

# In-memory conversation history
memory = ConversationBufferMemory(memory_key="chat_history")

class Message(BaseModel):
    message: str

@app.post("/chat")
async def chat(message: Message):
    try:
        user_question = message.message
        response_llm = get_response_llm(user_question=user_question, memory=memory)
        return {"response": response_llm}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
if __name__ ==  "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)






# from fastapi import FastAPI, File, UploadFile
# from fastapi.responses import JSONResponse
# import uvicorn
# from pydantic import BaseModel
# from typing import Optional
# from utils import load_whisper, transcribe_audio, get_response_llm, play_text_to_speech, record_audio_chunk
# from langchain.memory import ConversationBufferMemory
# import os
# import pyaudio
# import wave
# import time

# app = FastAPI()

# chunk_file = 'temp_audio_chunk.wav'
# model = load_whisper()
# memory = ConversationBufferMemory(memory_key="chat_history")

# class AudioRequest(BaseModel):
#     user_question: Optional[str] = None
#     chat_history: Optional[str] = None

# @app.post("/record-audio/")
# async def record_audio():
#     audio = pyaudio.PyAudio()
#     stream = audio.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)

#     try:
#         record_audio_chunk(audio, stream)
#     finally:
#         stream.stop_stream()
#         stream.close()
#         audio.terminate()

#     return {"message": "Audio recorded successfully"}

# @app.post("/transcribe-audio/")
# async def transcribe_audio_endpoint(file: UploadFile = File(...)):
#     try:
#         with open(chunk_file, "wb") as buffer:
#             buffer.write(file.file.read())

#         text = transcribe_audio(model, chunk_file)

#         if text is not None:
#             return {"transcription": text}
#         else:
#             return JSONResponse(status_code=400, content={"message": "Failed to transcribe audio"})
#     finally:
#         time.sleep(1)  # Add a delay before attempting to delete the file
#         if os.path.exists(chunk_file):
#             try:
#                 os.remove(chunk_file)
#             except PermissionError:
#                 pass  # Handle the exception if needed

# @app.post("/get-response/")
# async def get_response(data: AudioRequest):
#     response_llm = get_response_llm(user_question=data.user_question, memory=memory)
#     play_text_to_speech(response_llm)
#     return {"response": response_llm}

# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)
