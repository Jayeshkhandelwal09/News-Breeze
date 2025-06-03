# 🌟 News Breeze - AI-Powered News with Celebrity Voices

**News Breeze** is a cutting-edge news aggregation application that combines AI summarization with celebrity voice synthesis to deliver news in an engaging, personalized way.

![News Breeze Demo](https://img.shields.io/badge/Status-Live-brightgreen) ![Python](https://img.shields.io/badge/Python-3.11-blue) ![React](https://img.shields.io/badge/React-18-61dafb) ![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688)

## ✨ Features

### 🎭 **Celebrity Voice Synthesis**
- **Morgan Freeman Style** - Deep, wise, authoritative narrator
- **David Attenborough Style** - Gentle, educational nature documentary voice
- **Professional News Anchor** - Clear, trustworthy news delivery
- **Friendly Talk Show Host** - Warm, conversational style
- **Dramatic Movie Narrator** - Cinematic, powerful voice
- **Tech Reviewer Style** - Enthusiastic, tech-savvy presentation

### 🤖 **AI-Powered Features**
- **Smart Summarization** - BART model reduces articles by ~60% while preserving key information
- **Multi-Source Aggregation** - Fetches from BBC, CNN, Reuters, NPR, AP News, The Guardian
- **Real-time Processing** - Live news updates with instant AI analysis

### 🎨 **Beautiful Interface**
- **Modern React Frontend** - Material-UI components with responsive design
- **Audio Player** - Seamless playback of celebrity voice news
- **Voice Selector** - Easy switching between celebrity voice styles
- **Mobile-Friendly** - Works perfectly on desktop, tablet, and mobile

## 🚀 Quick Start

### Prerequisites
- Python 3.11 (required for TTS compatibility)
- Node.js 16+ and npm
- ~2GB free disk space (for AI models)

### 1. Clone the Repository
```bash
git clone <repository-url>
cd News-Breeze
```

### 2. Backend Setup (Python 3.11)
```bash
# Install Python 3.11 using pyenv (if not already installed)
pyenv install 3.11.9
pyenv local 3.11.9

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Start the API server
cd app
python main.py
```

The backend will be available at `http://localhost:8000`

### 3. Frontend Setup (React)
```bash
# In a new terminal
cd frontend
npm install
npm start
```

The frontend will be available at `http://localhost:3000`

## 🎯 Usage

1. **Open your browser** to `http://localhost:3000`
2. **Select a celebrity voice** from the dropdown (Morgan Freeman, David Attenborough, etc.)
3. **Click "Refresh News"** to fetch the latest articles with AI summaries
4. **Click "Play"** on any article to hear it in your selected celebrity voice
5. **Click "Read Full"** to view the complete article on the original site

## 🏗️ Architecture

### Backend (FastAPI + Python 3.11)
```
backend/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── services/
│   │   ├── news_fetcher.py     # RSS feed aggregation
│   │   ├── ai_summarizer.py    # BART AI summarization
│   │   └── voice_synthesizer.py # TTS celebrity voices
│   └── static/audio/           # Generated audio files
└── requirements.txt
```

### Frontend (React + TypeScript)
```
frontend/
├── src/
│   ├── App.tsx                 # Main application component
│   └── ...
├── public/
└── package.json
```

## 🔧 API Endpoints

### Core Endpoints
- `GET /` - Welcome message with system info
- `GET /health` - System health check
- `POST /news` - Fetch news with AI summaries and voice synthesis
- `POST /summarize` - Standalone AI text summarization

### Voice Synthesis
- `GET /voice/voices` - Available celebrity voice catalog
- `GET /voice/samples` - Sample texts for each voice
- `POST /voice/synthesize` - Generate celebrity voice audio
- `POST /voice/test/{voice}` - Test individual voice styles

### Model Management
- `GET /models/status` - AI model loading status

## 🎤 Voice Synthesis Technology

News Breeze uses the **Coqui TTS library** with advanced text-to-speech models:

- **Primary Model**: Tacotron2-DDC (stable, fast)
- **Fallback Model**: XTTS-v2 (advanced voice cloning)
- **Audio Format**: WAV, 22kHz sample rate
- **Caching**: Smart audio file caching for performance

## 🤖 AI Summarization

Powered by **Hugging Face Transformers**:

- **Model**: facebook/bart-base (500MB)
- **Compression**: ~60% text reduction
- **Quality**: Preserves key information and context
- **Speed**: Real-time processing for news articles

## 📊 News Sources

- **BBC News** - British Broadcasting Corporation
- **CNN** - Cable News Network  
- **Reuters** - International news agency
- **NPR** - National Public Radio
- **AP News** - Associated Press
- **The Guardian** - British daily newspaper

## 🔧 Configuration

### Environment Variables
```bash
# Optional: Set custom model paths
TRANSFORMERS_CACHE=/path/to/model/cache
TTS_CACHE=/path/to/tts/cache
```

### Voice Synthesis Settings
```python
# In voice_synthesizer.py
voice_clone_config = {
    "temperature": 0.75,      # Voice randomness
    "repetition_penalty": 5.0, # Reduce repetition
    "speed": 1.0              # Speech speed
}
```

## 🚀 Deployment

### Production Backend
```bash
# Install production server
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
```

### Production Frontend
```bash
# Build for production
npm run build

# Serve with nginx or deploy to Vercel/Netlify
```

## 🐛 Troubleshooting

### Common Issues

**TTS Library Not Working**
- Ensure Python 3.11 or earlier (TTS not compatible with 3.12+)
- Install with: `pip install TTS`

**Audio Not Playing**
- Check browser audio permissions
- Verify backend is serving static files correctly
- Check network connectivity to localhost:8000

**AI Model Loading Slowly**
- First run downloads ~500MB BART model
- Subsequent runs use cached model
- Ensure stable internet connection

**CORS Errors**
- Backend includes CORS middleware for localhost:3000
- Check that both servers are running on correct ports

## 📈 Performance

- **News Fetching**: ~2-3 seconds for 6 articles
- **AI Summarization**: ~1-2 seconds per article
- **Voice Synthesis**: ~3-5 seconds per article (first time)
- **Audio Caching**: Instant playback for cached articles

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Coqui TTS** - Text-to-speech synthesis
- **Hugging Face** - AI model hosting and transformers
- **Material-UI** - React component library
- **FastAPI** - Modern Python web framework
- **News Sources** - BBC, CNN, Reuters, NPR, AP News, The Guardian

## 📞 Support

For support, please open an issue on GitHub or contact the development team.

---

**News Breeze** - *Bringing you the news in the voices you love* 🎭📰🤖 