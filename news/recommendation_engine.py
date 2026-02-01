"""
Recommendation Engine for Personalized "For You" Feed
Implements weighted scoring algorithm with time decay
"""

import re
import math
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# SCORING WEIGHTS CONFIGURATION
# =============================================================================

WEIGHTS = {
    'keyword_match': 5,      # User's search history matches title/description
    'category_match': 3,     # News category matches user preferences
    'source_trust': 2,       # User has clicked this source before
    'recency_bonus': 2,      # Published within last 6 hours
    'engagement_boost': 1,   # High engagement (likes/comments/shares)
}

# Time decay coefficient (higher = faster decay)
TIME_DECAY_COEFFICIENT = 0.05

# Categories for cold start diversification
DEFAULT_CATEGORIES = ['technology', 'business', 'sports', 'entertainment', 'science', 'health']


# =============================================================================
# TEXT PROCESSING UTILITIES
# =============================================================================

def sanitize_text(text):
    """Clean and normalize text for comparison"""
    if not text:
        return ''
    # Convert to lowercase
    text = text.lower()
    # Remove special characters but keep spaces
    text = re.sub(r'[^\w\s]', ' ', text)
    # Remove extra whitespace
    text = ' '.join(text.split())
    return text


def tokenize_text(text):
    """
    Extract meaningful keywords from text
    Removes common stop words and returns unique tokens
    """
    if not text:
        return set()
    
    # Common English stop words to filter out
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare', 'ought',
        'used', 'it', 'its', 'this', 'that', 'these', 'those', 'i', 'you', 'he',
        'she', 'we', 'they', 'what', 'which', 'who', 'whom', 'whose', 'where',
        'when', 'why', 'how', 'all', 'each', 'every', 'both', 'few', 'more',
        'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
        'same', 'so', 'than', 'too', 'very', 'just', 'also', 'now', 'here',
        'there', 'then', 'once', 'news', 'says', 'said', 'new', 'latest'
    }
    
    # Clean and tokenize
    cleaned = sanitize_text(text)
    tokens = cleaned.split()
    
    # Filter: remove stop words and short tokens
    meaningful_tokens = {
        token for token in tokens 
        if token not in stop_words and len(token) > 2
    }
    
    return meaningful_tokens


def extract_keywords_from_history(search_history):
    """
    Extract and weight keywords from user's search history
    More recent searches get higher weight
    """
    keyword_weights = {}
    
    for i, search_term in enumerate(reversed(search_history[-20:])):  # Last 20 searches
        tokens = tokenize_text(search_term)
        # Recent searches get higher weight (1.0 to 0.5)
        weight = 1.0 - (i * 0.025)
        weight = max(weight, 0.5)
        
        for token in tokens:
            if token in keyword_weights:
                keyword_weights[token] = max(keyword_weights[token], weight)
            else:
                keyword_weights[token] = weight
    
    return keyword_weights


# =============================================================================
# SCORING FUNCTIONS
# =============================================================================

def calculate_time_decay(published_at):
    """
    Calculate time decay factor based on age of content
    Formula: 1.0 / (1.0 + hours_since_published * coefficient)
    
    Returns value between 0 and 1
    """
    if not published_at:
        return 0.5  # Default for unknown publish time
    
    try:
        if isinstance(published_at, str):
            # Parse ISO format datetime
            published_at = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
        
        now = timezone.now()
        if timezone.is_naive(published_at):
            published_at = timezone.make_aware(published_at)
        
        age = now - published_at
        hours = age.total_seconds() / 3600
        
        # Apply decay formula
        decay = 1.0 / (1.0 + hours * TIME_DECAY_COEFFICIENT)
        return max(decay, 0.1)  # Minimum 10% score retention
        
    except Exception as e:
        logger.warning(f"Time decay calculation error: {e}")
        return 0.5


def calculate_keyword_score(news_item, user_keywords):
    """
    Calculate score based on keyword matches between news and user interests
    """
    if not user_keywords:
        return 0
    
    # Combine title and description for matching
    news_text = f"{news_item.get('title', '')} {news_item.get('description', '')}"
    news_tokens = tokenize_text(news_text)
    
    score = 0
    for token in news_tokens:
        if token in user_keywords:
            score += user_keywords[token] * WEIGHTS['keyword_match']
    
    # Cap the keyword score to prevent single article dominance
    return min(score, WEIGHTS['keyword_match'] * 5)


