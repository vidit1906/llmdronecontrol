import cv2
import argparse
import os
import re
import threading
import time
from ollama import chat, ChatResponse
from djitellopy import Tello

parser = argparse.ArgumentParser()
parser.add_argument("--prompt", type=str, default="room.txt")
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
    response: ChatResponse = chat(model='qwen2.5', messages=chat_history)
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
    with open(args.prompt, "r") as f:
        prompt_text = f.read()
    ask(prompt_text)
    print("Welcome to the Tello Drone chatbot using djitellopy!")
    print("Type !quit or !exit to end the session, or !clear to clear the screen.\n")
    while True:
        question = input(colors.YELLOW + "Tello Chatbot> " + colors.ENDC)
        if question in ("!quit", "!exit"):
            break
        if question == "!clear":
            os.system("cls" if os.name == "nt" else "clear")
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
    print("Chatbot loop exiting...")

# ------------------------------------------------------------------------------
# Define the livestream function (to run in the main thread)
# ------------------------------------------------------------------------------
def livestream():
    while True:
        frame = tello.get_frame_read().frame
        cv2.imshow('Tello Video', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    tello.streamoff()
    cv2.destroyAllWindows()

# ------------------------------------------------------------------------------
# Start the chatbot loop in a separate thread
# ------------------------------------------------------------------------------
chat_thread = threading.Thread(target=chatbot_loop, daemon=True)
chat_thread.start()

# Run the livestream in the main thread
livestream()

# Wait for the chatbot loop to exit (if it hasn't already)
chat_thread.join()

# Land the drone at exit (if it's airborne) and perform cleanup.
print("Landing drone and exiting...")
tello.land()
time.sleep(2)