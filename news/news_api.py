"""
News API Utility Module
Handles fetching news from NewsAPI and Google News RSS with caching
"""

import requests
import feedparser
from django.core.cache import cache
from datetime import datetime, timedelta
import logging
import re
import os
from html import unescape

logger = logging.getLogger(__name__)

# API Configuration
NEWS_API_KEY = os.environ.get('NEWS_API_KEY', '')
NEWS_API_BASE_URL = 'https://newsapi.org/v2'
GOOGLE_NEWS_RSS_URL = 'https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en'

# Cache settings
CACHE_TIMEOUT = 600  # 10 minutes


def clean_html(text):
    """Remove HTML tags and unescape HTML entities"""
    if not text:
        return ''
    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', '', text)
    # Unescape HTML entities
    clean = unescape(clean)
    return clean.strip()


def fetch_from_newsapi(query, page_size=12, page=1):
    """
    Fetch news from NewsAPI
    
    Args:
        query: Search query (state/country name)
        page_size: Number of results per page
        page: Page number
    
    Returns:
        dict with 'articles' list and 'total_results' count
    """
    try:
        url = f"{NEWS_API_BASE_URL}/everything"
        params = {
            'q': query,
            'apiKey': NEWS_API_KEY,
            'pageSize': page_size,
            'page': page,
            'language': 'en',
            'sortBy': 'publishedAt'
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'ok':
                articles = []
                for article in data.get('articles', []):
                    articles.append({
                        'title': article.get('title') or 'No Title',
                        'description': article.get('description') or '',
                        'content': article.get('content') or '',
                        'url': article.get('url') or '#',
                        'image': article.get('urlToImage') or '',
                        'source': (article.get('source') or {}).get('name') or 'Unknown',
                        'author': article.get('author') or 'Unknown',
                        'published_at': article.get('publishedAt') or '',
                    })
                return {
                    'success': True,
                    'articles': articles,
                    'total_results': data.get('totalResults', 0),
                    'source': 'newsapi'
                }
        
        # API error or rate limit
        logger.warning(f"NewsAPI returned status {response.status_code}: {response.text}")
        return None
        
    except requests.RequestException as e:
        logger.error(f"NewsAPI request failed: {e}")
        return None


def fetch_from_google_rss(query, max_items=12):
    """
    Fetch news from Google News RSS feed (Fallback)
    
    Args:
        query: Search query
        max_items: Maximum number of items to fetch
    
    Returns:
        dict with 'articles' list
    """
    try:
        url = GOOGLE_NEWS_RSS_URL.format(query=query.replace(' ', '+'))
        feed = feedparser.parse(url)
        
        if feed.bozo:
            logger.warning(f"Google News RSS parse error: {feed.bozo_exception}")
        
        articles = []
        for entry in feed.entries[:max_items]:
            # Parse published date
            published = ''
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6]).isoformat()
            
            # Extract source from title (Google News format: "Title - Source")
            title = entry.get('title', 'No Title')
            source = 'Google News'
            if ' - ' in title:
                parts = title.rsplit(' - ', 1)
                title = parts[0]
                source = parts[1] if len(parts) > 1 else 'Google News'
            
            articles.append({
                'title': title,
                'description': clean_html(entry.get('summary', '')),
                'content': clean_html(entry.get('summary', '')),
                'url': entry.get('link', '#'),
                'image': '',  # RSS doesn't provide images
                'source': source,
                'author': source,
                'published_at': published,
            })
        
        return {
            'success': True,
            'articles': articles,
            'total_results': len(articles),
            'source': 'google_rss'
        }
        
    except Exception as e:
        logger.error(f"Google News RSS fetch failed: {e}")
        return None


def fetch_news(query, page_size=12, page=1, use_cache=True):
    """
    Main function to fetch news with caching and fallback
    
    Args:
        query: Search query (state/country name)
        page_size: Number of results
        page: Page number
        use_cache: Whether to use cached results
    
    Returns:
        dict with news data or error info
    """
    # Generate cache key
    cache_key = f"news_{query}_{page_size}_{page}".replace(' ', '_').lower()
    
    # Check cache first
    if use_cache:
        cached = cache.get(cache_key)
        if cached:
            cached['from_cache'] = True
            return cached
    
    # Try NewsAPI first
    result = fetch_from_newsapi(query, page_size, page)
    
    # Fallback to Google News RSS if NewsAPI fails
    if not result:
        logger.info(f"Falling back to Google News RSS for query: {query}")
        result = fetch_from_google_rss(query, page_size)
    
    # If we got results, cache them
    if result and result.get('success'):
        result['from_cache'] = False
        cache.set(cache_key, result, CACHE_TIMEOUT)
        return result
    
    # Return empty result if all sources fail
    return {
        'success': False,
        'articles': [],
        'total_results': 0,
        'error': 'Unable to fetch news at this time',
        'source': None,
        'from_cache': False
    }


def fetch_india_news(state_name, page_size=12, page=1):
    """
    Fetch news for Indian state/UT
    Adds 'India' context for better results
    """
    query = f"{state_name} India news"
    return fetch_news(query, page_size, page)


def fetch_world_news(country_name, page_size=12, page=1):
    """
    Fetch news for a specific country
    """
    query = f"{country_name} news"
    return fetch_news(query, page_size, page)


def fetch_trending_news(category='general', country='in', page_size=10):
    """
    Fetch top headlines for trending section
    """
    cache_key = f"trending_{category}_{country}_{page_size}"
    
    cached = cache.get(cache_key)
    if cached:
        cached['from_cache'] = True
        return cached
    
    try:
        url = f"{NEWS_API_BASE_URL}/top-headlines"
        params = {
            'apiKey': NEWS_API_KEY,
            'country': country,
            'category': category,
            'pageSize': page_size
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'ok':
                articles = []
                for article in data.get('articles', []):
                    articles.append({
                        'title': article.get('title') or 'No Title',
                        'description': article.get('description') or '',
                        'url': article.get('url') or '#',
                        'image': article.get('urlToImage') or '',
                        'source': (article.get('source') or {}).get('name') or 'Unknown',
                        'published_at': article.get('publishedAt') or '',
                    })
                
                result = {
                    'success': True,
                    'articles': articles,
                    'total_results': data.get('totalResults', 0),
                    'source': 'newsapi',
                    'from_cache': False
                }
                cache.set(cache_key, result, CACHE_TIMEOUT)
                return result
        
        return None
        
    except Exception as e:
        logger.error(f"Trending news fetch failed: {e}")
        return None
