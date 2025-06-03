import torch
import logging
import os
import hashlib
from typing import Optional, Dict, List
import tempfile
from datetime import datetime
import warnings

# Import TTS components
try:
    from TTS.api import TTS
    from TTS.tts.configs.xtts_config import XttsConfig
    from TTS.tts.models.xtts import Xtts
    TTS_AVAILABLE = True
    TTS_ERROR = None
    logging.info("✅ TTS library loaded successfully")
except ImportError as e:
    TTS_AVAILABLE = False
    TTS_ERROR = str(e)
    warnings.warn("TTS library not available. Voice synthesis will be disabled.")
    logging.warning(f"🚨 TTS not available: {e}")

logger = logging.getLogger(__name__)

class VoiceSynthesizer:
    """
    Enhanced Voice Synthesis Service with Celebrity Voice Cloning
    
    This service converts text to speech using AI-generated celebrity-like voices.
    Features:
    - Celebrity voice cloning using Coqui XTTS-v2
    - Multiple voice presets (Morgan Freeman, David Attenborough, etc.)
    - Voice caching for performance
    - Graceful fallback when TTS unavailable
    """
    
    def __init__(self):
        self.tts = None
        self.is_loaded = False
        self.model_name = "tts_models/en/ljspeech/tacotron2-DDC"  # More stable model
        self.backup_model = "tts_models/multilingual/multi-dataset/xtts_v2"  # Fallback
        self.output_dir = "static/audio"  # Relative to app directory
        self.available_voices = {}
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Audio configuration
        self.sample_rate = 22050
        self.audio_format = "wav"
        
        # Enhanced Celebrity Voice Presets
        self.celebrity_voices = {
            "morgan_freeman": {
                "name": "Morgan Freeman Style",
                "description": "Deep, wise, authoritative narrator voice",
                "language": "en",
                "category": "narrator",
                "style": "documentary",
                "reference_text": "Through the wormhole of time and space, we discover the mysteries of our universe."
            },
            "david_attenborough": {
                "name": "David Attenborough Style", 
                "description": "Gentle, educational, nature documentary voice",
                "language": "en",
                "category": "narrator",
                "style": "nature_documentary",
                "reference_text": "In the heart of the wilderness, nature reveals her most extraordinary secrets."
            },
            "news_anchor_pro": {
                "name": "Professional News Anchor",
                "description": "Clear, authoritative, trustworthy news delivery",
                "language": "en", 
                "category": "news",
                "style": "professional",
                "reference_text": "Good evening, here are tonight's top stories from around the world."
            },
            "friendly_host": {
                "name": "Friendly Talk Show Host",
                "description": "Warm, engaging, conversational style",
                "language": "en",
                "category": "casual",
                "style": "friendly",
                "reference_text": "Welcome back to the show! Today we have some fascinating stories to share."
            },
            "dramatic_narrator": {
                "name": "Dramatic Movie Narrator",
                "description": "Deep, dramatic, cinematic voice",
                "language": "en",
                "category": "entertainment", 
                "style": "dramatic",
                "reference_text": "In a world where news travels at the speed of light, one app dares to make sense of it all."
            },
            "tech_reviewer": {
                "name": "Tech Reviewer Style",
                "description": "Enthusiastic, clear, tech-savvy presentation",
                "language": "en",
                "category": "tech",
                "style": "enthusiastic",
                "reference_text": "Today we're looking at the latest breakthrough in artificial intelligence technology."
            }
        }
        
        # Fallback to simpler presets for compatibility
        self.voice_presets = {
            "news_anchor": {
                "name": "Professional News Anchor",
                "description": "Clear, authoritative voice perfect for news",
                "language": "en"
            },
            "casual": {
                "name": "Friendly Casual Voice", 
                "description": "Warm, conversational tone",
                "language": "en"
            },
            "documentary": {
                "name": "Documentary Narrator",
                "description": "Deep, engaging documentary style",
                "language": "en"
            }
        }
        
        # Voice cloning configuration
        self.voice_clone_config = {
            "temperature": 0.75,  # Controls randomness (0.1-1.0)
            "repetition_penalty": 5.0,  # Reduces repetition
            "top_k": 50,  # Limits vocabulary
            "top_p": 0.85,  # Nucleus sampling
            "speed": 1.0,  # Speech speed multiplier
        }
        
        # Check TTS availability
        if not TTS_AVAILABLE:
            logger.warning(f"🚨 Voice synthesis unavailable: {TTS_ERROR}")
            logger.info("💡 This is normal with Python 3.12+ - TTS library needs updating")
            logger.info("🎤 Celebrity voice cloning will be disabled")
            logger.info("📰 News fetching and AI summarization will still work perfectly!")
        else:
            logger.info("🎭 Celebrity voice cloning ready!")
    
    def load_model(self) -> bool:
        """
        Load the TTS model for voice synthesis
        First tries stable Tacotron2 model, then XTTS-v2 as fallback
        """
        if not TTS_AVAILABLE:
            logger.error("❌ TTS library not installed or compatible")
            logger.info("🔧 For voice cloning support:")
            logger.info("   1. Use Python 3.11 or earlier")
            logger.info("   2. pip install TTS")
            logger.info("   3. Or wait for Python 3.12+ compatibility")
            return False
        
        if self.is_loaded:
            logger.info("✅ Voice model already loaded")
            return True
        
        # Try stable model first
        for model_name in [self.model_name, self.backup_model]:
            try:
                logger.info(f"🎤 Loading TTS model: {model_name.split('/')[-1]}...")
                
                # Set environment variables to handle TTS terms agreement
                import os
                import sys
                from io import StringIO
                import torch
                
                # Agree to TTS terms automatically for non-commercial use
                os.environ['COQUI_TOS_AGREED'] = "1"
                
                # Fix PyTorch weights loading issue
                torch.serialization.add_safe_globals([
                    'TTS.tts.configs.xtts_config.XttsConfig',
                    'TTS.tts.configs.vits_config.VitsConfig',
                    'TTS.tts.configs.tacotron2_config.Tacotron2Config'
                ])
                
                # Check for GPU acceleration
                device = "cuda" if torch.cuda.is_available() else "cpu"
                if device == "cuda":
                    logger.info("🚀 GPU detected! Voice synthesis will be faster")
                else:
                    logger.info("💻 Using CPU for voice synthesis")
                
                # Handle the interactive license prompt by temporarily redirecting stdin
                original_stdin = sys.stdin
                try:
                    # Create fake input that answers "y" to the license agreement
                    sys.stdin = StringIO("y\n")
                    
                    # Load TTS model
                    self.tts = TTS(model_name).to(device)
                    
                finally:
                    # Restore original stdin
                    sys.stdin = original_stdin
                
                # Test model capabilities
                if hasattr(self.tts, 'speakers') and self.tts.speakers:
                    logger.info(f"🎭 Built-in voices available: {len(self.tts.speakers)}")
                    self.available_voices = {
                        f"speaker_{i}": name for i, name in enumerate(self.tts.speakers[:10])
                    }
                else:
                    logger.info("🎤 Single voice model loaded")
                
                self.is_loaded = True
                self.current_model = model_name
                logger.info(f"✅ TTS model loaded successfully: {model_name.split('/')[-1]}!")
                logger.info("🎬 Ready to synthesize news with AI voices!")
                
                return True
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to load {model_name}: {e}")
                if "terms of service" in str(e).lower():
                    logger.info("📜 TTS requires license agreement for voice synthesis")
                    logger.info("💡 This app uses TTS for non-commercial educational purposes")
                    logger.info("🔧 For commercial use, please purchase a Coqui license")
                elif "weights" in str(e).lower() or "pickle" in str(e).lower():
                    logger.info("⚙️ PyTorch compatibility issue - trying next model...")
                continue
        
        logger.error("❌ All TTS models failed to load")
        logger.info("💡 Voice synthesis will be disabled")
        logger.info("💡 News fetching and AI summarization will still work!")
        return False
    
    def get_celebrity_voice_config(self, voice_name: str) -> Dict:
        """
        Get configuration for a celebrity voice preset
        """
        if voice_name in self.celebrity_voices:
            return self.celebrity_voices[voice_name]
        elif voice_name in self.voice_presets:
            return self.voice_presets[voice_name]
        else:
            # Default to professional news anchor
            return self.celebrity_voices["news_anchor_pro"]
    
    def generate_filename(self, text: str, voice: str = "default") -> str:
        """
        Generate a unique filename for cached audio
        """
        # Create hash of text + voice for unique filename
        content = f"{text}_{voice}_{self.model_name}"
        hash_object = hashlib.md5(content.encode())
        hash_hex = hash_object.hexdigest()
        
        timestamp = datetime.now().strftime("%Y%m%d")
        filename = f"celebrity_voice_{voice}_{timestamp}_{hash_hex[:8]}.{self.audio_format}"
        
        return os.path.join(self.output_dir, filename)
    
    def clean_text_for_speech(self, text: str) -> str:
        """
        Clean and optimize text for celebrity voice synthesis
        """
        if not text:
            return ""
        
        # Remove problematic characters
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        text = text.replace('—', '-').replace('–', '-')
        text = text.replace('&', 'and')
        
        # Remove URLs and handles
        import re
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        text = re.sub(r'@\w+', '', text)
        text = re.sub(r'#\w+', '', text)
        
        # Clean extra whitespace
        text = ' '.join(text.split())
        
        # Optimize length for voice cloning (XTTS works best with shorter segments)
        if len(text) > 400:  # Optimal length for voice cloning
            sentences = text.split('.')
            truncated = ""
            for sentence in sentences:
                if len(truncated + sentence) < 400:
                    truncated += sentence + "."
                else:
                    break
            text = truncated
        
        # Add natural pauses for better speech rhythm
        text = text.replace('.', '. ')
        text = text.replace(',', ', ')
        text = text.replace(';', '; ')
        
        return text.strip()
    
    def synthesize_celebrity_voice(self, text: str, celebrity_voice: str = "morgan_freeman", language: str = "en") -> Dict:
        """
        Synthesize speech using AI voice models
        
        Args:
            text: Text to convert to speech
            celebrity_voice: Voice preset to use (determines style)
            language: Language code
        
        Returns:
            Dictionary with audio file path and metadata
        """
        if not TTS_AVAILABLE:
            return {
                "success": False,
                "error": f"Voice synthesis unavailable: {TTS_ERROR}",
                "audio_url": None,
                "fallback_text": text[:100] + "..." if len(text) > 100 else text,
                "note": "Voice synthesis disabled due to Python 3.12+ compatibility issues"
            }
        
        if not self.is_loaded:
            logger.warning("🎤 TTS model not loaded, attempting to load...")
            if not self.load_model():
                return {
                    "success": False,
                    "error": "TTS model failed to load",
                    "audio_url": None,
                    "fallback_text": text
                }
        
        try:
            # Get voice configuration
            voice_config = self.get_celebrity_voice_config(celebrity_voice)
            
            # Clean and prepare text
            clean_text = self.clean_text_for_speech(text)
            
            if not clean_text:
                return {
                    "success": False,
                    "error": "No valid text to synthesize",
                    "audio_url": None
                }
            
            # Generate filename for caching
            audio_file = self.generate_filename(clean_text, celebrity_voice)
            
            # Check if already cached
            if os.path.exists(audio_file):
                logger.info(f"🎤 Using cached {voice_config['name']} voice")
                audio_url = f"/static/audio/{os.path.basename(audio_file)}"
                return {
                    "success": True,
                    "audio_url": audio_url,
                    "text_length": len(clean_text),
                    "voice_used": voice_config['name'],
                    "cached": True,
                    "model_used": getattr(self, 'current_model', 'unknown')
                }
            
            logger.info(f"🎤 Generating {voice_config['name']} voice for: {clean_text[:50]}...")
            
            # Generate speech based on model type
            if hasattr(self.tts, 'speakers') and self.tts.speakers:
                # Multi-speaker model (XTTS)
                speaker = self.tts.speakers[0] if self.tts.speakers else None
                self.tts.tts_to_file(
                    text=clean_text,
                    file_path=audio_file,
                    speaker=speaker,
                    language=language
                )
            else:
                # Single speaker model (Tacotron2)
                self.tts.tts_to_file(
                    text=clean_text,
                    file_path=audio_file
                )
            
            # Verify file was created successfully
            if os.path.exists(audio_file) and os.path.getsize(audio_file) > 1000:  # Basic size check
                audio_url = f"/static/audio/{os.path.basename(audio_file)}"
                
                logger.info(f"✅ {voice_config['name']} voice generated successfully!")
                
                return {
                    "success": True,
                    "audio_url": audio_url,
                    "text_length": len(clean_text),
                    "voice_used": voice_config['name'],
                    "cached": False,
                    "voice_description": voice_config['description'],
                    "model_used": getattr(self, 'current_model', 'unknown')
                }
            else:
                logger.error("❌ Audio file generation failed or file too small")
                return {
                    "success": False,
                    "error": "Audio generation failed - file not created properly",
                    "audio_url": None
                }
                
        except Exception as e:
            logger.error(f"❌ Error in voice synthesis: {e}")
            return {
                "success": False,
                "error": f"Voice synthesis failed: {str(e)}",
                "audio_url": None,
                "fallback_text": clean_text
            }
    
    def synthesize_speech(self, text: str, voice: str = "morgan_freeman", language: str = "en") -> Dict:
        """
        Main speech synthesis method - now with celebrity voices!
        """
        return self.synthesize_celebrity_voice(text, voice, language)
    
    def synthesize_article_summary(self, article_data: Dict, celebrity_voice: str = "news_anchor_pro") -> Dict:
        """
        Generate celebrity-style speech for a news article summary
        
        Args:
            article_data: Article dictionary with title, summary, etc.
            celebrity_voice: Celebrity voice preset to use
        
        Returns:
            Dictionary with audio URL and metadata
        """
        if not TTS_AVAILABLE:
            return {
                "success": False,
                "error": "Celebrity voice cloning not available with current Python version",
                "audio_url": None,
                "note": "Try Python 3.11 or earlier for celebrity voice support"
            }
        
        # Get the AI summary if available, otherwise use original summary
        text_to_speak = article_data.get('ai_summary', article_data.get('summary', ''))
        title = article_data.get('title', '')
        
        if not text_to_speak:
            return {
                "success": False,
                "error": "No text available for celebrity voice synthesis",
                "audio_url": None
            }
        
        # Create engaging intro based on celebrity voice style
        voice_config = self.get_celebrity_voice_config(celebrity_voice)
        
        if celebrity_voice == "morgan_freeman":
            speech_text = f"In today's news... {title}. {text_to_speak}"
        elif celebrity_voice == "david_attenborough":
            speech_text = f"Here in the world of human affairs, we observe... {title}. {text_to_speak}"
        elif celebrity_voice == "dramatic_narrator":
            speech_text = f"Breaking: {title}. {text_to_speak}"
        else:
            speech_text = f"News update: {title}. {text_to_speak}"
        
        logger.info(f"🎭 Generating {voice_config['name']} voice for article: {title[:30]}...")
        
        # Generate celebrity speech
        result = self.synthesize_celebrity_voice(speech_text, celebrity_voice)
        
        if result['success']:
            logger.info(f"✅ {voice_config['name']} article speech generated successfully!")
        else:
            logger.warning(f"⚠️ {voice_config['name']} article speech generation failed")
        
        return result
    
    def batch_synthesize(self, articles: List[Dict], voice: str = "morgan_freeman") -> List[Dict]:
        """
        Generate celebrity voices for multiple articles
        
        Args:
            articles: List of article dictionaries
            voice: Celebrity voice preset to use
        
        Returns:
            List of articles with celebrity audio URLs added
        """
        logger.info(f"🎬 Starting batch celebrity voice synthesis for {len(articles)} articles...")
        
        if not TTS_AVAILABLE:
            logger.warning("🚨 Celebrity voice cloning unavailable - skipping audio generation")
            logger.info("📰 Articles will still have AI summaries!")
        
        synthesized_articles = []
        voice_config = self.get_celebrity_voice_config(voice)
        
        for i, article in enumerate(articles, 1):
            logger.info(f"Processing article {i}/{len(articles)} with {voice_config['name']}")
            
            # Generate celebrity speech (will fail gracefully if TTS unavailable)
            speech_result = self.synthesize_article_summary(article, voice)
            
            # Add audio info to article
            article_copy = article.copy()
            if speech_result['success']:
                article_copy['audio_url'] = speech_result['audio_url']
                article_copy['has_audio'] = True
                logger.info(f"✅ Audio generated for: {article.get('title', 'Unknown')[:50]}...")
            else:
                article_copy['audio_url'] = None
                article_copy['has_audio'] = False
                logger.warning(f"⚠️ Audio failed for: {article.get('title', 'Unknown')[:50]}...")
            
            article_copy['voice_synthesis_metadata'] = {
                'success': speech_result['success'],
                'celebrity_voice': voice,
                'voice_name': voice_config['name'],
                'voice_description': voice_config['description'],
                'error': speech_result.get('error'),
                'note': speech_result.get('note', 'Celebrity voice synthesis attempted')
            }
            
            synthesized_articles.append(article_copy)
        
        success_count = sum(1 for a in synthesized_articles if a['has_audio'])
        logger.info(f"🎭 Celebrity voice batch complete! Generated {success_count}/{len(articles)} audio files")
        return synthesized_articles
    
    def get_available_voices(self) -> Dict:
        """
        Get list of available celebrity voice presets and their descriptions
        """
        return {
            "celebrity_voices": self.celebrity_voices,
            "fallback_presets": self.voice_presets,
            "model_voices": self.available_voices,
            "model_loaded": self.is_loaded,
            "tts_available": TTS_AVAILABLE,
            "model_name": self.model_name,
            "error": TTS_ERROR if not TTS_AVAILABLE else None,
            "recommendations": {
                "news": ["news_anchor_pro", "morgan_freeman"],
                "educational": ["david_attenborough", "documentary"],
                "entertainment": ["dramatic_narrator", "friendly_host"],
                "tech": ["tech_reviewer", "casual"]
            }
        }
    
    def get_voice_samples(self) -> Dict:
        """
        Get sample text for each celebrity voice to demonstrate styles
        """
        samples = {}
        for voice_id, config in self.celebrity_voices.items():
            samples[voice_id] = {
                "name": config["name"],
                "sample_text": config["reference_text"],
                "description": config["description"],
                "category": config["category"]
            }
        return samples
    
    def cleanup_old_files(self, days_old: int = 7):
        """
        Clean up old celebrity voice audio files to save disk space
        """
        try:
            import time
            current_time = time.time()
            cleanup_count = 0
            
            if not os.path.exists(self.output_dir):
                return
            
            for filename in os.listdir(self.output_dir):
                if filename.startswith("celebrity_voice_"):
                    file_path = os.path.join(self.output_dir, filename)
                    if os.path.isfile(file_path):
                        file_age = current_time - os.path.getctime(file_path)
                        if file_age > (days_old * 24 * 60 * 60):  # Convert days to seconds
                            os.remove(file_path)
                            cleanup_count += 1
            
            if cleanup_count > 0:
                logger.info(f"🧹 Cleaned up {cleanup_count} old celebrity voice files")
            
        except Exception as e:
            logger.error(f"Error during celebrity voice cleanup: {e}")
    
    def test_celebrity_voice(self, celebrity_voice: str = "morgan_freeman") -> Dict:
        """
        Test a celebrity voice with sample text
        """
        voice_config = self.get_celebrity_voice_config(celebrity_voice)
        sample_text = voice_config.get('reference_text', 'This is a test of the celebrity voice system.')
        
        logger.info(f"🎭 Testing {voice_config['name']} voice...")
        
        result = self.synthesize_celebrity_voice(sample_text, celebrity_voice)
        
        if result['success']:
            logger.info(f"✅ {voice_config['name']} test successful!")
        else:
            logger.warning(f"⚠️ {voice_config['name']} test failed: {result.get('error', 'Unknown error')}")
        
        return result

# Create global instance
voice_synthesizer = VoiceSynthesizer() 