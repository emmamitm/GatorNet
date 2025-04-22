# GatorNet: The AI Campus Companion

## Overview
GatorNet is an AI-powered campus assistant created specifically for University of Florida students. We've successfully unified UF's fragmented information systems into a single, student-friendly interface that feels personal, approachable, and context-aware. 

Our mission: Foster a greater sense of community on the UF campus by addressing the challenge of scattered information through a friendly chatbot that centralizes campus resources and helps students engage with campus life.

## Key Features

- **AI-Powered Chatbot**: Conversational interface using Meta LLama 3 that mimics a fellow Gator
- **UF-Specific Knowledge Base**: Comprehensive information about campus resources, events, and locations
- **Real-Time Interaction**: Immediate responses to student queries with context maintenance
- **Interactive Campus Map**: Visual navigation and location services
- **Secure User Accounts**: Protected personal profiles and conversation history
- **Semantic Search**: Intelligent understanding of queries beyond keyword matching
- **Mobile-Friendly Design**: Access GatorNet on any device, anywhere on campus

## Technology Stack

### Frontend
- React 18 with React Router
- React Context API for state management
- CSS Modules for styling
- Material-UI Icons
- React Leaflet for interactive maps

### Backend
- Flask (2.2.5+) REST API
- JWT Authentication
- SQLAlchemy with SQLite database
- Flask-CORS for cross-origin requests

### AI System
- llama-cpp-python (0.2.32) for LLaMA 3 model inference
- Sentence-transformers (2.2.2) for semantic search
- NLTK and spaCy for natural language processing
- Custom knowledge graph using networkx

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 16+
- npm 8+
- Git

### Installation

1. Clone the repository:
```bash
git clone https://github.com/your-org/GatorNet.git
cd GatorNet
```

2. Run the installation script:
```bash
# For macOS/Linux
chmod +x run.py
python3 run.py

# For Windows
python run_windows.py
```

3. Access the application:
- Web Interface: http://localhost:3000
- Backend API: http://localhost:5001

## System Architecture

GatorNet is built with a modular architecture divided into three main components:

1. **AI System**: The intelligence core that processes user queries using classes like EnhancedUFAssistant, ConversationState, QueryAnalyzer, and ResponseGenerator.

2. **Flask Backend**: The API layer handling routes for chat messages, authentication, and conversation management with SQLite database for user data and chat history.

3. **React Frontend**: The user interface featuring components like ChatWindow, QuickAccess, CampusMap, and ProfileSettings.

## Team

- **Emma Mitchell**: Project Manager and Backend Developer
- **Matis Luzi**: Frontend Developer and Middleware Engineer
- **Jake Rubin**: Frontend and Backend Developer
- **Adriano Arias**: Scrum Master, Backend and Database Developer, AI Contributor
- **Sophia Huerta**: AI Developer and Training Data Engineer

Project supervised by Dr. Mohammad Al-Saad

## Contributing

We welcome contributions to GatorNet! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

For major changes, please open an issue first to discuss what you would like to change.

## Troubleshooting

### Common Issues

- **Port Conflicts**: If ports 3000 or 5001 are already in use, the deployment script will attempt to find alternative ports automatically.
- **Dependencies Issues**: Ensure you have the correct Python version (3.10+) and necessary build tools installed.
- **Connection Problems**: Verify both servers are running and check firewall settings.

For additional help, please contact the development team.

## License

[MIT License](LICENSE)

## Contact

- Emma Mitchell
- Sophia Huerta
- Matis Luzi
- Adriano Arias
- Jake Rubin

---

**GatorNet**: Bringing the Gator community together through AI!
