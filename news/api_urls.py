from django.urls import path
from . import api_views

app_name = 'news_api'

urlpatterns = [
    path('feed/', api_views.DashboardFeedAPIView.as_view(), name='dashboard_feed'),
    path('explore/', api_views.ExploreFeedAPIView.as_view(), name='explore_feed'),
    path('trending/', api_views.TrendingDataAPIView.as_view(), name='trending_data'),
    
    path('posts/', api_views.NewsCreateAPIView.as_view(), name='post_create'),
    path('posts/<int:pk>/', api_views.NewsDetailAPIView.as_view(), name='post_detail'),
    path('posts/<int:pk>/like/', api_views.LikeToggleAPIView.as_view(), name='like_toggle'),
    path('posts/<int:pk>/comments/', api_views.CommentsAPIView.as_view(), name='post_comments'),
]
