

target_fps = 5
delay = 1 / target_fps
prev_time = 0

while True:
    current_time = time.time()
    elapsed = current_time - prev_time

    if elapsed > delay:
        prev_time = current_time

        

