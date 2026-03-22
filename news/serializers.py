from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile, Hashtag, News, NewsImage, Comment, Share, Notification

class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    bio = serializers.CharField(source='profile.bio', read_only=True)
    country = serializers.CharField(source='profile.country', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'avatar', 'bio', 'country']

    def get_avatar(self, obj):
        try:
            request = self.context.get('request')
            if obj.profile.avatar:
                avatar_url = obj.profile.avatar.url
                return request.build_absolute_uri(avatar_url) if request else avatar_url
        except Exception:
            pass
        return None


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    followers_count = serializers.IntegerField(source='followers.count', read_only=True)
    following_count = serializers.IntegerField(source='following.count', read_only=True)

    class Meta:
        model = Profile
        fields = ['id', 'user', 'bio', 'avatar', 'country', 'timezone', 'followers_count', 'following_count']


class HashtagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hashtag
        fields = ['id', 'name', 'total_count', 'geo_affinity']


class NewsImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsImage
        fields = ['id', 'image', 'caption', 'uploaded_at']


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    reply_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = ['id', 'author', 'content', 'created_at', 'parent', 'reply_count']

    def get_reply_count(self, obj):
        return obj.replies.count()


class NewsSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    images = NewsImageSerializer(many=True, read_only=True)
    hashtags = HashtagSerializer(many=True, read_only=True)
    tagged_users = UserSerializer(many=True, read_only=True)
    likes_count = serializers.IntegerField(source='likes.count', read_only=True)
    comments_count = serializers.IntegerField(source='comments.count', read_only=True)
    shares_count = serializers.IntegerField(source='shares.count', read_only=True)
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = News
        fields = [
            'id', 'author', 'title', 'content', 'created_at', 'updated_at',
            'news_type', 'views', 'geo_category', 'video', 'images',
            'hashtags', 'tagged_users', 'likes_count', 'comments_count', 
            'shares_count', 'is_liked'
        ]

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(id=request.user.id).exists()
        return False


class NewsCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer optimized for creating/updating a News post"""
    class Meta:
        model = News
        fields = ['title', 'content', 'news_type', 'geo_category', 'video']
