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
from flask import Flask, Response, render_template_string, request, jsonify
import numpy as np
import imutils
from vector_store import DroneCommandVectorStore
import os

command_store = DroneCommandVectorStore()


detection_enabled = True

parser = argparse.ArgumentParser()
parser.add_argument("--port", type=int, default=5001, help="Port for HTTP server")
parser.add_argument("--host", type=str, default="0.0.0.0", help="Host for HTTP server")
parser.add_argument("--no-local-display", action="store_true", help="Disable local video display window")
args = parser.parse_args()

# Load the MobileNet SSD model files
print("[INFO] loading model...")
# Make sure these files are in your project directory
net = cv2.dnn.readNetFromCaffe('MobileNetSSD_deploy.prototxt.txt', 'MobileNetSSD_deploy.caffemodel')

# Initialize the classes and colors for object detection
CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
    "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
    "dog", "horse", "motorbike", "person", "pottedplant", "sheep",
    "sofa", "train", "tvmonitor"]
COLORS = np.random.uniform(0, 255, size=(len(CLASSES), 3))

print("Initializing the drone chat...")

# Initialize the vector store
command_store = DroneCommandVectorStore()

def initialize_vector_store():
    """Initialize the vector store from the tello.txt file"""
    try:
        # Check if the vector store exists, if not create it
        if not os.path.exists("./drone_commands_db"):
            print("Creating vector database from tello.txt...")
            num_chunks = command_store.create_from_tello_commands("tello.txt")
            print(f"Vector database created with {num_chunks} command chunks")
        else:
            print("Vector database already exists")
            
        # Test if the store is working
        test_query = "takeoff"
        results = command_store.similarity_search(test_query, k=1)
        print(f"Vector store test: {results}")
        return True
    except Exception as e:
        print(f"Error initializing vector store: {e}")
        print("Using default commands")
        return False
    

# Call this function during startup
initialize_vector_store()
# Get the command reference content

def read_tello_commands_file():
    """Read all tello commands - fallback if vector store fails"""
    try:
        with open("tello.txt", "r") as file:
            return file.read()
    except FileNotFoundError:
        print("Warning: tello.txt file not found. Using default commands.")
        return """
        # Tello Commands
        - takeoff(): Take off
        - land(): Land
        - move_forward(x): Move forward x cm
        - move_back(x): Move backward x cm
        - move_left(x): Move left x cm
        - move_right(x): Move right x cm
        - rotate_clockwise(x): Rotate CW x degrees
        - rotate_counter_clockwise(x): Rotate CCW x degrees
        """

tello_commands = read_tello_commands_file()
# Initialize conversation history with a system prompt.
chat_history = [
    {
        "role": "system",
        "content": (
            "You are an assistant helping me control an actual Tello drone using its Python SDK (djitellopy). "
            "When I ask you to do something, provide Python code that uses only the Tello methods (like takeoff, land, move_left, rotate_clockwise, etc.) and then an explanation of what that code does. "
            "Do not make up your own commands, only use the ones I give. "
            "Also note that there is no command as move_backward(x), it is move_back. "
            "Keep in mind that you can only use these commands. Do not generate any commands other than the ones that I am giving you. "
            "Every information about the parameters and the commands is given in the following reference:\n\n"
            f"{tello_commands}"
        ),
    }
]

def get_relevant_commands(user_query, k=5):
    """Get relevant commands based on user query"""
    try:
        commands = command_store.similarity_search(user_query, k=k)
        return "\n".join(commands)
    except Exception as e:
        print(f"Error retrieving commands: {e}")
        return read_tello_commands_file()  # Fallback to all commands


