from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import logging
import torch
from typing import Optional, Dict
import warnings
import re

# Suppress some warnings for cleaner output
warnings.filterwarnings("ignore", category=UserWarning)

logger = logging.getLogger(__name__)

try:
    from transformers import pipeline, BartTokenizer, BartForConditionalGeneration
    TRANSFORMERS_AVAILABLE = True
    logger.info("✅ Transformers library loaded successfully")
except ImportError as e:
    TRANSFORMERS_AVAILABLE = False
    logger.warning(f"🚨 Transformers not available: {e}")

class AISummarizer:
    """
    AI Summarization Service using Hugging Face Transformers
    
    This class uses pre-trained AI models to automatically summarize news articles.
    Think of it as an AI reading assistant that extracts the key points.
    """
    
    def __init__(self):
        # Use a smaller, faster model for quicker testing
        self.model_name = "facebook/bart-base"  # Much smaller than bart-large-cnn
        self.model = None
        self.tokenizer = None
        self.summarizer = None
        self.is_loaded = False
        
        # Configuration
        self.max_input_length = 1024  # Maximum input text length
        self.default_summary_length = 100  # Default summary length
        self.min_summary_length = 30   # Minimum summary length
        
        logger.info(f"🤖 AI Summarizer initialized with model: {self.model_name}")
    
    def load_model(self) -> bool:
        """
        Load the AI model for summarization
        This will download the model on first use (~500MB for bart-base vs 1.6GB for bart-large-cnn)
        """
        if not TRANSFORMERS_AVAILABLE:
            logger.error("❌ Cannot load model: transformers library not available")
            return False
        
        if self.is_loaded:
            logger.info("✅ Model already loaded")
            return True
        
        try:
            logger.info(f"🚀 Loading AI model: {self.model_name}")
            logger.info("📥 This will download the model on first use (~500MB)")
            
            # Create summarization pipeline with smaller model
            self.summarizer = pipeline(
                "summarization",
                model=self.model_name,
                tokenizer=self.model_name,
                framework="pt",  # Use PyTorch
                device=-1  # Use CPU (set to 0 for GPU)
            )
            
            self.is_loaded = True
            logger.info("✅ AI model loaded successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load AI model: {e}")
            self.is_loaded = False
            return False
    
    def preprocess_text(self, text: str) -> str:
        """
        Prepare text for summarization
        Clean and truncate if necessary
        """
        if not text:
            return ""
        
        # Remove extra whitespace
        text = " ".join(text.split())
        
        # Truncate if too long (AI models have limits)
        if len(text) > self.max_input_length * 4:  # Rough character estimate
            text = text[:self.max_input_length * 4]
            # Try to end at a sentence
            last_period = text.rfind('.')
            if last_period > len(text) * 0.8:  # If period is in last 20%
                text = text[:last_period + 1]
        
        return text
    
    def summarize_text(self, text: str, custom_length: Optional[int] = None) -> Dict[str, any]:
        """
        Summarize a piece of text using AI
        
        Args:
            text: The text to summarize
            custom_length: Custom maximum length for summary
        
        Returns:
            Dictionary with summary and metadata
        """
        if not self.is_loaded:
            logger.warning("AI model not loaded, attempting to load...")
            if not self.load_model():
                return {
                    "success": False,
                    "error": "AI model failed to load",
                    "summary": text[:200] + "..." if len(text) > 200 else text,
                    "fallback": True
                }
        
        try:
            # Preprocess the text
            processed_text = self.preprocess_text(text)
            
            if len(processed_text) < 50:  # Too short to summarize meaningfully
                return {
                    "success": True,
                    "summary": processed_text,
                    "original_length": len(text),
                    "summary_length": len(processed_text),
                    "compression_ratio": 1.0,
                    "note": "Text too short for summarization"
                }
            
            # Set summary length
            max_len = custom_length if custom_length else self.default_summary_length
            min_len = max(self.min_summary_length, max_len - 10)
            
            logger.info(f"🤖 AI is summarizing text of {len(processed_text)} characters...")
            
            # Generate summary using AI
            summary_result = self.summarizer(
                processed_text,
                max_length=max_len,
                min_length=min_len,
                do_sample=False,  # Deterministic output
                truncation=True
            )
            
            summary = summary_result[0]['summary_text']
            
            # Calculate compression metrics
            compression_ratio = len(summary) / len(processed_text)
            
            logger.info(f"✅ AI summarization complete! Compressed by {compression_ratio:.1%}")
            
            return {
                "success": True,
                "summary": summary,
                "original_length": len(text),
                "summary_length": len(summary),
                "compression_ratio": compression_ratio,
                "model_used": self.model_name
            }
            
        except Exception as e:
            logger.error(f"❌ Error during AI summarization: {e}")
            
            # Fallback: Return first few sentences
            sentences = text.split('.')[:3]
            fallback_summary = '.'.join(sentences) + '.'
            
            return {
                "success": False,
                "error": str(e),
                "summary": fallback_summary,
                "fallback": True,
                "note": "Used fallback summarization due to AI error"
            }
    
    def summarize_article(self, article_data: Dict) -> Dict:
        """
        Summarize a news article (title + content)
        
        Args:
            article_data: Dictionary with 'title', 'summary', etc.
        
        Returns:
            Dictionary with AI summary
        """
        # Combine title and existing summary for better context
        title = article_data.get('title', '')
        existing_summary = article_data.get('summary', '')
        
        # Create combined text for summarization
        combined_text = f"{title}. {existing_summary}"
        
        logger.info(f"📰 Summarizing article: {title[:50]}...")
        
        # Get AI summary
        result = self.summarize_text(combined_text)
        
        if result['success']:
            logger.info(f"✅ Article summarized successfully!")
        else:
            logger.warning(f"⚠️ Article summarization had issues, using fallback")
        
        return result
    
    def batch_summarize(self, articles: list, max_concurrent: int = 3) -> list:
        """
        Summarize multiple articles efficiently
        
        Args:
            articles: List of article dictionaries
            max_concurrent: Maximum articles to process simultaneously
        
        Returns:
            List of articles with AI summaries added
        """
        logger.info(f"🔄 Starting batch summarization of {len(articles)} articles...")
        
        summarized_articles = []
        
        for i, article in enumerate(articles, 1):
            logger.info(f"Processing article {i}/{len(articles)}")
            
            # Get AI summary
            summary_result = self.summarize_article(article)
            
            # Add AI summary to article
            article_copy = article.copy()
            article_copy['ai_summary'] = summary_result['summary']
            article_copy['ai_summary_metadata'] = {
                'success': summary_result['success'],
                'compression_ratio': summary_result.get('compression_ratio', 0),
                'model_used': summary_result.get('model_used', 'fallback')
            }
            
            summarized_articles.append(article_copy)
        
        logger.info(f"✅ Batch summarization complete! Processed {len(summarized_articles)} articles")
        return summarized_articles

# Create global instance
ai_summarizer = AISummarizer() 