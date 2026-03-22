"""
Geo-Categorization Engine for User-Uploaded News Posts
Determines whether a post is 'india' or 'global' using a 4-technique weighted pipeline.
"""

import re

# =============================================================================
# KEYWORD DICTIONARIES
# =============================================================================

INDIA_KEYWORDS = {
    # States
    'andhra pradesh', 'arunachal pradesh', 'assam', 'bihar', 'chhattisgarh',
    'goa', 'gujarat', 'haryana', 'himachal pradesh', 'jharkhand', 'karnataka',
    'kerala', 'madhya pradesh', 'maharashtra', 'manipur', 'meghalaya',
    'mizoram', 'nagaland', 'odisha', 'punjab', 'rajasthan', 'sikkim',
    'tamil nadu', 'telangana', 'tripura', 'uttar pradesh', 'uttarakhand',
    'west bengal',
    # Major cities
    'mumbai', 'delhi', 'bangalore', 'bengaluru', 'hyderabad', 'chennai',
    'kolkata', 'pune', 'ahmedabad', 'jaipur', 'lucknow', 'kanpur',
    'nagpur', 'indore', 'bhopal', 'patna', 'vadodara', 'ludhiana',
    'agra', 'varanasi', 'surat', 'coimbatore', 'kochi', 'chandigarh',
    'guwahati', 'thiruvananthapuram', 'visakhapatnam', 'noida', 'gurugram',
    'gurgaon', 'faridabad', 'nashik', 'ranchi', 'shimla', 'dehradun',
    'amritsar', 'jodhpur', 'mysore', 'mysuru', 'mangalore', 'mangaluru',
    # UTs
    'jammu', 'kashmir', 'ladakh', 'puducherry', 'pondicherry', 'lakshadweep',
    'andaman', 'nicobar', 'daman', 'diu', 'dadra', 'nagar haveli',
    # Political / Institutional
    'lok sabha', 'rajya sabha', 'indian parliament', 'niti aayog',
    'supreme court of india', 'rbi', 'reserve bank', 'sebi', 'isro',
    'drdo', 'bcci', 'ipl', 'modi', 'bjp', 'congress', 'nda', 'upa',
    'aap', 'aam aadmi', 'rahul gandhi', 'amit shah',
    # General India terms
    'india', 'indian', 'bharat', 'hindustan', 'desi',
    'rupee', 'nifty', 'sensex', 'bse', 'nse',
    'bollywood', 'cricket india', 'team india',
}

INDIA_HASHTAG_PATTERNS = {
    # Direct matches (case-insensitive)
    'india', 'indian', 'bharat', 'bharatiya', 'desi',
    'makeinindia', 'digitalindia', 'indianews', 'indiatoday',
    'modi', 'bjp', 'congress', 'aap', 'nda',
    'ipl', 'bcci', 'teamindia', 'cricketindia',
    'bollywood', 'tollywood', 'kollywood',
    'mumbai', 'delhi', 'bangalore', 'bengaluru', 'hyderabad',
    'chennai', 'kolkata', 'pune', 'jaipur', 'lucknow',
    'delhipolice', 'delhincr', 'mumbaipolice',
    'nifty', 'sensex', 'bse', 'nse', 'rbi',
    'isro', 'drdo', 'upsc',
    'loksabha', 'rajyasabha',
}

# State/city name patterns that may appear as part of hashtags
INDIA_HASHTAG_SUBSTRINGS = [
    'delhi', 'mumbai', 'bangalore', 'bengaluru', 'hyderabad', 'chennai',
    'kolkata', 'pune', 'jaipur', 'lucknow', 'india', 'bharat',
    'gujarat', 'rajasthan', 'maharashtra', 'karnataka', 'kerala',
    'tamilnadu', 'telangana', 'bihar', 'punjab', 'haryana',
    'kashmir', 'goa', 'assam',
]

GLOBAL_KEYWORDS = {
    'united nations', 'un summit', 'nato', 'eu', 'european union',
    'g7', 'g20', 'imf', 'world bank', 'who', 'world health',
    'white house', 'pentagon', 'kremlin', 'downing street',
    'wall street', 'silicon valley', 'nasdaq', 'nyse',
    'olympics', 'fifa', 'nba', 'nfl', 'formula 1', 'f1',
    'hollywood', 'grammy', 'oscar', 'emmy',
    'climate change', 'global warming', 'carbon emissions',
    'cryptocurrency', 'bitcoin', 'ethereum',
    'spacex', 'nasa', 'esa',
    'apple', 'google', 'microsoft', 'amazon', 'meta', 'tesla',
    'ukraine', 'russia war', 'middle east', 'gaza',
}

GLOBAL_HASHTAG_PATTERNS = {
    'worldnews', 'globalnews', 'international', 'breaking',
    'un', 'unsummit', 'nato', 'eu', 'europeanunion',
    'g7', 'g20summit', 'imf', 'worldbank', 'who',
    'usa', 'uk', 'china', 'russia', 'japan', 'germany', 'france',
    'ukraine', 'middleeast', 'africa',
    'climatechange', 'globalwarming',
    'olympics', 'fifa', 'worldcup',
    'bitcoin', 'crypto', 'ethereum',
    'spacex', 'nasa',
    'hollywood', 'oscars', 'grammy',
    'wallstreet', 'nasdaq',
}

