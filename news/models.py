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

