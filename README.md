# 🚁 Altivue - AI-Powered Drone Control System

**Intelligent drone control through natural language processing and real-time computer vision**

![Altivue Banner](https://img.shields.io/badge/Altivue-AI%20Drone%20Control-blue?style=for-the-badge&logo=drone)

## 🌟 Overview

Altivue is an advanced drone control system that combines AI-powered natural language processing with real-time computer vision to create an intuitive and intelligent drone operation experience. Built for DJI Tello drones, this system allows users to control their drone using conversational commands while providing live video streaming and object detection capabilities.

### ✨ Key Features

- 🗣️ **Natural Language Control** - Control your drone using conversational commands
- 🤖 **AI-Powered Assistant** - Powered by Ollama/Llama 3.2 for intelligent command interpretation
- 📹 **Real-time Video Streaming** - Live video feed with optional object detection overlay
- 🎯 **Object Detection** - MobileNet SSD-based real-time object recognition
- 🌐 **Web Interface** - Beautiful, responsive web control panel
- 🔒 **Safety Features** - Emergency stop, battery monitoring, and connection status
- 📱 **Cross-Platform** - Works on desktop and mobile browsers

## 🏗️ System Architecture

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   Frontend (React)  │◄──►│  Backend (Flask)    │◄──►│   Tello Drone      │
│                     │    │                     │    │                     │
│ • Control Interface │    │ • AI Chat Handler   │    │ • Video Stream     │
│ • Video Display     │    │ • Command Executor  │    │ • Flight Commands  │
│ • Real-time Chat    │    │ • Object Detection  │    │ • Telemetry Data   │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
                                     │
                           ┌─────────▼─────────┐
                           │   Ollama/Llama    │
                           │   AI Assistant     │
                           └───────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- DJI Tello drone
- Ollama installed with Llama 3.2 model
- OpenCV compatible camera setup

### Backend Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/vidit1906/llmdronecontrol.git
   cd llmdronecontrol
   ```

2. **Install Python dependencies:**
   ```bash
   cd final_backend/real-time-object-detection
   pip install -r requirements.txt
   ```

3. **Install required Python packages:**
   ```bash
   pip install opencv-python djitellopy flask ollama numpy imutils chromadb
   ```

4. **Download AI models:**
   - MobileNet SSD model files should be present in the project directory
   - Ensure Ollama is running with Llama 3.2 model

5. **Start the backend server:**
   ```bash
   python chat_drone.py --host 0.0.0.0 --port 5001
   ```

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend/FullyHacks25
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm start
   ```

4. **Access the application:**
   - Open http://localhost:3000 in your browser
   - Navigate to the Control page to start using the drone interface

## 🎮 Usage

### Web Interface Commands

The system provides multiple ways to control your drone:

1. **Quick Command Buttons**: Pre-configured buttons for common operations
   - Take Off / Land
   - Movement controls (Forward, Back, Left, Right, Up, Down)
   - Rotation controls (Clockwise, Counter-clockwise)
   - Flip maneuvers
   - Emergency stop

2. **AI Chat Interface**: Natural language commands
   ```
   "Take off and fly forward 50 centimeters"
   "Rotate 90 degrees clockwise then move up"
   "Fly in a square pattern"
   "Land the drone safely"
   ```

3. **Advanced Commands**: Complex flight patterns
   ```
   "Perform a figure-8 maneuver"
   "Survey the area by flying in a grid pattern"
   "Follow a curved path to the window"
   ```

### Terminal Interface

For developers and advanced users, the system also provides a terminal-based chat interface:

```bash
python chat_drone.py
```

Then interact with commands like:
```
Tello Chatbot> Take off and hover for 5 seconds
Tello Chatbot> Move in a triangle pattern
Tello Chatbot> !quit
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
OLLAMA_HOST=localhost:11434
FLASK_PORT=5001
FLASK_HOST=0.0.0.0
TELLO_VIDEO_PORT=11111
DEBUG=True
```

### Drone Settings

Configure drone parameters in `tello.txt`:
- Flight speed limits
- Movement boundaries
- Safety protocols
- Custom command mappings

## 📁 Project Structure

```
├── final_backend/
│   └── real-time-object-detection/
│       ├── chat_drone.py              # Main backend server
│       ├── chat_vector.py             # Vector database integration
│       ├── vector_store.py            # Vector operations
│       ├── MobileNetSSD_deploy.*      # Object detection models
│       └── tello.txt                  # Drone command reference
├── frontend/
│   └── FullyHacks25/
│       ├── src/
│       │   ├── components/            # React components
│       │   ├── pages/                 # Application pages
│       │   └── assets/                # Static assets
│       └── package.json              # Node.js dependencies
├── yolo/                             # YOLO detection (alternative)
├── README.md                         # Project documentation
└── .gitignore                        # Git ignore rules
```

## 🤝 API Endpoints

### Backend API

- `GET /` - Main control interface
- `GET /video_feed` - Real-time video stream
- `POST /execute_command` - Direct drone command execution
- `POST /ask` - AI assistant chat interface

### Command Format

```json
{
  "command": "takeoff",
  "parameters": {}
}
```

### Response Format

```json
{
  "status": "success|error",
  "result": "Command result",
  "message": "Status message"
}
```

## 🔒 Safety Features

- **Emergency Stop**: Immediate motor shutdown
- **Battery Monitoring**: Real-time battery level display
- **Connection Status**: Drone connectivity monitoring
- **Automatic Landing**: Safety landing on low battery
- **Command Validation**: Input sanitization and validation
- **Flight Boundaries**: Configurable flight area limits

## 🛠️ Development

### Adding New Commands

1. **Backend (Python)**:
   ```python
   @app.route('/execute_command', methods=['POST'])
   def execute_command():
       # Add new command handling
       elif command == 'your_new_command':
           # Implementation
           return jsonify({'status': 'success', 'result': 'Done'})
   ```

2. **Frontend (React)**:
   ```javascript
   const newCommand = () => {
       sendCommand('your_new_command');
   };
   ```

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 🐛 Troubleshooting

### Common Issues

1. **Drone Connection Failed**
   - Ensure drone is powered on
   - Check WiFi connection to drone's network
   - Verify djitellopy installation

2. **Video Stream Not Loading**
   - Check if drone video streaming is enabled
   - Verify network connectivity
   - Restart backend server

3. **AI Assistant Not Responding**
   - Ensure Ollama is running
   - Check if Llama 3.2 model is installed
   - Verify network connection to Ollama service

4. **Object Detection Not Working**
   - Ensure MobileNet model files are present
   - Check OpenCV installation
   - Verify camera permissions

### Debug Mode

Enable debug mode for detailed logging:
```bash
python chat_drone.py --debug
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **DJI** for the Tello drone platform
- **djitellopy** community for the Python SDK
- **Ollama** team for the AI inference engine
- **OpenCV** community for computer vision tools
- **React** team for the frontend framework

## 📞 Support

For support and questions:
- 📧 Email: [support@altivue.com](mailto:support@altivue.com)
- 🐛 Issues: [GitHub Issues](https://github.com/vidit1906/llmdronecontrol/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/vidit1906/llmdronecontrol/discussions)

---

**⚠️ Warning**: Always follow local drone regulations and fly responsibly. This software is for educational and research purposes. Users are responsible for safe operation of their drones.

**Built with ❤️ for the future of intelligent drone technology**