# Indian timezone identifiers
INDIA_TIMEZONES = {'Asia/Kolkata', 'Asia/Calcutta', 'IST'}


# =============================================================================
# SCORING FUNCTIONS
# =============================================================================

def _score_hashtags(news_obj):
    """
    Technique 1: Analyze hashtags for region-specific patterns.
    Returns (india_score, global_score)
    """
    india_score = 0.0
    global_score = 0.0

    hashtags = news_obj.hashtags.all()
    for hashtag in hashtags:
        tag_lower = hashtag.name.lower()

        # Exact match check
        if tag_lower in INDIA_HASHTAG_PATTERNS:
            india_score += 1.0
        elif tag_lower in GLOBAL_HASHTAG_PATTERNS:
            global_score += 1.0
        else:
            # Substring match check
            for substr in INDIA_HASHTAG_SUBSTRINGS:
                if substr in tag_lower:
                    india_score += 0.7
                    break

    return india_score, global_score


def _score_content(news_obj):
    """
    Technique 2: Scan title + content for India/Global keywords.
    Returns (india_score, global_score)
    """
    text = f"{news_obj.title} {news_obj.content}".lower()
    india_score = 0.0
    global_score = 0.0

    for keyword in INDIA_KEYWORDS:
        if keyword in text:
            india_score += 1.0

    for keyword in GLOBAL_KEYWORDS:
        if keyword in text:
            global_score += 1.0

    # Normalize to prevent keyword-count dominance
    india_score = min(india_score, 10.0)
    global_score = min(global_score, 10.0)

    return india_score, global_score


def _score_profile_country(news_obj):
    """
    Technique 3: Check the author's registered country.
    Returns (india_score, global_score)
    """
    try:
        country = news_obj.author.profile.country.lower().strip()
    except Exception:
        return 0.5, 0.5  # Neutral if no profile

    if country in ('india', 'in', 'भारत', 'bharat'):
        return 1.0, 0.0
    elif country == '' or country == 'india':  # default value
        return 0.7, 0.3
    else:
        return 0.0, 1.0


def _score_timezone(news_obj):
    """
    Technique 4: Timezone inference from user profile.
    Returns (india_score, global_score)
    """
    try:
        tz = news_obj.author.profile.timezone.strip()
    except Exception:
        return 0.5, 0.5

    if not tz:
        return 0.5, 0.5

    if tz in INDIA_TIMEZONES or 'kolkata' in tz.lower() or 'calcutta' in tz.lower():
        return 1.0, 0.0
    else:
        return 0.0, 1.0


# =============================================================================
# MAIN CATEGORIZATION FUNCTION
# =============================================================================

# Weights for each technique (must sum to 1.0)
WEIGHTS = {
    'hashtags': 0.40,
    'content': 0.30,
    'profile': 0.20,
    'timezone': 0.10,
}


def categorize_post(news_obj):
    """
    Main categorization function. Analyzes a News object using 4 weighted
    techniques and returns 'india' or 'global'.

    Args:
        news_obj: News model instance (must be saved with hashtags processed)

    Returns:
        str: 'india' or 'global'
    """
    # Gather scores from each technique
    h_india, h_global = _score_hashtags(news_obj)
    c_india, c_global = _score_content(news_obj)
    p_india, p_global = _score_profile_country(news_obj)
    t_india, t_global = _score_timezone(news_obj)

    # Normalize each technique's scores to 0-1 range
    def _normalize(india, globe):
        total = india + globe
        if total == 0:
            return 0.5, 0.5
        return india / total, globe / total

    h_india, h_global = _normalize(h_india, h_global)
    c_india, c_global = _normalize(c_india, c_global)
    p_india, p_global = _normalize(p_india, p_global)
    t_india, t_global = _normalize(t_india, t_global)

    # Weighted sum
    india_total = (
        h_india * WEIGHTS['hashtags'] +
        c_india * WEIGHTS['content'] +
        p_india * WEIGHTS['profile'] +
        t_india * WEIGHTS['timezone']
    )

    global_total = (
        h_global * WEIGHTS['hashtags'] +
        c_global * WEIGHTS['content'] +
        p_global * WEIGHTS['profile'] +
        t_global * WEIGHTS['timezone']
    )

    return 'india' if india_total >= global_total else 'global'


def update_hashtag_affinity(news_obj):
    """
    Update the geo_affinity of hashtags based on the post's geo_category.
    Called after categorization to enrich hashtag metadata.
    """
    geo = news_obj.geo_category
    for hashtag in news_obj.hashtags.all():
        if not hashtag.geo_affinity:
            hashtag.geo_affinity = geo
            hashtag.save(update_fields=['geo_affinity'])
