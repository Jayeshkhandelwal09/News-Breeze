from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
import os
from typing import List, Dict, Optional
import logging

# Import our services using relative imports
from services.news_fetcher import news_fetcher, NewsArticle
from services.ai_summarizer import ai_summarizer
from services.voice_synthesizer import voice_synthesizer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create our FastAPI app
app = FastAPI(
    title="News Breeze API",
    description="AI-powered news aggregation with voice synthesis",
    version="1.0.0"
)

# Add CORS middleware to allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories for storing audio files
os.makedirs("static/audio", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Pydantic models for request/response
class NewsRequest(BaseModel):
    max_articles_per_source: Optional[int] = 3
    include_ai_summary: Optional[bool] = True
    include_voice: Optional[bool] = True
    voice_preset: Optional[str] = "morgan_freeman"  # Default to Morgan Freeman style

class SummarizeRequest(BaseModel):
    text: str
    max_length: Optional[int] = 150

class VoiceRequest(BaseModel):
    text: str
    voice_preset: Optional[str] = "morgan_freeman"  # Default celebrity voice
    language: Optional[str] = "en"

# Root endpoint - Welcome message
@app.get("/")
def read_root():
    """
    Welcome endpoint for the News Breeze API
    """
    return {
        "message": "Welcome to News Breeze API with Celebrity Voice Cloning!",
        "description": "AI-powered news aggregation with celebrity-style voice synthesis",
        "version": "1.0.0",
        "endpoints": {
            "/health": "Health check",
            "/news": "Get latest news with AI summaries and celebrity voices",
            "/news/simple": "Get simple news without AI processing",
            "/summarize": "Summarize any text using AI",
            "/voice/synthesize": "Convert text to celebrity-style speech",
            "/voice/voices": "Get available celebrity voice presets",
            "/voice/samples": "Get sample text for each celebrity voice",
            "/voice/test/{voice}": "Test a celebrity voice with sample audio",
            "/models/status": "Check AI model status"
        },
        "features": [
            "📰 RSS feed aggregation from multiple news sources",
            "🤖 AI-powered summarization using Hugging Face",
            "🎭 Celebrity voice cloning (Morgan Freeman, David Attenborough, etc.)",
            "🎬 Multiple voice styles (news anchor, documentary, dramatic)",
            "⚡ Audio caching for better performance",
            "🔄 Background processing"
        ],
        "celebrity_voices": [
            "🎬 Morgan Freeman Style - Deep, wise narrator",
            "🌿 David Attenborough Style - Nature documentary voice", 
            "📺 Professional News Anchor - Clear, authoritative",
            "🎪 Friendly Talk Show Host - Warm, engaging",
            "🎭 Dramatic Movie Narrator - Cinematic, powerful",
            "💻 Tech Reviewer Style - Enthusiastic, clear"
        ],
        "getting_started": {
            "1": "Visit /docs for interactive API testing",
            "2": "Try /voice/samples to hear celebrity voice styles",
            "3": "Use /news with voice_preset='morgan_freeman' for full experience",
            "4": "Test individual voices with /voice/test/morgan_freeman"
        }
    }

# Health check endpoint
@app.get("/health")
def health_check():
    """
    Health check endpoint to verify server is running
    """
    return {
        "status": "healthy",
        "message": "News Breeze API is running successfully!",
        "version": "1.0.0",
        "services": {
            "news_fetcher": "available",
            "ai_summarizer": "available" if ai_summarizer.is_loaded else "not_loaded",
            "voice_synthesizer": "available" if voice_synthesizer.is_loaded else "not_loaded"
        }
    }

# Simple news endpoint (no AI processing)
@app.get("/news/simple")
def get_simple_news(max_articles_per_source: int = 3):
    """
    Get latest news without AI processing (faster)
    """
    try:
        logger.info(f"📰 Fetching simple news...")
        
        # Fetch news articles
        articles = news_fetcher.fetch_latest_news(max_articles_per_source)
        
        # Convert to dictionaries
        articles_data = [article.to_dict() for article in articles]
        
        return {
            "success": True,
            "count": len(articles_data),
            "articles": articles_data,
            "processing": {
                "ai_summary": False,
                "voice_synthesis": False
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching simple news: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Main news endpoint with AI processing
@app.post("/news")
def get_news_with_ai(request: NewsRequest, background_tasks: BackgroundTasks):
    """
    Get latest news with AI summaries and voice synthesis
    This is the main endpoint that showcases all our AI features!
    """
    try:
        logger.info(f"📰 Fetching news with AI processing...")
        
        # Step 1: Fetch news articles
        logger.info("Step 1: Fetching news from RSS feeds...")
        articles = news_fetcher.fetch_latest_news(request.max_articles_per_source)
        articles_data = [article.to_dict() for article in articles]
        
        if not articles_data:
            return {
                "success": True,
                "count": 0,
                "articles": [],
                "message": "No articles found"
            }
        
        # Step 2: AI Summarization (if requested)
        if request.include_ai_summary:
            logger.info("Step 2: AI summarization...")
            try:
                articles_data = ai_summarizer.batch_summarize(articles_data)
                logger.info("✅ AI summarization completed")
            except Exception as e:
                logger.warning(f"AI summarization failed: {e}")
                # Continue without AI summaries
        
        # Step 3: Voice Synthesis (if requested)
        if request.include_voice:
            logger.info("Step 3: Voice synthesis...")
            try:
                articles_data = voice_synthesizer.batch_synthesize(
                    articles_data, 
                    voice=request.voice_preset
                )
                logger.info("✅ Voice synthesis completed")
            except Exception as e:
                logger.warning(f"Voice synthesis failed: {e}")
                # Continue without voice
        
        # Add cleanup task
        background_tasks.add_task(voice_synthesizer.cleanup_old_files)
        
        return {
            "success": True,
            "count": len(articles_data),
            "articles": articles_data,
            "processing": {
                "ai_summary": request.include_ai_summary,
                "voice_synthesis": request.include_voice,
                "voice_preset": request.voice_preset
            },
            "metadata": {
                "processing_time": "varies",
                "sources": len(news_fetcher.rss_feeds),
                "ai_model": ai_summarizer.model_name if ai_summarizer.is_loaded else None,
                "voice_model": voice_synthesizer.model_name if voice_synthesizer.is_loaded else None
            }
        }
        
    except Exception as e:
        logger.error(f"Error in news processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Standalone summarization endpoint
@app.post("/summarize")
def summarize_text(request: SummarizeRequest):
    """
    Summarize any text using AI
    """
    try:
        logger.info(f"🤖 Summarizing text of length {len(request.text)}")
        
        result = ai_summarizer.summarize_text(
            request.text, 
            custom_length=request.max_length
        )
        
        return {
            "success": result['success'],
            "summary": result['summary'],
            "original_length": result.get('original_length', 0),
            "summary_length": result.get('summary_length', 0),
            "compression_ratio": result.get('compression_ratio', 0),
            "model_used": result.get('model_used', 'unknown'),
            "error": result.get('error')
        }
        
    except Exception as e:
        logger.error(f"Error in text summarization: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Voice synthesis endpoint
@app.post("/voice/synthesize")
def synthesize_voice(request: VoiceRequest):
    """
    Convert text to speech using celebrity-style voices
    """
    try:
        logger.info(f"🎭 Synthesizing celebrity voice for text length {len(request.text)}")
        
        result = voice_synthesizer.synthesize_celebrity_voice(
            request.text,
            celebrity_voice=request.voice_preset,
            language=request.language
        )
        
        return {
            "success": result['success'],
            "audio_url": result.get('audio_url'),
            "text_length": result.get('text_length', 0),
            "celebrity_voice": result.get('celebrity_style'),
            "voice_name": result.get('voice_used'),
            "voice_description": result.get('voice_description'),
            "cached": result.get('cached', False),
            "error": result.get('error')
        }
        
    except Exception as e:
        logger.error(f"Error in celebrity voice synthesis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Get available celebrity voices
@app.get("/voice/voices")
def get_available_voices():
    """
    Get list of available celebrity voice presets with descriptions
    """
    try:
        voices = voice_synthesizer.get_available_voices()
        return {
            "success": True,
            "celebrity_voices": voices['celebrity_voices'],
            "fallback_presets": voices['fallback_presets'],
            "model_voices": voices['model_voices'],
            "model_loaded": voices['model_loaded'],
            "tts_available": voices['tts_available'],
            "recommendations": voices['recommendations'],
            "model_name": voices['model_name'],
            "error": voices['error']
        }
    except Exception as e:
        logger.error(f"Error getting celebrity voices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Get celebrity voice samples
@app.get("/voice/samples")
def get_voice_samples():
    """
    Get sample text for each celebrity voice to preview their styles
    """
    try:
        samples = voice_synthesizer.get_voice_samples()
        return {
            "success": True,
            "voice_samples": samples,
            "note": "Use these sample texts to preview different celebrity voice styles"
        }
    except Exception as e:
        logger.error(f"Error getting voice samples: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Test celebrity voice endpoint
@app.post("/voice/test/{celebrity_voice}")
def test_celebrity_voice(celebrity_voice: str):
    """
    Test a specific celebrity voice with sample text
    """
    try:
        logger.info(f"🎭 Testing celebrity voice: {celebrity_voice}")
        
        result = voice_synthesizer.test_celebrity_voice(celebrity_voice)
        
        return {
            "success": result['success'],
            "celebrity_voice": celebrity_voice,
            "audio_url": result.get('audio_url'),
            "voice_name": result.get('voice_used'),
            "sample_text": result.get('text_length', 0),
            "error": result.get('error'),
            "note": f"Test audio for {celebrity_voice} voice style"
        }
        
    except Exception as e:
        logger.error(f"Error testing celebrity voice: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Model status endpoint
@app.get("/models/status")
def get_models_status():
    """
    Check the status of all AI models
    """
    return {
        "ai_summarizer": {
            "loaded": ai_summarizer.is_loaded,
            "model": ai_summarizer.model_name,
            "status": "ready" if ai_summarizer.is_loaded else "not_loaded"
        },
        "voice_synthesizer": {
            "loaded": voice_synthesizer.is_loaded,
            "model": voice_synthesizer.model_name,
            "status": "ready" if voice_synthesizer.is_loaded else "not_loaded"
        },
        "news_fetcher": {
            "loaded": True,
            "sources": len(news_fetcher.rss_feeds),
            "status": "ready"
        }
    }

# Load models endpoint (for manual initialization)
@app.post("/models/load")
def load_models(background_tasks: BackgroundTasks):
    """
    Manually load AI models (useful for warming up)
    """
    def load_all_models():
        logger.info("🚀 Loading all AI models...")
        ai_summarizer.load_model()
        voice_synthesizer.load_model()
        logger.info("✅ All models loaded!")
    
    background_tasks.add_task(load_all_models)
    
    return {
        "message": "Model loading started in background",
        "status": "loading"
    }

if __name__ == "__main__":
    logger.info("🚀 Starting News Breeze API server...")
    logger.info("📖 Visit http://localhost:8000 for API documentation")
    logger.info("🎯 Visit http://localhost:8000/docs for interactive API docs")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info"
    ) 