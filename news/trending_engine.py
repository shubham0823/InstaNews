"""
Trending Engine with Velocity-Based Scoring
Calculates trending status based on engagement velocity, not total counts.
Separates results by geo_category ('india' vs 'global').
"""

from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Q, F, FloatField, ExpressionWrapper
from django.db.models.functions import Greatest

import logging

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

# Time window for trending calculation
TRENDING_WINDOW_HOURS = 24

# Minimum age in hours to prevent division by near-zero
MIN_AGE_HOURS = 0.5

# Engagement weights for velocity calculation
ENGAGEMENT_WEIGHTS = {
    'likes': 1.0,
    'comments': 2.0,
    'shares': 3.0,
    'views': 0.1,
}


# =============================================================================
# VELOCITY SCORING
# =============================================================================

def _calculate_velocity(news_obj, now=None):
    """
    Calculate velocity score for a single news post.
    Velocity = weighted_engagement / hours_since_upload

    Args:
        news_obj: News model instance (annotated with engagement counts)
        now: current time (optional, for testing)

    Returns:
        float: velocity score
    """
    if now is None:
        now = timezone.now()

    # Calculate age in hours
    age = now - news_obj.created_at
    hours = max(age.total_seconds() / 3600, MIN_AGE_HOURS)

    # Calculate weighted engagement
    likes_count = getattr(news_obj, 'likes_count', 0) or news_obj.likes.count()
    comments_count = getattr(news_obj, 'comments_count', 0) or news_obj.comments.count()
    shares_count = getattr(news_obj, 'shares_count', 0) or news_obj.shares.count()
    views_count = news_obj.views or 0

    weighted_engagement = (
        likes_count * ENGAGEMENT_WEIGHTS['likes'] +
        comments_count * ENGAGEMENT_WEIGHTS['comments'] +
        shares_count * ENGAGEMENT_WEIGHTS['shares'] +
        views_count * ENGAGEMENT_WEIGHTS['views']
    )

    velocity = weighted_engagement / hours
    return round(velocity, 2)


def get_trending_posts(geo_category, limit=10):
    """
    Get the top trending user-uploaded posts for a geo_category.
    Uses velocity scoring on posts from the last 24 hours.

    Args:
        geo_category: 'india' or 'global'
        limit: max number of posts to return

    Returns:
        list of dicts: [{news_obj, velocity_score}, ...]
    """
    from .models import News

    now = timezone.now()
    cutoff = now - timedelta(hours=TRENDING_WINDOW_HOURS)

    # Get recent posts with engagement counts
    posts = (
        News.objects
        .filter(geo_category=geo_category, created_at__gte=cutoff)
        .select_related('author', 'author__profile')
        .prefetch_related('images', 'likes', 'comments', 'shares', 'hashtags')
        .annotate(
            likes_count=Count('likes'),
            comments_count=Count('comments'),
            shares_count=Count('shares'),
        )
    )

    # Calculate velocity for each post and sort
    scored_posts = []
    for post in posts:
        velocity = _calculate_velocity(post, now)
        scored_posts.append({
            'news': post,
            'velocity': velocity,
        })

    # Sort by velocity (descending)
    scored_posts.sort(key=lambda x: x['velocity'], reverse=True)

    return scored_posts[:limit]


def get_trending_hashtags(geo_category, limit=5):
    """
    Get the top trending hashtags for a geo_category.
    For each hashtag, sums the velocity scores of all posts containing it
    from the last 24 hours.

    Args:
        geo_category: 'india' or 'global'
        limit: max number of hashtags to return

    Returns:
        list of dicts: [{name, score, post_count}, ...]
    """
    from .models import News, Hashtag

    now = timezone.now()
    cutoff = now - timedelta(hours=TRENDING_WINDOW_HOURS)

    # Get recent posts for this geo_category
    recent_posts = (
        News.objects
        .filter(geo_category=geo_category, created_at__gte=cutoff)
        .prefetch_related('likes', 'comments', 'shares', 'hashtags')
        .annotate(
            likes_count=Count('likes'),
            comments_count=Count('comments'),
            shares_count=Count('shares'),
        )
    )

    # Build hashtag-to-velocity map
    hashtag_scores = {}  # {hashtag_name: {score: float, post_count: int}}

    for post in recent_posts:
        velocity = _calculate_velocity(post, now)
        for hashtag in post.hashtags.all():
            tag_name = hashtag.name
            if tag_name not in hashtag_scores:
                hashtag_scores[tag_name] = {'score': 0.0, 'post_count': 0}
            hashtag_scores[tag_name]['score'] += velocity
            hashtag_scores[tag_name]['post_count'] += 1

    # Sort by score and return top N
    sorted_tags = sorted(
        hashtag_scores.items(),
        key=lambda x: x[1]['score'],
        reverse=True
    )[:limit]

    return [
        {
            'name': name,
            'score': round(data['score'], 1),
            'post_count': data['post_count'],
        }
        for name, data in sorted_tags
    ]


def get_trending_data():
    """
    Convenience function: returns all trending data for both categories.
    Used by the landing page view.

    Returns:
        dict with india_hashtags, global_hashtags, india_posts, global_posts
    """
    return {
        'india_hashtags': get_trending_hashtags('india', limit=5),
        'global_hashtags': get_trending_hashtags('global', limit=5),
        'india_posts': get_trending_posts('india', limit=6),
        'global_posts': get_trending_posts('global', limit=6),
    }