def calculate_category_score(news_item, category_weights):
    """
    Calculate score based on category preferences
    """
    if not category_weights:
        return 0
    
    # Try to detect category from news content
    news_text = f"{news_item.get('title', '')} {news_item.get('description', '')}".lower()
    
    category_keywords = {
        'technology': ['tech', 'software', 'ai', 'artificial', 'startup', 'app', 'digital', 'computer', 'internet'],
        'sports': ['cricket', 'football', 'match', 'team', 'player', 'game', 'sport', 'tournament', 'league'],
        'business': ['market', 'stock', 'economy', 'company', 'business', 'trade', 'investment', 'finance'],
        'politics': ['government', 'minister', 'election', 'parliament', 'political', 'policy', 'vote'],
        'entertainment': ['movie', 'film', 'actor', 'actress', 'music', 'celebrity', 'bollywood', 'hollywood'],
        'science': ['research', 'study', 'scientist', 'discovery', 'space', 'climate', 'health', 'medical'],
    }
    
    score = 0
    for category, keywords in category_keywords.items():
        if category in category_weights:
            for keyword in keywords:
                if keyword in news_text:
                    score += category_weights[category] * WEIGHTS['category_match']
                    break  # Only count once per category
    
    return min(score, WEIGHTS['category_match'] * 3)


def calculate_source_score(news_item, trusted_sources):
    """
    Calculate score based on source trust (user has clicked before)
    """
    if not trusted_sources:
        return 0
    
    source = news_item.get('source', '').lower()
    
    for trusted in trusted_sources:
        if trusted.lower() in source or source in trusted.lower():
            return WEIGHTS['source_trust']
    
    return 0


def calculate_recency_score(published_at):
    """
    Bonus score for very recent news (< 6 hours old)
    """
    if not published_at:
        return 0
    
    try:
        if isinstance(published_at, str):
            published_at = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
        
        now = timezone.now()
        if timezone.is_naive(published_at):
            published_at = timezone.make_aware(published_at)
        
        age = now - published_at
        hours = age.total_seconds() / 3600
        
        if hours < 1:
            return WEIGHTS['recency_bonus'] * 2  # Double bonus for <1 hour
        elif hours < 6:
            return WEIGHTS['recency_bonus']
        elif hours < 12:
            return WEIGHTS['recency_bonus'] * 0.5
        
        return 0
        
    except Exception:
        return 0


def calculate_engagement_score(news_item):
    """
    Score based on engagement metrics (if available from local DB)
    """
    likes = news_item.get('likes', 0)
    comments = news_item.get('comments', 0)
    shares = news_item.get('shares', 0)
    
    # Logarithmic scaling to prevent viral content from dominating
    if likes + comments + shares > 0:
        engagement = math.log10(1 + likes + comments * 2 + shares * 3)
        return min(engagement * WEIGHTS['engagement_boost'], WEIGHTS['engagement_boost'] * 3)
    
    return 0


def calculate_total_score(news_item, user_interests):
    """
    Calculate the total personalization score for a news item
    
    Args:
        news_item: dict with title, description, source, published_at, etc.
        user_interests: dict with search_keywords, clicked_sources, category_weights
    
    Returns:
        float: Final weighted score
    """
    # Extract user interest data
    user_keywords = user_interests.get('keyword_weights', {})
    category_weights = user_interests.get('category_weights', {})
    trusted_sources = user_interests.get('clicked_sources', [])
    
    # Calculate individual scores
    keyword_score = calculate_keyword_score(news_item, user_keywords)
    category_score = calculate_category_score(news_item, category_weights)
    source_score = calculate_source_score(news_item, trusted_sources)
    recency_score = calculate_recency_score(news_item.get('published_at'))
    engagement_score = calculate_engagement_score(news_item)
    
    # Sum base score
    base_score = keyword_score + category_score + source_score + recency_score + engagement_score
    
    # Apply time decay
    decay_factor = calculate_time_decay(news_item.get('published_at'))
    final_score = base_score * decay_factor
    
    # Add some randomness for diversity (±10%)
    import random
    diversity_factor = random.uniform(0.9, 1.1)
    final_score *= diversity_factor
    
    return round(final_score, 2)


# =============================================================================
# MAIN FEED GENERATION
# =============================================================================

def get_user_interests(user):
    """
    Retrieve user interests from database or return empty structure
    """
    try:
        from .models import UserInterest
        interest = UserInterest.objects.get(user=user)
        
        # Build keyword weights from search history
        keyword_weights = extract_keywords_from_history(interest.search_keywords or [])
        
        return {
            'keyword_weights': keyword_weights,
            'category_weights': interest.category_weights or {},
            'clicked_sources': interest.clicked_sources or [],
            'has_history': bool(interest.search_keywords),
        }
    except Exception:
        return {
            'keyword_weights': {},
            'category_weights': {},
            'clicked_sources': [],
            'has_history': False,
        }


