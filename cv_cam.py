import torch
import cv2
import time
import serial
import time

object_target = ["plastic", "paper", "glass", "metal"]

object_id = {
    "plastic" : 1, 
    "paper" : 2, 
    "glass" : 3, 
    "metal" : 4
}

object_chache = {
    "plastic" : [],
    "paper" : [],
    "glass" : [],
    "metal": [],    
}

ser = serial.Serial(
    port='/dev/serial0',  
    baudrate=115200,      
    timeout=1
)

model = torch.hub.load(
    'ultralytics/yolov5', 
    'custom', 
    path='/weights/trash.pt',  
    source='local'  
)
model.conf = 0.4  

cap = cv2.VideoCapture(0)
screen_width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
screen_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

target_fps = 5
delay = 1 / target_fps
prev_time = 0


def object_similarity(data1, data2):
    w1 = (data1['xmax'] - data1['xmin'])
    h1 = (data1['ymax'] - data1['ymin'])
    w2 = (data2['xmax'] - data2['xmin'])
    h2 = (data2['ymax'] - data2['ymin'])

    dimention_similarity = (1-abs(w1-w2)/w1) * (1-abs(h1-h2)/h1)
    position_similarity = (1 - (abs(data1['cx']-data2['cx']) * abs(data1['cy']-data2['cy']))/screen_width))
    
    return dimention_similarity * position_similarity



def update_object_chache(results):
    df = results.pandas().xyxy[0]

    for _, row in df.iterrows():
        label = row['name']
        xmin, ymin, xmax, ymax = row['xmin'], row['ymin'], row['xmax'], row['ymax']

        cx = (xmin + xmax) / 2
        cy = (ymin + ymax) / 2

        obj_info = {
            'xmin': float(xmin),
            'xmax': float(xmax),
            'ymin': float(ymin),
            'ymax': float(ymax),
            'cx': float(cx),
            'cy': float(cy)
        }
        
        if label in objects_chache:
            objects_dict[label].append(obj_info)


def send_data_to_esp32():
    object_data = ""
    for label in object_target:
        if len(object_target[label]) > 1
            object_data = object_target[label][0]
            break

    data = f"[{object_data['cx']/screen_width * 100},{object_data['cx']/screen_width * 100}]"
    ser.write(data.encode('utf-8'))


while True:
    ret, frame = cap.read()
    if not ret:
        break

    current_time = time.time()
    elapsed = current_time - prev_time

    if elapsed > delay:
        prev_time = current_time

        results = model(frame)
        update_object_chache(results)
        send_data_to_esp32()   

        labeled_frame = results.render()[0]

        cv2.imshow('YOLO Detection', labeled_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

