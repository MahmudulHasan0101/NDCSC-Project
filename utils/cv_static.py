import torch
import cv2
import time

object_target = ["plastic", "paper", "glass", "metal"]

object_chache = {
    "plastic" : [],
    "paper" : [],
    "glass" : [],
    "metal": [],    
}

def object_similarity(data1, data2):
    w1 = (data1['xmax'] - data1['xmin'])
    h1 = (data1['ymax'] - data1['ymin'])
    w2 = (data2['xmax'] - data2['xmin'])
    h2 = (data2['ymax'] - data2['ymin'])

    dimention_similarity = (1-abs(w1-w2)/w1) * (1-abs(h1-h2)/h1)
    position_similarity = (1 - (abs(data1['cx']-data2['cx']) * abs(data1['cy']-data2['cy']) )/screen_width)
    
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
        
        if label in object_chache:
            object_chache[label].append(obj_info)


model = torch.hub.load(
    'yolov5', 
    'custom', 
    path='./weights/trash.pt',  
    source='local'  
)
model.conf = 0.4  

frame = cv2.imread("dataset/test/sample3.jpeg")
results = model(frame)

update_object_chache(results)
print(object_chache)

labeled_frame = results.render()[0]
cv2.imshow('YOLO Detection', labeled_frame)

delay(10)
cv2.destroyAllWindows()

