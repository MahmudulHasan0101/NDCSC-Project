import sounddevice as sd
from vosk import Model, KaldiRecognizer
import json
import queue
import threading

model = Model("./models/vosk-model-small-en-us-0.15")
rec = KaldiRecognizer(model, 16000)
q = queue.Queue()

def callback(indata, frames, time, status):
    q.put(bytes(indata))

def recognize_loop(dispatcher):
    while True:
        data = q.get()
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            if result.get("text"):
                dispatcher(result["text"])

def demo_dispatcher(text):
    print(text)

stream = sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                           channels=1, callback=callback)

def start(dispatcher):
    stream.start()
    print("INFO: recognition thread started")
    threading.Thread(target=recognize_loop, args=(dispatcher,), daemon=True).start()

def end():
    stream.stop()
    stream.close()

if __name__ == "__main__":
    start(demo_dispatcher)

    print("Press Enter to stop the loop.")
    while True:
        if input("Press Enter to exit (or type anything else to continue): ") == "":
            break

    end()

