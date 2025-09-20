#!/bin/bash

echo "🚀 Starting Python environment setup for Tello Drone Project..."

# Step 1: Create virtual environment
echo "📁 Creating virtual environment: tello_env"
python3 -m venv tello_env
source tello_env/bin/activate

# Step 2: Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Step 3: Install required Python packages
echo "📦 Installing dependencies..."
pip install opencv-python flask numpy imutils djitellopy ollama

echo "✅ Setup complete! Virtual environment 'tello_env' is now active."
echo "🛸 Ready to control your drone and integrate with Ollama!"