# Modify your ask function to use the relevant commands
def ask(prompt: str) -> str:
    """
    Sends the conversation (including the prompt) to Ollama and returns the assistant's response.
    """
    global chat_history
    
    # Get relevant commands for this query
    relevant_commands = get_relevant_commands(prompt)
    
    # Create a temporary system message with only relevant commands
    system_message = {
        "role": "system",
        "content": (
            "You are an assistant helping me control an actual Tello drone using its Python SDK (djitellopy). "
            "When I ask you to do something, provide Python code that uses only the Tello methods and then an explanation of what that code does. "
            "Do not make up your own commands, only use the ones provided. "
            "Keep in mind that you can only use these commands. Do not generate any commands other than the ones listed below:\n\n"
            f"{relevant_commands}"
        ),
    }
    
    # Create a message list with the system message and current prompt
    temp_history = [system_message]
    
    # Add the last few messages from chat history for context (optional)
    if len(chat_history) > 2:  # If there are previous messages
        # Take the last few user and assistant exchanges (skip the system message)
        temp_history.extend(chat_history[1:5] if len(chat_history) >= 5 else chat_history[1:])
    
    # Add the current prompt
    temp_history.append({"role": "user", "content": prompt})
    
    # Send to Ollama with temporary history
    response = chat(model='llama3.2', messages=temp_history)
    assistant_message = response['message']['content']
    
    # Add the exchange to the persistent chat history
    chat_history.append({"role": "user", "content": prompt})
    chat_history.append({"role": "assistant", "content": assistant_message})
    
    return assistant_message
# Utility to extract Python code from triple-backtick blocks.
# ------------------------------------------------------------------------------
code_block_regex = re.compile(r"```(.*?)```", re.DOTALL)
def extract_python_code(content: str) -> str:
    """
    Extracts Python code wrapped in triple backticks from the given content.
    Removes the "python" specifier if present.
    """
    code_blocks = code_block_regex.findall(content)
    if code_blocks:
        full_code = "\n".join(code_blocks)
        if full_code.strip().startswith("python"):
            full_code = full_code.strip()[len("python"):].lstrip()
        return full_code
    return None

# ------------------------------------------------------------------------------
# Terminal Colors for nicer output.
# ------------------------------------------------------------------------------
class colors:
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    ENDC = "\033[0m"

# ------------------------------------------------------------------------------
# Flask App for Video Streaming
# ------------------------------------------------------------------------------
app = Flask(__name__)
frame_buffer = None
frame_lock = threading.Lock()

def gen_frames():
    """Generator function that yields frames for the HTTP stream."""
    global frame_buffer
    while True:
        with frame_lock:
            if frame_buffer is not None:
                # Encode the frame as JPEG
                ret, buffer = cv2.imencode('.jpg', frame_buffer)
                if not ret:
                    continue
                # Convert to bytes and yield
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        # Add a small delay to prevent overwhelming the connection
        time.sleep(0.03)  # ~30 fps

# ------------------------------------------------------------------------------
# Flask App for Video Streaming and Drone Control
# ------------------------------------------------------------------------------
app = Flask(__name__)
frame_buffer = None
frame_lock = threading.Lock()
command_output = []  # Store command output for the web interface

def gen_frames():
    """Generator function that yields frames for the HTTP stream."""
    global frame_buffer
    while True:
        with frame_lock:
            if frame_buffer is not None:
                # Encode the frame as JPEG
                ret, buffer = cv2.imencode('.jpg', frame_buffer)
                if not ret:
                    continue
                # Convert to bytes and yield
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        # Add a small delay to prevent overwhelming the connection
        time.sleep(0.03)  # ~30 fps

