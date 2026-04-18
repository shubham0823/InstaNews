from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    avatar = models.ImageField(upload_to='avatars/', default='avatars/default.svg')
    following = models.ManyToManyField('self', symmetrical=False, related_name='followers', blank=True)
    country = models.CharField(max_length=100, default='India', blank=True)
    timezone = models.CharField(max_length=50, blank=True)
    
    # Trust Score Engine (Reputation System)
    trust_weight = models.FloatField(default=1.0)
    lifetime_agreements = models.IntegerField(default=0)
    lifetime_disagreements = models.IntegerField(default=0)
    voting_diversity = models.JSONField(default=dict, blank=True)
    is_echo_chamber_penalized = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s profile"

class Hashtag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    total_count = models.IntegerField(default=0)
    geo_affinity = models.CharField(max_length=10, blank=True, default='')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-total_count']

class News(models.Model):
    NEWS_TYPES = (
        ('short', 'Short Format'),
        ('long', 'Long Format'),
    )

    GEO_CATEGORIES = (
        ('india', 'India'),
        ('global', 'Global'),
    )

    author = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    news_type = models.CharField(max_length=10, choices=NEWS_TYPES)
    likes = models.ManyToManyField(User, related_name='liked_news', blank=True)
    views = models.IntegerField(default=0)
    geo_category = models.CharField(max_length=10, choices=GEO_CATEGORIES, default='india')
    
    # For long format news
    video = models.FileField(upload_to='news_videos/', null=True, blank=True)
    hashtags = models.ManyToManyField(Hashtag, related_name='news_posts', blank=True)
    tagged_users = models.ManyToManyField(User, related_name='tagged_in_news', blank=True)

    # Trust & AI Bias System
    ai_factual_tone = models.IntegerField(default=0)  # 0-100 Sensationalism/Factual
    ai_emotional_tone = models.IntegerField(default=0) # 0-100 Emotional Polarity
    is_ai_analyzed = models.BooleanField(default=False)
    is_frozen_by_brigading = models.BooleanField(default=False)

    def get_trust_score(self):
        """Returns the weighted consensus trust percentage based on user TrustVotes."""
        votes = self.trust_votes.all()
        if not votes.exists():
            return 0
        
        # Calculate weighted sum
        total_weight = sum(v.user.profile.trust_weight for v in votes)
        if total_weight == 0:
            return 0
            
        verifications = votes.filter(vote_type='verify')
        verified_weight = sum(v.user.profile.trust_weight for v in verifications)
        
        return int((verified_weight / total_weight) * 100)

    def get_top_dispute_reason(self):
        """Returns the most common dispute reason if more than 30% weighted votes are disputes."""
        votes = self.trust_votes.all()
        if not votes.exists():
            return None
            
        total_weight = sum(v.user.profile.trust_weight for v in votes)
        if total_weight == 0:
            return None
            
        disputes = votes.filter(vote_type='dispute')
        disputed_weight = sum(v.user.profile.trust_weight for v in disputes)
        
        if disputed_weight / total_weight >= 0.3:
            # Aggregate weights by reason
            reasons = {}
            for dispute in disputes:
                reasons[dispute.dispute_reason] = reasons.get(dispute.dispute_reason, 0) + dispute.user.profile.trust_weight
                
            if reasons:
                # Get the reason with the highest combined weight
                top_reason_key = max(reasons, key=reasons.get)
                if top_reason_key != 'none':
                    reason_dict = dict(TrustVote.REASON_CHOICES)
                    return reason_dict.get(top_reason_key, 'Disputed')
        return None

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            # Create notification for tagged users
            for user in self.tagged_users.all():
                if user != self.author:
                    Notification.objects.create(
                        recipient=user,
                        notification_type='tag',
                        actor=self.author,
                        content_type=ContentType.objects.get_for_model(self),
                        object_id=self.id
                    )

    def process_hashtags(self, hashtag_text):
        # Remove existing hashtags
        self.hashtags.clear()
        
        # Process new hashtags
        if hashtag_text:
            hashtag_list = hashtag_text.split()
            for tag_name in hashtag_list:
                if tag_name.startswith('#'):
                    tag_name = tag_name[1:]  # Remove the # symbol
                    hashtag, created = Hashtag.objects.get_or_create(name=tag_name)
                    if created:
                        hashtag.total_count = 1
                    else:
                        hashtag.total_count += 1
                    hashtag.save()
                    self.hashtags.add(hashtag)

    def process_tagged_users(self, tagged_users_text):
        # Remove existing tagged users
        self.tagged_users.clear()
        
        # Process new tagged users
        if tagged_users_text:
            tagged_list = tagged_users_text.split()
            for username in tagged_list:
                if username.startswith('@'):
                    username = username[1:]  # Remove the @ symbol
                    try:
                        user = User.objects.get(username=username)
                        self.tagged_users.add(user)
                    except User.DoesNotExist:
                        pass  # Skip if user doesn't exist

