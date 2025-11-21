import cv_cam
import speech_recognition as sr
import nlp
import time

target_fps = 5
delay = 1 / target_fps
prev_time = 0



def voice_input_dispatcher(text):
    response = nlp.run(text)
    print(f"RECOGNIZED SPEECH: {text} OUTPUT: {response}")
    
   
sr.start(voice_input_dispatcher) 


print("INFO: Entering main loop")
while True:
    current_time = time.time()
    elapsed = current_time - prev_time

    if elapsed > delay:
        cv_cam.update()
        print("tick")
        prev_time = current_time


sr.end()
cv_cam.end()
nlp.end()

