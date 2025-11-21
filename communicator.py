import serial



ser = serial.Serial(
    port='/dev/serial0',  
    baudrate=115200,      
    timeout=1
)

def send_data_to_esp32(data):
    object_data = ""
    for label in object_target:
        if len(object_target[label]) > 1:
            object_data = object_target[label][0]
            break

    data = f"[{object_data['cx']/screen_width * 100},{object_data['cx']/screen_width * 100}]"
    ser.write(data.encode('utf-8'))