@app.route('/')
def index():
    """Serve the main HTML page with the video stream and control interface."""
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Tello Drone Control Panel</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                margin: 0; 
                padding: 0; 
                background-color: #f5f5f5; 
                color: #333;
            }
            .container {
                display: flex;
                flex-direction: column;
                height: 100vh;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                box-sizing: border-box;
            }
            .header {
                background-color: #34495e;
                color: white;
                padding: 15px;
                border-radius: 8px 8px 0 0;
                text-align: center;
            }
            .content {
                display: flex;
                flex: 1;
                gap: 20px;
                margin-top: 20px;
            }
            .video-container {
                flex: 2;
                background-color: white;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                text-align: center;
            }
            .video-feed {
                width: 100%;
                height: auto;
                max-height: 70vh;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            .controls {
                flex: 1;
                display: flex;
                flex-direction: column;
                gap: 20px;
            }
            .chatbot-container {
                background-color: white;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                display: flex;
                flex-direction: column;
                flex: 1;
            }
            .quick-commands {
                background-color: white;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            .command-grid {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 10px;
            }
            .command-button {
                padding: 10px;
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
                transition: background-color 0.2s;
            }
            .command-button:hover {
                background-color: #2980b9;
            }
            #chatOutput {
                flex: 1;
                overflow-y: auto;
                background-color: #f9f9f9;
                padding: 10px;
                border-radius: 4px;
                border: 1px solid #ddd;
                margin-bottom: 10px;
                white-space: pre-wrap;
                font-family: monospace;
                min-height: 200px;
                max-height: 40vh;
            }
            .chat-controls {
                display: flex;
                gap: 10px;
            }
            #chatInput {
                flex: 1;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
            #sendButton {
                padding: 10px 15px;
                background-color: #2ecc71;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
                transition: background-color 0.2s;
            }
            #sendButton:hover {
                background-color: #27ae60;
            }
            .status-bar {
                background-color: #34495e;
                color: white;
                padding: 10px;
                border-radius: 0 0 8px 8px;
                display: flex;
                justify-content: space-between;
                margin-top: 20px;
            }
            .badge {
                background-color: #e74c3c;
                color: white;
                padding: 5px 10px;
                border-radius: 4px;
                font-weight: bold;
            }
            .emergency-button {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 15px;
                font-weight: bold;
                cursor: pointer;
                transition: background-color 0.2s;
            }
            .emergency-button:hover {
                background-color: #c0392b;
            }
            .user-message {
                color: #2980b9;
                margin-bottom: 5px;
                font-weight: bold;
            }
            .assistant-message {
                color: #27ae60;
                margin-bottom: 10px;
            }
            .system-message {
                color: #e74c3c;
                margin-bottom: 5px;
                font-style: italic;
            }
            .code-block {
                background-color: #f0f0f0;
                padding: 10px;
                border-radius: 4px;
                border-left: 4px solid #3498db;
                margin: 10px 0;
                overflow-x: auto;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Tello Drone Control Panel</h1>
                <p>Control your drone and view the live stream</p>
            </div>
            
            <div class="content">
                <div class="video-container">
                    <h2>Live Video Feed</h2>
                    <img src="/video_feed" alt="Drone video stream" class="video-feed">
                </div>
                
                <div class="controls">
                    <div class="quick-commands">
                        <h2>Quick Commands</h2>
                        <div class="command-grid">
                            <button class="command-button" onclick="sendCommand('takeoff')">Take Off</button>
                            <button class="command-button" onclick="sendCommand('toggle_detection')">Toggle Detection</button>
                            <button class="command-button" onclick="sendCommand('land')">Land</button>
                            <button class="command-button" onclick="sendCommand('emergency')">Emergency Stop</button>
                            <button class="command-button" onclick="sendCommand('move_up 20')">Up 20cm</button>
                            <button class="command-button" onclick="sendCommand('move_down 20')">Down 20cm</button>
                            <button class="command-button" onclick="sendCommand('battery')">Check Battery</button>
                            <button class="command-button" onclick="sendCommand('move_forward 30')">Forward 30cm</button>
                            <button class="command-button" onclick="sendCommand('move_back 30')">Back 30cm</button>
                            <button class="command-button" onclick="sendCommand('flip_forward')">Flip Forward</button>
                            <button class="command-button" onclick="sendCommand('move_left 30')">Left 30cm</button>
                            <button class="command-button" onclick="sendCommand('move_right 30')">Right 30cm</button>
                            <button class="command-button" onclick="sendCommand('flip_back')">Flip Back</button>
                            <button class="command-button" onclick="sendCommand('rotate_clockwise 90')">Rotate CW 90°</button>
                            <button class="command-button" onclick="sendCommand('rotate_counter_clockwise 90')">Rotate CCW 90°</button>
                            <button class="command-button" onclick="sendCommand('streamoff')">Stop Stream</button>
                        </div>
                    </div>
                    
                    <div class="chatbot-container">
                        <h2>AI Drone Assistant</h2>
                        <div id="chatOutput"></div>
                        <div class="chat-controls">
                            <input type="text" id="chatInput" placeholder="Enter a command or ask a question...">
                            <button id="sendButton">Send</button>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="status-bar">
                <div>Status: <span id="droneStatus">Connected</span></div>
                <div>Battery: <span id="batteryStatus" class="badge">Unknown</span></div>
                <button class="emergency-button" onclick="sendCommand('emergency')">EMERGENCY STOP</button>
            </div>
        </div>
        
        <script>
            // Initialize the chat output with a welcome message
            document.addEventListener('DOMContentLoaded', function() {
                addSystemMessage("Welcome to the Tello Drone Control Panel!");
                addSystemMessage("Use the quick command buttons or type instructions below.");
                addSystemMessage("For example, try asking: 'How do I make the drone fly in a square pattern?'");
                
                // Check battery status on load
                sendCommand('battery', true);
                
                // Set up enter key for chat input
                document.getElementById('chatInput').addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        sendChatMessage();
                    }
                });
                
                document.getElementById('sendButton').addEventListener('click', sendChatMessage);
            });
            
            // Add messages to the chat output
            function addSystemMessage(message) {
                const chatOutput = document.getElementById('chatOutput');
                chatOutput.innerHTML += `<div class="system-message">${message}</div>`;
                chatOutput.scrollTop = chatOutput.scrollHeight;
            }
            
            function addUserMessage(message) {
                const chatOutput = document.getElementById('chatOutput');
                chatOutput.innerHTML += `<div class="user-message">You: ${message}</div>`;
                chatOutput.scrollTop = chatOutput.scrollHeight;
            }
            
            function addAssistantMessage(message) {
                const chatOutput = document.getElementById('chatOutput');
                
                // Format code blocks if they exist
                let formattedMessage = message;
                
                // Check for code blocks with triple backticks
                const codeBlockRegex = /```(.*?)```/gs;
                formattedMessage = formattedMessage.replace(codeBlockRegex, function(match, code) {
                    return `<div class="code-block">${code}</div>`;
                });
                
                chatOutput.innerHTML += `<div class="assistant-message">Assistant: ${formattedMessage}</div>`;
                chatOutput.scrollTop = chatOutput.scrollHeight;
            }
            
            // Send a direct command to the drone
            function sendCommand(command, silent = false) {
                if (!silent) {
                    addSystemMessage(`Executing command: ${command}`);
                }
                
                fetch('/execute_command', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ command: command }),
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        if (command === 'battery') {
                            document.getElementById('batteryStatus').textContent = data.result + '%';
                        }
                        if (!silent) {
                            addSystemMessage(`Result: ${data.result}`);
                        }
                    } else {
                        addSystemMessage(`Error: ${data.message}`);
                    }
                })
                .catch(error => {
                    addSystemMessage(`Error: ${error.toString()}`);
                });
            }
            
            // Send a message to the AI assistant
            function sendChatMessage() {
                const chatInput = document.getElementById('chatInput');
                const message = chatInput.value.trim();
                
                if (message === '') return;
                
                addUserMessage(message);
                chatInput.value = '';
                
                // Show typing indicator
                addSystemMessage("Assistant is thinking...");
                
                fetch('/ask', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message: message }),
                })
                .then(response => response.json())
                .then(data => {
                    // Remove typing indicator
                    document.getElementById('chatOutput').lastChild.remove();
                    
                    addAssistantMessage(data.response);
                    
                    // Execute code if present
                    if (data.has_code && data.code_to_execute) {
                        addSystemMessage("Executing code...");
                        sendCommand(`execute_code:${data.code_to_execute}`);
                    }
                })
                .catch(error => {
                    // Remove typing indicator
                    document.getElementById('chatOutput').lastChild.remove();
                    addSystemMessage(`Error: ${error.toString()}`);
                });
            }
        </script>
    </body>
    </html>
    """)

@app.route('/video_feed')
def video_feed():
    """Route that returns the video stream."""
    return Response(gen_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/execute_command', methods=['POST'])
def execute_command():
    """Execute a drone command directly."""
    data = request.json
    command = data.get('command', '')
    
    try:
        # Handle special command that executes Python code
        if command.startswith('execute_code:'):
            code_to_execute = command[len('execute_code:'):]
            # Execute the code and capture any output or errors
            try:
                # Create a local dict to capture output
                local_vars = {'tello': tello, 'result': ''}
                exec(code_to_execute, globals(), local_vars)
                result = local_vars.get('result', 'Code executed successfully')
                return jsonify({'status': 'success', 'result': result})
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)})
        
        # Handle regular drone commands
        if command == 'battery':
            result = tello.get_battery()
            return jsonify({'status': 'success', 'result': result})
        elif command == 'takeoff':
            tello.takeoff()
            return jsonify({'status': 'success', 'result': 'Takeoff successful'})
        elif command == 'land':
            tello.land()
            return jsonify({'status': 'success', 'result': 'Landing successful'})
        elif command == 'emergency':
            tello.emergency()
            return jsonify({'status': 'success', 'result': 'Emergency stop triggered'})
        elif command == 'streamoff':
            tello.streamoff()
            return jsonify({'status': 'success', 'result': 'Video stream stopped'})
        elif command == 'streamon':
            tello.streamon()
            return jsonify({'status': 'success', 'result': 'Video stream started'})
        elif command.startswith('move_up '):
            distance = int(command.split(' ')[1])
            tello.move_up(distance)
            return jsonify({'status': 'success', 'result': f'Moved up {distance}cm'})
        elif command.startswith('move_down '):
            distance = int(command.split(' ')[1])
            tello.move_down(distance)
            return jsonify({'status': 'success', 'result': f'Moved down {distance}cm'})
        elif command.startswith('move_left '):
            distance = int(command.split(' ')[1])
            tello.move_left(distance)
            return jsonify({'status': 'success', 'result': f'Moved left {distance}cm'})
        elif command.startswith('move_right '):
            distance = int(command.split(' ')[1])
            tello.move_right(distance)
            return jsonify({'status': 'success', 'result': f'Moved right {distance}cm'})
        elif command.startswith('move_forward '):
            distance = int(command.split(' ')[1])
            tello.move_forward(distance)
            return jsonify({'status': 'success', 'result': f'Moved forward {distance}cm'})
        elif command.startswith('move_back '):
            distance = int(command.split(' ')[1])
            tello.move_back(distance)
            return jsonify({'status': 'success', 'result': f'Moved back {distance}cm'})
        elif command.startswith('rotate_clockwise '):
            angle = int(command.split(' ')[1])
            tello.rotate_clockwise(angle)
            return jsonify({'status': 'success', 'result': f'Rotated clockwise {angle} degrees'})
        elif command.startswith('rotate_counter_clockwise '):
            angle = int(command.split(' ')[1])
            tello.rotate_counter_clockwise(angle)
            return jsonify({'status': 'success', 'result': f'Rotated counter-clockwise {angle} degrees'})
        elif command == 'flip_forward':
            tello.flip_forward()
            return jsonify({'status': 'success', 'result': 'Flipped forward'})
        elif command == 'flip_back':
            tello.flip_back()
            return jsonify({'status': 'success', 'result': 'Flipped backward'})
        elif command == 'flip_left':
            tello.flip_left()
            return jsonify({'status': 'success', 'result': 'Flipped left'})
        elif command == 'flip_right':
            tello.flip_right()
            return jsonify({'status': 'success', 'result': 'Flipped right'})
        elif command == 'toggle_detection':
            global detection_enabled
            detection_enabled = not detection_enabled
            status = "enabled" if detection_enabled else "disabled"
            return jsonify({'status': 'success', 'result': f'Object detection {status}'})
        else:
            return jsonify({'status': 'error', 'message': f'Unknown command: {command}'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/ask', methods=['POST'])
def ask_assistant():
    """Send a message to the Ollama assistant and get a response."""
    data = request.json
    message = data.get('message', '')
    
    try:
        response = ask(message)
        # Check if there's Python code in the response
        code = extract_python_code(response)
        if code:
            return jsonify({
                'status': 'success', 
                'response': response,
                'has_code': True,
                'code_to_execute': code
            })
        else:
            return jsonify({
                'status': 'success', 
                'response': response,
                'has_code': False
            })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# ------------------------------------------------------------------------------
# Connect to Tello drone and start video streaming
# ------------------------------------------------------------------------------
print("Connecting to Tello drone...")
tello = Tello()
tello.connect()
print("Battery:", tello.get_battery())

# Start video streaming immediately
tello.streamon()

# ------------------------------------------------------------------------------
# Define the interactive chatbot loop (to be run in a separate thread)
# ------------------------------------------------------------------------------
def chatbot_loop():
    print("Welcome to the Tello Drone chatbot using djitellopy!")
    print("Type !quit or !exit to end the session, or !clear to clear the screen.\n")
    
    # Send initial system message to Ollama if needed
    # Removed tello.txt dependency
    
    while True:
        try:
            question = input(colors.YELLOW + "Tello Chatbot> " + colors.ENDC)
            if question in ("!quit", "!exit"):
                # Signal the main thread to exit
                os.kill(os.getpid(), signal.SIGINT)
                break
            if question == "!clear":
                os.system("cls" if os.name == "nt" else "clear")
                continue
            if not question.strip():
                continue

            response = ask(question)
            print("\n" + response + "\n")

            # Extract and execute any Python code provided in the assistant's response.
            code = extract_python_code(response)
            if code is not None:
                print("Executing the following code:")
                print(code)
                try:
                    exec(code)
                except Exception as e:
                    print("Error executing code:", e)
                print("Execution complete!\n")
                print("Battery:", tello.get_battery())
        except EOFError:
            # Handle Ctrl+D gracefully
            break
        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            break
    
    print("Chatbot loop exiting...")

# ------------------------------------------------------------------------------
# Define the frame capture function (to run in its own thread)
# ------------------------------------------------------------------------------
def capture_frames():
    global frame_buffer
    while True:
        # Get the raw frame from drone
        frame = tello.get_frame_read().frame
        
        if frame is not None:
            # Always make a copy of the frame to avoid modifying the original
            processed_frame = frame.copy()
            
            # Only perform detection if enabled
            if detection_enabled:
                # Resize the frame for detection
                processed_frame = imutils.resize(processed_frame, width=400)
                
                # Get frame dimensions and create a blob for the neural network
                (h, w) = processed_frame.shape[:2]
                blob = cv2.dnn.blobFromImage(cv2.resize(processed_frame, (300, 300)),
                    0.007843, (300, 300), 127.5)
                
                # Pass the blob through the network and get detections
                net.setInput(blob)
                detections = net.forward()
                
                # Process each detection
                for i in np.arange(0, detections.shape[2]):
                    # Extract the confidence of the prediction
                    confidence = detections[0, 0, i, 2]
                    
                    # Filter out weak detections
                    if confidence > 0.2:
                        # Get the class index and bounding box coordinates
                        idx = int(detections[0, 0, i, 1])
                        box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                        (startX, startY, endX, endY) = box.astype("int")
                        
                        # Draw the prediction on the frame
                        label = "{}: {:.2f}%".format(CLASSES[idx], confidence * 100)
                        cv2.rectangle(processed_frame, (startX, startY), (endX, endY),
                            COLORS[idx], 2)
                        y = startY - 15 if startY - 15 > 15 else startY + 15
                        cv2.putText(processed_frame, label, (startX, y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORS[idx], 2)
            
            # Update the frame buffer with either the processed frame (if detection enabled)
            # or the original frame (if detection disabled)
            with frame_lock:
                frame_buffer = processed_frame
        
        # Small delay to prevent maxing out CPU
        time.sleep(0.01)
# ------------------------------------------------------------------------------
# Define the main function to manage program flow
# ------------------------------------------------------------------------------
def main():
    initialize_vector_store()
    global frame_buffer
    
    # Start the frame capture thread
    capture_thread = threading.Thread(target=capture_frames, daemon=True)
    capture_thread.start()
    
    # Start the chatbot thread
    chat_thread = threading.Thread(target=chatbot_loop, daemon=True)
    chat_thread.start()
    
    # Display local window in main thread if enabled (avoids macOS OpenCV issues)
    if not args.no_local_display:
        def display_window():
            while True:
                try:
                    with frame_lock:
                        if frame_buffer is not None:
                            cv2.imshow('Tello Video (Local)', frame_buffer)
                    # Short wait for key press and window updates
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        os.kill(os.getpid(), signal.SIGINT)
                        break
                except Exception as e:
                    print(f"Display error: {e}")
                    break
            cv2.destroyAllWindows()
        
        # Start display in a separate thread
        display_thread = threading.Thread(target=display_window, daemon=True)
        display_thread.start()
    
    try:
        # Start the Flask server in the main thread
        print(f"Starting HTTP server at http://{args.host}:{args.port}")
        print(f"Access video stream at http://{args.host}:{args.port}/video_feed")
        print(f"Press Ctrl+C to exit")
        app.run(host=args.host, port=args.port, threaded=True)
    except KeyboardInterrupt:
        print("\nShutdown requested... exiting")
    finally:
        # Clean up - land the drone and close connections
        print("Landing drone and exiting...")
        try:
            tello.land()
            time.sleep(1)
            tello.end()
        except Exception as e:
            print(f"Error during shutdown: {e}")
        cv2.destroyAllWindows()

# Start the program
if __name__ == "__main__":
    main()