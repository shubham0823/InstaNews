from django.urls import path
from . import views

app_name = 'news'

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('explore/', views.explore_page, name='explore'),
    path('for-you/', views.for_you_feed, name='for_you_feed'),
    path('create/', views.create_news, name='create_news'),
    path('news/<int:pk>/', views.news_detail, name='news_detail'),
    path('news/<int:pk>/like/', views.like_news, name='like_news'),
    path('news/<int:pk>/comment/', views.add_comment, name='add_comment'),
    path('news/<int:pk>/share/', views.share_news, name='share_news'),
    path('news/<int:pk>/edit/', views.edit_news, name='edit_news'),
    path('news/<int:pk>/delete/', views.delete_news, name='delete_news'),
    path('search/', views.search_news, name='search_news'),
    path('notifications/', views.notifications_list, name='notifications'),
    path('notifications/<int:pk>/mark-read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('user/<str:username>/', views.user_profile, name='user_profile'),
    path('user/<str:username>/follow/', views.follow_user, name='follow_user'),
    path('user/<str:username>/followers/', views.followers_list, name='followers_list'),
    path('user/<str:username>/following/', views.following_list, name='following_list'),
    path('api/world-news/', views.world_news_api, name='world_news_api'),
    path('api/indian-news/', views.indian_news_api, name='indian_news_api'),
    path('hashtag/<str:tag_name>/', views.hashtag_view, name='hashtag'),
    path('settings/', views.profile_settings, name='profile_settings'),
    path('market/', views.market_list, name='market_list'),
    path('api/market-data/', views.market_data_api, name='market_data_api'),
    path('api/user-search/', views.user_search_api, name='user_search_api'),
    
    # India News Hub
    path('news/india/', views.india_news_hub, name='india_news_hub'),
    path('news/india/<str:state_code>/', views.india_state_news, name='india_state_news'),
    
    # World News Hub
    path('news/world/', views.world_news_hub, name='world_news_hub'),
    path('news/world/<str:country_code>/', views.world_country_news, name='world_country_news'),
    
    # News API Endpoints
    path('api/fetch-news/', views.api_fetch_news, name='api_fetch_news'),
    path('api/trending-news/', views.api_trending_news, name='api_trending_news'),
    path('api/for-you/', views.api_for_you_feed, name='api_for_you_feed'),
    path('api/track-interaction/', views.api_track_interaction, name='api_track_interaction'),
] 