class NewsImage(models.Model):
    news = models.ForeignKey(News, on_delete=models.CASCADE, related_name='images', null=True, blank=True)
    image = models.ImageField(upload_to='news_images/')
    caption = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image {self.id} - {self.caption}"

class Comment(models.Model):
    news = models.ForeignKey(News, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.username} on {self.news.title}"

class Share(models.Model):
    news = models.ForeignKey(News, on_delete=models.CASCADE, related_name='shares')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    shared_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('news', 'user')

    def __str__(self):
        return f"{self.user.username} shared {self.news.title}"

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('share', 'Share'),
        ('follow', 'Follow'),
    )

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=10, choices=NOTIFICATION_TYPES)
    actor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='actions')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.actor.username} {self.notification_type}d your content"


class UserInterest(models.Model):
    """
    Tracks user interests for personalized feed recommendations
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='interests')
    
    # Search history - list of search queries
    search_keywords = models.JSONField(default=list, blank=True)
    
    # Sources the user has clicked on
    clicked_sources = models.JSONField(default=list, blank=True)
    
    # Category preferences with weights (0.0 to 1.0)
    category_weights = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s interests"

    class Meta:
        verbose_name = 'User Interest'
        verbose_name_plural = 'User Interests'


class ExternalNews(models.Model):
    """Stores a reference to an external API-fetched article once a user interacts with it."""
    url = models.URLField(unique=True, max_length=2000)
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True, default='')
    image = models.URLField(max_length=2000, blank=True, default='')
    source = models.CharField(max_length=200, blank=True, default='')
    published_at = models.CharField(max_length=50, blank=True, default='')

    # Social
    likes = models.ManyToManyField(User, related_name='liked_external', blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title[:80]

    class Meta:
        verbose_name = 'External News'
        verbose_name_plural = 'External News'


class ExternalShare(models.Model):
    """Tracks reshares of external news articles."""
    news = models.ForeignKey(ExternalNews, on_delete=models.CASCADE, related_name='shares')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    shared_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('news', 'user')

    def __str__(self):
        return f"{self.user.username} reshared external: {self.news.title[:40]}"


class ExternalComment(models.Model):
    """Comments on external news articles."""
    news = models.ForeignKey(ExternalNews, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.author.username}: {self.content[:50]}"


class TrustVote(models.Model):
    """Stores user trust verification or disputes for a news post."""
    VOTE_CHOICES = (
        ('verify', 'Verify'),
        ('dispute', 'Dispute'),
    )
    REASON_CHOICES = (
        ('misleading_title', 'Misleading Title'),
        ('altered_image', 'Altered Image'),
        ('outdated_news', 'Outdated News'),
        ('missing_context', 'Missing Context'),
        ('none', 'None'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    news = models.ForeignKey(News, on_delete=models.CASCADE, related_name='trust_votes')
    vote_type = models.CharField(max_length=10, choices=VOTE_CHOICES)
    dispute_reason = models.CharField(max_length=20, choices=REASON_CHOICES, default='none')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'news')

    def __str__(self):
        return f"{self.user.username} voted {self.vote_type} on {self.news.id}"
