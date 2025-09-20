import argparse
import os
import re
import json
from ollama import chat, ChatResponse
from DroneBlocksTelloSimulator import SimulatedDrone

# ------------------------------------------------------------------------------
# Argument Parsing and Config Loading
# ------------------------------------------------------------------------------
parser = argparse.ArgumentParser()
parser.add_argument("--prompt", type=str, default="tello_basic.txt")
args = parser.parse_args()

with open("config.json", "r") as f:
    config = json.load(f)

print("Initializing Ollama and DroneBlocks Simulator...")

# ------------------------------------------------------------------------------
# Chat History and Chat Function using Ollama
# ------------------------------------------------------------------------------
chat_history = [
    {
        "role": "system",
        "content": (
            "You are an assistant helping me with the DroneBlocks simulator for the Tello drone. "
            "When I ask you to do something, provide Python code that uses only the simulator's functions "
            "(like drone.takeoff(), drone.fly_forward(), drone.fly_left(), etc.) and then an explanation of what that code does. "
            "Do not use any other hypothetical functions."
        ),
    }
]

def ask(prompt: str) -> str:
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
# Utility to Extract Python Code from Triple Backticks
# ------------------------------------------------------------------------------
code_block_regex = re.compile(r"```(.*?)```", re.DOTALL)
def extract_python_code(content: str) -> str:
    code_blocks = code_block_regex.findall(content)
    if code_blocks:
        full_code = "\n".join(code_blocks)
        if full_code.strip().startswith("python"):
            full_code = full_code.strip()[len("python"):].lstrip()
        return full_code
    return None

# ------------------------------------------------------------------------------
# Terminal Colors for Output
# ------------------------------------------------------------------------------
class colors:
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    ENDC = "\033[0m"

# ------------------------------------------------------------------------------
# Initialize the DroneBlocks Simulator
# ------------------------------------------------------------------------------
print("Initializing DroneBlocks Simulator...")
drone = SimulatedDrone(config["DRONEBLOCKS_SIM_KEY"])
print("Drone initialized successfully.")

# Optionally, define a dictionary of corners (if needed for your commands)
dict_of_corners = {
    'origin': [0, 0],
    'front right corner': [1000, -1000],
    'front left corner': [1000, 1000],
    'back left corner': [-1000, 1000],
    'back right corner': [-1000, -1000]
}

# ------------------------------------------------------------------------------
# Prime the Conversation with a Prompt File
# ------------------------------------------------------------------------------
with open(args.prompt, "r") as f:
    prompt_text = f.read()

ask(prompt_text)

print("Welcome to the DroneBlocks Tello simulator chatbot using Ollama! I am ready to help you with your Tello commands.")

# ------------------------------------------------------------------------------
# Interactive Chatbot Loop
# ------------------------------------------------------------------------------
while True:
    question = input(colors.YELLOW + "DroneBlocks Simulator> " + colors.ENDC)
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
        print("Executing the following code in the simulator:")
        print(code)
        try:
            exec(code)
        except Exception as e:
            print("Error executing code:", e)
        print("Done!\n")