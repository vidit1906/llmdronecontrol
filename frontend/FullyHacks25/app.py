import cv2
import argparse
import os
import re
import threading
import time
import signal
import json
from ollama import chat, ChatResponse
from djitellopy import Tello
from flask import Flask, Response, request, jsonify
import numpy as np
import imutils

# ---------------------------- CONFIG ----------------------------
detection_enabled = True

parser = argparse.ArgumentParser()
parser.add_argument("--port", type=int, default=5001)
parser.add_argument("--host", type=str, default="0.0.0.0")
parser.add_argument("--no-local-display", action="store_true")
args = parser.parse_args()

# Serve React static files from build
app = Flask(__name__, static_folder='frontend/build', static_url_path='/')

# ------------------------- DRONE SETUP -------------------------
print("Connecting to Tello drone...")
tello = Tello()
tello.connect()
print("Battery:", tello.get_battery())
tello.streamon()

print("[INFO] loading model...")
net = cv2.dnn.readNetFromCaffe('MobileNetSSD_deploy.prototxt.txt', 'MobileNetSSD_deploy.caffemodel')
CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
           "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
           "dog", "horse", "motorbike", "person", "pottedplant", "sheep",
           "sofa", "train", "tvmonitor"]
COLORS = np.random.uniform(0, 255, size=(len(CLASSES), 3))

# Load Tello commands
def read_tello_commands_file():
    try:
        with open("tello.txt", "r") as file:
            return file.read()
    except FileNotFoundError:
        return "..."

tello_commands = read_tello_commands_file()

chat_history = [{
    "role": "system",
    "content": (
        "You are an assistant helping me control an actual Tello drone using its Python SDK (djitellopy)...\n\n"
        f"{tello_commands}"
    ),
}]

def ask(prompt: str) -> str:
    chat_history.append({"role": "user", "content": prompt})
    response: ChatResponse = chat(model='llama3.2', messages=chat_history)
    assistant_message = response['message']['content']
    chat_history.append({"role": "assistant", "content": assistant_message})
    return assistant_message

code_block_regex = re.compile(r"```(.*?)```", re.DOTALL)

def extract_python_code(content: str) -> str:
    code_blocks = code_block_regex.findall(content)
    if code_blocks:
        full_code = "\n".join(code_blocks)
        if full_code.strip().startswith("python"):
            full_code = full_code.strip()[len("python"):].lstrip()
        return full_code
    return None

# ------------------------ VIDEO STREAM ------------------------
frame_buffer = None
frame_lock = threading.Lock()

def gen_frames():
    global frame_buffer
    while True:
        with frame_lock:
            if frame_buffer is not None:
                ret, buffer = cv2.imencode('.jpg', frame_buffer)
                if not ret:
                    continue
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        time.sleep(0.03)

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# ------------------------- COMMAND API -------------------------
@app.route('/execute_command', methods=['POST'])
def execute_command():
    data = request.json
    command = data.get('command', '')
    try:
        if command.startswith('execute_code:'):
            code = command[len('execute_code:'):]
            local_vars = {'tello': tello, 'result': ''}
            exec(code, globals(), local_vars)
            return jsonify({'status': 'success', 'result': local_vars.get('result', 'Executed')})
        if command == 'battery':
            return jsonify({'status': 'success', 'result': tello.get_battery()})
        if command == 'takeoff':
            tello.takeoff()
        elif command == 'land':
            tello.land()
        elif command == 'emergency':
            tello.emergency()
        elif command == 'streamoff':
            tello.streamoff()
        elif command == 'streamon':
            tello.streamon()
        elif command.startswith('move_up '):
            tello.move_up(int(command.split()[1]))
        elif command.startswith('move_down '):
            tello.move_down(int(command.split()[1]))
        elif command.startswith('move_left '):
            tello.move_left(int(command.split()[1]))
        elif command.startswith('move_right '):
            tello.move_right(int(command.split()[1]))
        elif command.startswith('move_forward '):
            tello.move_forward(int(command.split()[1]))
        elif command.startswith('move_back '):
            tello.move_back(int(command.split()[1]))
        elif command.startswith('rotate_clockwise '):
            tello.rotate_clockwise(int(command.split()[1]))
        elif command.startswith('rotate_counter_clockwise '):
            tello.rotate_counter_clockwise(int(command.split()[1]))
        elif command == 'flip_forward':
            tello.flip_forward()
        elif command == 'flip_back':
            tello.flip_back()
        elif command == 'flip_left':
            tello.flip_left()
        elif command == 'flip_right':
            tello.flip_right()
        elif command == 'toggle_detection':
            global detection_enabled
            detection_enabled = not detection_enabled
        else:
            return jsonify({'status': 'error', 'message': f'Unknown command: {command}'})
        return jsonify({'status': 'success', 'result': f'Executed: {command}'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/ask', methods=['POST'])
def ask_assistant():
    data = request.json
    message = data.get('message', '')
    try:
        response = ask(message)
        code = extract_python_code(response)
        return jsonify({
            'status': 'success',
            'response': response,
            'has_code': bool(code),
            'code_to_execute': code or ''
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# ---------------------- React Frontend Routes ----------------------
@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.errorhandler(404)
def not_found(e):
    return app.send_static_file('index.html')

# ------------------------- FRAME THREADS --------------------------
def capture_frames():
    global frame_buffer
    while True:
        frame = tello.get_frame_read().frame
        if frame is not None:
            frame = imutils.resize(frame, width=400)
            (h, w) = frame.shape[:2]
            blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 0.007843, (300, 300), 127.5)
            net.setInput(blob)
            detections = net.forward()
            for i in np.arange(0, detections.shape[2]):
                confidence = detections[0, 0, i, 2]
                if confidence > 0.2:
                    idx = int(detections[0, 0, i, 1])
                    box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                    (startX, startY, endX, endY) = box.astype("int")
                    label = f"{CLASSES[idx]}: {confidence * 100:.2f}%"
                    cv2.rectangle(frame, (startX, startY), (endX, endY), COLORS[idx], 2)
                    y = startY - 15 if startY - 15 > 15 else startY + 15
                    cv2.putText(frame, label, (startX, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORS[idx], 2)
            with frame_lock:
                frame_buffer = frame
        time.sleep(0.01)

# --------------------------- MAIN ----------------------------
def main():
    capture_thread = threading.Thread(target=capture_frames, daemon=True)
    capture_thread.start()

    if not args.no_local_display:
        def display_window():
            while True:
                with frame_lock:
                    if frame_buffer is not None:
                        cv2.imshow('Tello Video (Local)', frame_buffer)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    os.kill(os.getpid(), signal.SIGINT)
                    break
            cv2.destroyAllWindows()
        threading.Thread(target=display_window, daemon=True).start()

    print(f"Server running at http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, threaded=True)

if __name__ == "__main__":
    main()