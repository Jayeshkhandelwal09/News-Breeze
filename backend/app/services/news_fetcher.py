import feedparser
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import logging
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class NewsArticle:
    """
    A class to represent a news article
    This makes it easier to work with news data
    """
    def __init__(self, title: str, summary: str, url: str, published: str, source: str):
        self.title = title
        self.summary = summary
        self.url = url
        self.published = published
        self.source = source
        self.ai_summary = None  # We'll add AI summary later
        self.audio_url = None   # We'll add voice audio later
    
    def to_dict(self) -> Dict:
        """Convert the article to a dictionary for easy JSON conversion"""
        return {
            "title": self.title,
            "summary": self.summary,
            "url": self.url,
            "published": self.published,
            "source": self.source,
            "ai_summary": self.ai_summary,
            "audio_url": self.audio_url
        }

class NewsFetcher:
    """
    A class that fetches news from various RSS feeds
    
    RSS = Really Simple Syndication
    It's a standard way websites share their latest content
    """
    
    def __init__(self):
        # Popular news RSS feeds
        # These are free and don't require API keys
        self.rss_feeds = {
            "BBC News": "http://feeds.bbci.co.uk/news/rss.xml",
            "CNN": "http://rss.cnn.com/rss/edition.rss",
            "Reuters": "http://feeds.reuters.com/reuters/topNews",
            "NPR": "https://feeds.npr.org/1001/rss.xml",
            "AP News": "https://rsshub.app/ap/topics/apf-topnews",
            "The Guardian": "https://www.theguardian.com/world/rss",
        }
    
    def clean_text(self, text: str) -> str:
        """
        Clean up messy text from RSS feeds
        Remove HTML tags, extra spaces, etc.
        """
        if not text:
            return ""
        
        # Remove HTML tags
        soup = BeautifulSoup(text, 'html.parser')
        clean_text = soup.get_text()
        
        # Remove extra whitespace
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        # Remove common RSS artifacts
        clean_text = re.sub(r'\[.*?\]', '', clean_text)  # Remove [brackets]
        clean_text = re.sub(r'<.*?>', '', clean_text)    # Remove any remaining HTML
        
        return clean_text
    
    def fetch_from_feed(self, feed_url: str, source_name: str, max_articles: int = 5) -> List[NewsArticle]:
        """
        Fetch news articles from a single RSS feed
        
        Args:
            feed_url: The RSS feed URL
            source_name: Name of the news source (like "BBC")
            max_articles: Maximum number of articles to fetch
        
        Returns:
            List of NewsArticle objects
        """
        articles = []
        
        try:
            logger.info(f"Fetching news from {source_name}...")
            
            # Parse the RSS feed
            feed = feedparser.parse(feed_url)
            
            # Check if feed was parsed successfully
            if feed.bozo:
                logger.warning(f"Feed {source_name} has issues, but trying to continue...")
            
            # Extract articles from the feed
            for entry in feed.entries[:max_articles]:
                try:
                    # Get article data
                    title = self.clean_text(entry.get('title', 'No title'))
                    summary = self.clean_text(entry.get('summary', entry.get('description', 'No summary')))
                    url = entry.get('link', '')
                    
                    # Handle different date formats
                    published = entry.get('published', entry.get('updated', 'Unknown date'))
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        published = datetime(*entry.published_parsed[:6]).strftime('%Y-%m-%d %H:%M:%S')
                    
                    # Create article object
                    article = NewsArticle(
                        title=title,
                        summary=summary,
                        url=url,
                        published=published,
                        source=source_name
                    )
                    
                    articles.append(article)
                    logger.info(f"✓ Fetched: {title[:50]}...")
                    
                except Exception as e:
                    logger.error(f"Error processing article from {source_name}: {e}")
                    continue
            
            logger.info(f"Successfully fetched {len(articles)} articles from {source_name}")
            
        except Exception as e:
            logger.error(f"Error fetching from {source_name}: {e}")
        
        return articles
    
    def fetch_latest_news(self, max_articles_per_source: int = 3) -> List[NewsArticle]:
        """
        Fetch latest news from all configured RSS feeds
        
        Args:
            max_articles_per_source: How many articles to get from each source
        
        Returns:
            List of all news articles
        """
        all_articles = []
        
        logger.info("Starting to fetch news from all sources...")
        
        for source_name, feed_url in self.rss_feeds.items():
            try:
                articles = self.fetch_from_feed(feed_url, source_name, max_articles_per_source)
                all_articles.extend(articles)
            except Exception as e:
                logger.error(f"Failed to fetch from {source_name}: {e}")
                continue
        
        logger.info(f"Total articles fetched: {len(all_articles)}")
        return all_articles
    
    def get_article_content(self, url: str) -> Optional[str]:
        """
        Get the full content of an article (for better summarization)
        This is optional - we can work with RSS summaries too
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try to find the main content
            # Different news sites use different HTML structures
            content_selectors = [
                'article', '.article-body', '.story-body', 
                '.entry-content', '.post-content', 'main'
            ]
            
            for selector in content_selectors:
                content_div = soup.select_one(selector)
                if content_div:
                    # Extract text and clean it
                    text = content_div.get_text()
                    return self.clean_text(text)
            
            # Fallback: get all paragraph text
            paragraphs = soup.find_all('p')
            text = ' '.join([p.get_text() for p in paragraphs])
            return self.clean_text(text)
            
        except Exception as e:
            logger.error(f"Error fetching article content from {url}: {e}")
            return None

# Create a global instance
news_fetcher = NewsFetcher() 