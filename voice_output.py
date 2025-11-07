import numpy as np
import sounddevice as sd
from piper.voice import PiperVoice

model_path = "./voices/en_GB-alan-medium.onnx"

def speak(text):
    voice = PiperVoice.load(model_path)
    chunks = []
    for chunk in voice.synthesize(text):
        chunks.append(chunk.audio_int16_bytes)


    all_bytes = b"".join(chunks)
    audio = np.frombuffer(all_bytes, dtype=np.int16)

    sd.play(audio, samplerate=voice.config.sample_rate)


if __name__ == "__main__":
    speak(input("Enter text to speak: "))
    sd.wait()