def get_cold_start_feed(page_size=12):
    """
    Generate feed for new users with no history
    Mix of trending news and diverse categories
    """
    from .news_api import fetch_trending_news, fetch_news
    
    articles = []
    
    # Get trending news (50% of feed)
    trending = fetch_trending_news(category='general', country='in', page_size=page_size // 2)
    if trending and trending.get('success'):
        for article in trending.get('articles', []):
            article['score'] = 10  # High base score for trending
            article['reason'] = 'Trending'
            articles.append(article)
    
    # Get diverse category news (50% of feed)
    categories_to_fetch = ['technology', 'sports', 'business']
    per_category = max(2, (page_size - len(articles)) // len(categories_to_fetch))
    
    for category in categories_to_fetch:
        cat_news = fetch_trending_news(category=category, country='in', page_size=per_category)
        if cat_news and cat_news.get('success'):
            for article in cat_news.get('articles', []):
                article['score'] = 5
                article['reason'] = f'{category.title()}'
                articles.append(article)
    
    # Shuffle to prevent category clustering
    import random
    random.shuffle(articles)
    
    return articles[:page_size]


def generate_personalized_feed(user, raw_news_list=None, page=1, page_size=12):
    """
    Main function to generate a personalized "For You" feed
    
    Args:
        user: Django User object (can be None for anonymous)
        raw_news_list: Optional pre-fetched news list
        page: Page number for pagination
        page_size: Number of items per page
    
    Returns:
        dict with articles, pagination info, and metadata
    """
    from .news_api import fetch_news, fetch_trending_news
    
    # Get user interests
    if user and user.is_authenticated:
        user_interests = get_user_interests(user)
    else:
        user_interests = {'has_history': False}
    
    # Cold start: return trending/diverse feed for new users
    if not user_interests.get('has_history'):
        articles = get_cold_start_feed(page_size * 2)  # Fetch extra for pagination
        
        # Paginate
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated = articles[start_idx:end_idx]
        
        return {
            'success': True,
            'articles': paginated,
            'is_cold_start': True,
            'page': page,
            'has_more': len(articles) > end_idx,
            'source': 'cold_start'
        }
    
    # Personalized feed for users with history
    all_articles = []
    
    # Fetch news if not provided
    if raw_news_list is None:
        # Get news based on user's top keywords
        top_keywords = sorted(
            user_interests['keyword_weights'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        for keyword, _ in top_keywords:
            keyword_news = fetch_news(keyword, page_size=5, page=1)
            if keyword_news and keyword_news.get('success'):
                all_articles.extend(keyword_news.get('articles', []))
        
        # Also add some trending for diversity
        trending = fetch_trending_news(category='general', country='in', page_size=6)
        if trending and trending.get('success'):
            all_articles.extend(trending.get('articles', []))
    else:
        all_articles = raw_news_list
    
    # Score each article
    scored_articles = []
    seen_titles = set()  # Deduplicate
    
    for article in all_articles:
        title = article.get('title', '')
        if title in seen_titles:
            continue
        seen_titles.add(title)
        
        score = calculate_total_score(article, user_interests)
        article['score'] = score
        article['reason'] = 'For You'
        scored_articles.append(article)
    
    # Sort by score (descending)
    scored_articles.sort(key=lambda x: x.get('score', 0), reverse=True)
    
    # Paginate
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated = scored_articles[start_idx:end_idx]
    
    return {
        'success': True,
        'articles': paginated,
        'is_cold_start': False,
        'page': page,
        'has_more': len(scored_articles) > end_idx,
        'source': 'personalized'
    }


def track_user_interaction(user, interaction_type, data):
    """
    Track user interactions to improve recommendations
    
    Args:
        user: Django User object
        interaction_type: 'search', 'click', 'like', 'share'
        data: dict with relevant data (query, source, category, etc.)
    """
    if not user or not user.is_authenticated:
        return
    
    try:
        from .models import UserInterest
        
        interest, created = UserInterest.objects.get_or_create(
            user=user,
            defaults={
                'search_keywords': [],
                'clicked_sources': [],
                'category_weights': {},
            }
        )
        
        if interaction_type == 'search':
            query = data.get('query', '')
            if query:
                keywords = list(interest.search_keywords or [])
                keywords.append(query)
                interest.search_keywords = keywords[-50:]  # Keep last 50
        
        elif interaction_type == 'click':
            source = data.get('source', '')
            if source:
                sources = list(interest.clicked_sources or [])
                if source not in sources:
                    sources.append(source)
                interest.clicked_sources = sources[-20:]  # Keep last 20
            
            # Update category weight
            category = data.get('category', '')
            if category:
                weights = dict(interest.category_weights or {})
                weights[category] = min(weights.get(category, 0) + 0.1, 1.0)
                interest.category_weights = weights
        
        interest.save()
        
    except Exception as e:
        logger.error(f"Failed to track user interaction: {e}")
