from flask import Flask, render_template, request, jsonify
from model import Model
import cv2
import numpy as np
import base64
import os
from datetime import datetime
from threading import Thread, Lock
import time

app = Flask(__name__)
model = Model()
violence_labels = {'fight on a street', 'street violence', 'violence in office', 'fire in office'}
recording = False
recording_lock = Lock()
out = None
record_start_time = None
record_folder = "recordings"
os.makedirs(record_folder, exist_ok=True)

# Save frames to video file if needed
def save_video(frames, timestamp):
    filename = os.path.join(record_folder, f"violence_{timestamp}.mp4")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    height, width, _ = frames[0].shape
    out = cv2.VideoWriter(filename, fourcc, 10, (width, height))
    for f in frames:
        out.write(f)
    out.release()


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/predict', methods=['POST'])
def predict():
    global recording, out, record_start_time

    data = request.json
    image_data = data['image']
    image_data = base64.b64decode(image_data.split(',')[1])
    np_arr = np.frombuffer(image_data, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    # Add timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cv2.putText(frame, timestamp, (10, 25), cv2.FONT_HERSHEY_SIMPLEX,
                0.8, (255, 255, 255), 2, cv2.LINE_AA)

    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    prediction = model.predict(image_rgb)
    label = prediction['label']
    confidence = prediction['confidence']

    response = {
        "label": label,
        "confidence": round(confidence, 2),
        "violence": label in violence_labels
    }

    # Recording logic
    with recording_lock:
        if label in violence_labels:
            if not recording:
                recording = True
                record_start_time = time.time()
                app.frames_buffer = [frame]
            else:
                app.frames_buffer.append(frame)
        else:
            if recording:
                duration = time.time() - record_start_time
                if duration >= 3:  # save if >= 3 sec
                    Thread(target=save_video,
                           args=(app.frames_buffer.copy(),
                                 datetime.now().strftime('%Y%m%d_%H%M%S'))).start()
                recording = False
                app.frames_buffer = []

    return jsonify(response)


if __name__ == '__main__':
    app.frames_buffer = []
    app.run(host='0.0.0.0', port=5000, debug=True)



