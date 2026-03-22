from rest_framework import generics, permissions, status, views
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from .models import News, Comment, Hashtag, NewsImage
from .serializers import NewsSerializer, CommentSerializer, HashtagSerializer, NewsCreateUpdateSerializer
from .trending_engine import get_trending_data

class DashboardFeedAPIView(generics.ListAPIView):
    """Returns chronologically ordered posts from people the user follows"""
    serializer_class = NewsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        following = self.request.user.profile.following.all()
        return News.objects.filter(author__profile__in=following).order_by('-created_at')

class ExploreFeedAPIView(generics.ListAPIView):
    """Returns global/india posts for the explore tab"""
    serializer_class = NewsSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = News.objects.all().order_by('-created_at')
        geo = self.request.query_params.get('geo')
        author = self.request.query_params.get('author')
        
        if author:
            queryset = queryset.filter(author__username=author)
        elif geo:
            queryset = queryset.filter(geo_category=geo)
            
        return queryset

class TrendingDataAPIView(views.APIView):
    """Returns the velocity-scored trending feed data natively for React."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        trending_data = get_trending_data()
        
        def serialize_post_list(post_list):
            return [
                {
                    'velocity': item['velocity'],
                    'news': NewsSerializer(item['news'], context={'request': request}).data
                } for item in post_list
            ]
            
        def serialize_tag_list(tag_list):
            return [
                {
                    'score': item['score'],
                    'post_count': item['post_count'],
                    'hashtag': HashtagSerializer(item['hashtag']).data
                } for item in tag_list
            ]

        data = {
            'india': {
                'posts': serialize_post_list(trending_data['india_posts']),
                'tags': serialize_tag_list(trending_data['india_tags']),
            },
            'global': {
                'posts': serialize_post_list(trending_data['global_posts']),
                'tags': serialize_tag_list(trending_data['global_tags']),
            }
        }
        return Response(data)

class NewsCreateAPIView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = NewsCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            news = serializer.save(author=request.user)
            
            # Process hashtags and tagged users text fields natively
            hashtags_text = request.data.get('hashtags_text', '')
            news.process_hashtags(hashtags_text)
            
            tagged_users_text = request.data.get('tagged_users_text', '')
            news.process_tagged_users(tagged_users_text)

            # Handle multiple images
            images = request.FILES.getlist('images')
            for img in images:
                NewsImage.objects.create(news=news, image=img)
                
            return Response(NewsSerializer(news, context={'request': request}).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class NewsDetailAPIView(generics.RetrieveDestroyAPIView):
    queryset = News.objects.all()
    serializer_class = NewsSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def delete(self, request, *args, **kwargs):
        news = self.get_object()
        if news.author != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return super().delete(request, *args, **kwargs)

class LikeToggleAPIView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        news = get_object_or_404(News, pk=pk)
        if request.user in news.likes.all():
            news.likes.remove(request.user)
            action = 'unliked'
        else:
            news.likes.add(request.user)
            action = 'liked'
        return Response({'status': 'success', 'action': action, 'likes_count': news.likes.count()})

class CommentsAPIView(views.APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, pk):
        news = get_object_or_404(News, pk=pk)
        comments = news.comments.all()
        return Response(CommentSerializer(comments, many=True, context={'request': request}).data)
        
    def post(self, request, pk):
        news = get_object_or_404(News, pk=pk)
        content = request.data.get('content')
        if not content:
            return Response({'error': 'Content required'}, status=status.HTTP_400_BAD_REQUEST)
            
        comment = Comment.objects.create(news=news, author=request.user, content=content)
        return Response(CommentSerializer(comment, context={'request': request}).data, status=status.HTTP_201_CREATED)
