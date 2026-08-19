"""
Speech-to-Text service utilizing faster-whisper on CPU.
"""
import os
from faster_whisper import WhisperModel

# Use base to minimize memory usage since Ollama uses the GPU
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL", "base")

_model = None

def get_whisper_model():
    global _model
    if _model is None:
        # Load on CPU with int8 to conserve resources
        print(f"Loading Whisper model: {WHISPER_MODEL_SIZE} on CPU (int8)...")
        _model = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
        print("Whisper model loaded.")
    return _model

def transcribe_audio(file_path: str) -> str:
    """
    Transcribes audio using faster-whisper.
    """
    model = get_whisper_model()
    segments, info = model.transcribe(file_path, beam_size=5)
    
    transcript = ""
    for segment in segments:
        transcript += segment.text + " "
        
    return transcript.strip()
