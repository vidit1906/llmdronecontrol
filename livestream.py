import cv2
import argparse
import os
import re
import threading
import time
import signal
from ollama import chat, ChatResponse
from djitellopy import Tello
from flask import Flask, Response, render_template_string
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument("--port", type=int, default=5001, help="Port for HTTP server")
parser.add_argument("--host", type=str, default="0.0.0.0", help="Host for HTTP server")
parser.add_argument("--no-local-display", action="store_true", help="Disable local video display window")
args = parser.parse_args()

print("Initializing the drone chat...")

# Initialize conversation history with a system prompt.
chat_history = [
    {
        "role": "system",
        "content": (
            "You are an assistant helping me control an actual Tello drone using its Python SDK (djitellopy). "
            "When I ask you to do something, provide Python code that uses only the Tello methods (like takeoff, land, move_left, rotate_clockwise, etc.) and then an explanation of what that code does. Do not make yp your own commands only use the ones I give. Also note that there is no command as move_backward(x) it is move_back"
        ),
    }
]

def ask(prompt: str) -> str:
    """
    Sends the conversation (including the prompt) to Ollama and returns the assistant's response.
    """
    chat_history.append({
        "role": "user",
        "content": prompt,
    })
    response: ChatResponse = chat(model='llama3.2', messages=chat_history)
    assistant_message = response['message']['content']
    chat_history.append({
        "role": "assistant",
        "content": assistant_message,
    })
    return assistant_message

# ------------------------------------------------------------------------------
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

@app.route('/')
def index():
    """Serve a simple HTML page with the video stream."""
    return render_template_string("""
    <html>
    <head>
        <title>Tello Drone Stream</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; text-align: center; background-color: #f5f5f5; }
            h1 { color: #333; }
            img { max-width: 100%; border: 2px solid #ddd; border-radius: 4px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
            .container { max-width: 800px; margin: 0 auto; padding: 20px; background-color: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .info { background-color: #e8f4f8; padding: 12px; border-radius: 4px; margin-top: 20px; text-align: left; }
            code { background-color: #f0f0f0; padding: 2px 5px; border-radius: 3px; }
            .battery { font-size: 16px; font-weight: bold; margin-top: 15px; color: #555; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Tello Drone Live Stream</h1>
            <img src="/video_feed" alt="Drone video stream" />
            
            <div class="info">
                <h3>Stream Information:</h3>
                <p>Stream URL for YOLO processing: <code>http://[YOUR_IP]:{{ port }}/video_feed</code></p>
                <p>You can use this URL in your YOLO model code to process the stream.</p>
            </div>
        </div>
    </body>
    </html>
    """, port=args.port)

@app.route('/video_feed')
def video_feed():
    """Route that returns the video stream."""
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

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
        frame = tello.get_frame_read().frame
        with frame_lock:
            frame_buffer = frame
        time.sleep(0.01)  # Small delay to prevent maxing out CPU

# ------------------------------------------------------------------------------
# Define the main function to manage program flow
# ------------------------------------------------------------------------------
def main():
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