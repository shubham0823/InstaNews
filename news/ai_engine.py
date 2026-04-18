import random
import time
import threading
from django.db import transaction

def _run_mock_nlp_analysis(news_id):
    """
    Mock AI NLP analysis that runs in a background thread.
    Simulates testing for Sensationalism and Emotional Polarity.
    """
    time.sleep(2)  # Simulate API network delay
    
    from .models import News
    
    try:
        news = News.objects.get(id=news_id)
        
        content = news.content.lower()
        title = news.title.lower()
        full_text = f"{title} {content}"
        
        # Mock NLP Logic: Check for sensationalist/emotional keywords
        sensational_keywords = ['horrific', 'evil', 'destroyed', 'insane', 'shocking', 'mind-blowing', 'devastating', 'slams', 'destroys']
        emotional_keywords = ['angry', 'furious', 'outraged', 'terrified', 'scared', 'crying', 'weeping', 'heartbreaking', 'miracle']
        
        sensational_count = sum(1 for word in sensational_keywords if word in full_text)
        emotional_count = sum(1 for word in emotional_keywords if word in full_text)
        
        # Calculate AI Sensationalism (0 = purely factual, 100 = completely sensational)
        sensationalism_score = min(100, sensational_count * 15 + random.randint(0, 10))
        factual_tone = 100 - sensationalism_score
        
        # Calculate Emotional Polarity (0 = neutral, 100 = highly emotional)
        emotional_tone = min(100, emotional_count * 20 + random.randint(0, 15))
        
        news.ai_factual_tone = factual_tone
        news.ai_emotional_tone = emotional_tone
        news.is_ai_analyzed = True
        
        news.save(update_fields=['ai_factual_tone', 'ai_emotional_tone', 'is_ai_analyzed'])
        
    except News.DoesNotExist:
        pass


def analyze_news_text(news_id):
    """
    Triggers the AI text analysis in a background thread.
    """
    thread = threading.Thread(target=_run_mock_nlp_analysis, args=(news_id,))
    thread.daemon = True
    thread.start()
