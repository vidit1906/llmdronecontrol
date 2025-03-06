import argparse
import os
import re
from ollama import chat, ChatResponse
from djitellopy import Tello
import time
import cv2

# ------------------------------------------------------------------------------
# Ollama Chat Setup
# ------------------------------------------------------------------------------
parser = argparse.ArgumentParser()
parser.add_argument("--prompt", type=str, default="tello.txt")
args = parser.parse_args()

print("Initializing the drone chat...")
drone = Tello()
drone.streamon() 



while True:

    # Get the current frame from the stream

    frame = drone.get_frame_read().frame

    

    # Display the frame using OpenCV

    cv2.imshow('Tello Video', frame)

    

    # Press 'q' to quit

    if cv2.waitKey(1) & 0xFF == ord('q'):

        break



# Stop the video stream

drone.streamoff()



# Close the video window

cv2.destroyAllWindows()

# Initialize conversation history with a system prompt.
chat_history = [
    {
        "role": "system",
        "content": (
            "You are an assistant helping me control an actual Tello drone using its Python SDK (djitellopy). "
            "When I ask you to do something, provide Python code that uses only the Tello methods (like takeoff, land, move_left, rotate_clockwise, etc.) and then an explanation of what that code does. Reference what I have given you do not make commands on your own"
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
# Initialize and connect to the Tello drone using djitellopy.
# ------------------------------------------------------------------------------
print("Connecting to Tello drone...")
tello = Tello()
tello.connect()
print("Battery:", tello.get_battery())

# Optionally, you can start video streaming if desired:
# tello.streamon()

# ------------------------------------------------------------------------------
# Prime conversation with the initial prompt file.
# ------------------------------------------------------------------------------
with open(args.prompt, "r") as f:
    prompt_text = f.read()
ask(prompt_text)

print("Welcome to the Tello Drone chatbot using djitellopy!")
print("Type !quit or !exit to end the session, or !clear to clear the screen.\n")

# ------------------------------------------------------------------------------
# Main interactive loop.
# ------------------------------------------------------------------------------
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


# Land the drone at exit (if it's airborne) and perform cleanup.
print("Landing drone and exiting...")
tello.land()
time.sleep(2)