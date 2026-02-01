from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.conf import settings
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from .models import News, Comment, Profile, NewsImage, Notification, Share, Hashtag
import requests
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count
from .forms import NewsForm
from django.db import models
from django.utils import timezone
import os
import uuid

def get_market_data():
    import requests
    
    # Finnhub API configuration
    API_KEY = 'cu4gcr1r01qna2rnb3t0cu4gcr1r01qna2rnb3tg'
    BASE_URL = 'https://finnhub.io/api/v1'
    
    # List of stock symbols to track
    STOCK_SYMBOLS = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'META']
    # List of crypto symbols to track
    CRYPTO_SYMBOLS = ['BINANCE:BTCUSDT', 'BINANCE:ETHUSDT', 'BINANCE:BNBUSDT']
    
    stocks_data = []
    crypto_data = []
    
    try:
        # Fetch stock data
        for symbol in STOCK_SYMBOLS:
            quote = requests.get(f'{BASE_URL}/quote', 
                               params={'symbol': symbol, 'token': API_KEY})
            profile = requests.get(f'{BASE_URL}/stock/profile2', 
                                 params={'symbol': symbol, 'token': API_KEY})
            
            if quote.status_code == 200 and profile.status_code == 200:
                quote_data = quote.json()
                profile_data = profile.json()
                
                stocks_data.append({
                    'symbol': symbol,
                    'name': profile_data.get('name', symbol),
                    'price': quote_data.get('c', 0),  # Current price
                    'change_percent': quote_data.get('dp', 0),  # Percent change
                    'market_cap': profile_data.get('marketCapitalization', 0) * 1000000  # Convert to actual value
                })
        
        # Fetch crypto data
        for symbol in CRYPTO_SYMBOLS:
            quote = requests.get(f'{BASE_URL}/quote', 
                               params={'symbol': symbol, 'token': API_KEY})
            
            if quote.status_code == 200:
                quote_data = quote.json()
                clean_symbol = symbol.split(':')[1][:3]  # Extract first 3 chars after BINANCE:
                
                crypto_data.append({
                    'symbol': clean_symbol,
                    'name': f'{clean_symbol}/USDT',
                    'price': quote_data.get('c', 0),
                    'change_percent': quote_data.get('dp', 0),
                    'market_cap': 0  # Finnhub doesn't provide market cap for crypto
                })
    
    except Exception as e:
        print(f"Error fetching market data: {e}")
    
    return {
        'stocks': stocks_data,
        'crypto': crypto_data
    }

def landing_page(request):
    # Get the 3 most recent news posts for trending section
    trending_news = News.objects.select_related('author', 'author__profile').prefetch_related(
        'images', 'likes', 'comments', 'shares', 'hashtags'
    ).order_by('-created_at')[:3]
    
    # Get all news for the main feed
    news_feed = News.objects.select_related('author', 'author__profile').prefetch_related(
        'images', 'likes', 'comments', 'shares', 'hashtags'
    ).order_by('-created_at')[3:]  # Skip the first 3 as they're in trending
    
    # Get trending hashtags for world news
    global_trending_tags = (
        Hashtag.objects
        .filter(news_posts__content__iregex=r'\b(world|global|international)\b')
        .order_by('-total_count')[:5]
    )
    
    # Get trending hashtags for Indian news
    india_trending_tags = (
        Hashtag.objects
        .filter(news_posts__content__iregex=r'\b(india|indian)\b')
        .order_by('-total_count')[:5]
    )
    
    # Fetch market data
    market_data = get_market_data()
    
    # Fetch world news from API
    api_key = settings.WORLD_NEWS_API_KEY
    world_news = []
    indian_news = []

    try:
        # Fetch world news
        world_response = requests.get(
            f'https://api.worldnewsapi.com/search-news',
            params={
                'api-key': api_key,
                'text': 'world',
                'number': 5
            }
        )
        if world_response.status_code == 200:
            world_news = world_response.json().get('news', [])

        # Fetch Indian news
        indian_response = requests.get(
            f'https://api.worldnewsapi.com/search-news',
            params={
                'api-key': api_key,
                'text': 'India',
                'number': 5
            }
        )
        if indian_response.status_code == 200:
            indian_news = indian_response.json().get('news', [])
    except Exception as e:
        print(f"Error fetching news: {str(e)}")

    context = {
        'market_data': market_data,
        'world_news': world_news,
        'indian_news': indian_news,
        'trending_news': trending_news,
        'news_feed': news_feed,
        'global_trending_tags': global_trending_tags,
        'india_trending_tags': india_trending_tags,
        'debug': settings.DEBUG,
    }

    return render(request, 'news/landing_page.html', context)

@login_required
def explore_page(request):
    # Get the filter type from query parameters
    active_filter = request.GET.get('filter', 'trending')
    
    # Base queryset with all necessary related data
    news_queryset = News.objects.select_related('author', 'author__profile')\
        .prefetch_related('likes', 'comments', 'shares', 'images')\
        .annotate(engagement_score=Count('likes') + Count('comments') + Count('shares'))
    
    external_news = []  # For API-fetched personalized news
    is_personalized = False
    
    if active_filter == 'trending':
        # Get trending news based on engagement score in the last 7 days
        seven_days_ago = timezone.now() - timezone.timedelta(days=7)
        news_items = news_queryset.filter(created_at__gte=seven_days_ago)\
            .order_by('-engagement_score', '-created_at')
    elif active_filter == 'for_you':
        # Use the recommendation engine for personalized feed
        from .recommendation_engine import generate_personalized_feed
        
        page = int(request.GET.get('page', 1))
        feed_data = generate_personalized_feed(request.user, page=page, page_size=12)
        
        external_news = feed_data.get('articles', [])
        is_personalized = not feed_data.get('is_cold_start', True)
        
        # Also get some local news from followed users and liked authors
        followed_users = request.user.profile.following.values_list('user', flat=True)
        liked_news = request.user.liked_news.values_list('author', flat=True)
        interested_hashtags = Hashtag.objects.filter(
            news_posts__in=request.user.liked_news.all()
        ).values_list('name', flat=True)
        
        news_items = news_queryset.filter(
            Q(author__in=followed_users) |  # Posts from followed users
            Q(author__in=liked_news) |      # Posts from authors whose content user has liked
            Q(hashtags__name__in=interested_hashtags)  # Posts with hashtags user has interacted with
        ).distinct().order_by('-created_at')[:6]  # Limit to 6 local items
    else:  # followers
        # Get news only from followed users
        followed_users = request.user.profile.following.values_list('user', flat=True)
        news_items = news_queryset.filter(author__in=followed_users).order_by('-created_at')
    
    # Pagination (only for non-for_you filters since for_you uses API pagination)
    if active_filter != 'for_you':
        paginator = Paginator(news_items, 12)  # Show 12 news items per page
        page = request.GET.get('page')
        try:
            news_items = paginator.page(page)
        except PageNotAnInteger:
            news_items = paginator.page(1)
        except EmptyPage:
            news_items = paginator.page(paginator.num_pages)
    
    context = {
        'news_items': news_items,
        'active_filter': active_filter,
        'external_news': external_news,
        'is_personalized': is_personalized,
    }
    return render(request, 'news/explore.html', context)

@login_required
def create_news(request):
    if request.method == 'POST':
        try:
            form = NewsForm(request.POST, request.FILES)
            if form.is_valid():
                news = form.save(commit=False)
                news.author = request.user
                
                # Get the media type for short format
                media_type = form.cleaned_data.get('media_type')
                
                # Ensure media directories exist
                video_path = os.path.join(settings.MEDIA_ROOT, 'news_videos')
                image_path = os.path.join(settings.MEDIA_ROOT, 'news_images')
                os.makedirs(video_path, exist_ok=True)
                os.makedirs(image_path, exist_ok=True)
                
                # Save the news object first
                news.save()
                
                if news.news_type == 'short':
                    if media_type == 'video' and request.FILES.get('video'):
                        video_file = request.FILES['video']
                        file_ext = os.path.splitext(video_file.name)[1]
                        unique_filename = f"{uuid.uuid4()}{file_ext}"
                        news.video.save(unique_filename, video_file, save=True)
                    elif media_type == 'image' and request.FILES.getlist('images'):
                        image = request.FILES.getlist('images')[0]
                        NewsImage.objects.create(
                            news=news,
                            image=image,
                            caption=f"Image for {news.title}"
                        )
                else:  # Long format
                    if request.FILES.get('video'):
                        video_file = request.FILES['video']
                        file_ext = os.path.splitext(video_file.name)[1]
                        unique_filename = f"{uuid.uuid4()}{file_ext}"
                        news.video.save(unique_filename, video_file, save=True)
                    
                    for image in request.FILES.getlist('images'):
                        NewsImage.objects.create(
                            news=news,
                            image=image,
                            caption=f"Image for {news.title}"
                        )
                
                # Process hashtags and tagged users
                hashtags = form.cleaned_data.get('hashtags', '')
                news.process_hashtags(hashtags)
                tagged_users = form.cleaned_data.get('tagged_users', '')
                news.process_tagged_users(tagged_users)
                
                messages.success(request, 'News article created successfully!')
                return redirect('news:news_detail', pk=news.pk)
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
        except Exception as e:
            messages.error(request, f'Error creating news article: {str(e)}')
            if 'news' in locals():
                news.delete()  # Clean up if there was an error
    else:
        form = NewsForm()
    
    return render(request, 'news/create_news.html', {'form': form})

def news_detail(request, pk):
    news = get_object_or_404(News, pk=pk)
    # Increment view count
    news.views += 1
    news.save()
    
    comments = news.comments.filter(parent=None)  # Get only top-level comments
    
    # Debug information
    images = news.images.all()
    print(f"Number of images for news {pk}: {images.count()}")  # Debug log
    for img in images:
        print(f"Image {img.id}: URL={img.image.url}, Path={img.image.path}")  # Debug log
    
    context = {
        'news': news,
        'comments': comments,
        'debug': settings.DEBUG,
    }
    return render(request, 'news/news_detail.html', context)

@login_required
def like_news(request, pk):
    news = get_object_or_404(News, pk=pk)
    if request.user in news.likes.all():
        news.likes.remove(request.user)
        liked = False
    else:
        news.likes.add(request.user)
        liked = True
        # Create notification
        if request.user != news.author:
            Notification.objects.create(
                recipient=news.author,
                notification_type='like',
                actor=request.user,
                content_type=ContentType.objects.get_for_model(news),
                object_id=news.id
            )
    
    return JsonResponse({
        'liked': liked,
        'likes_count': news.likes.count()
    })

@login_required
def add_comment(request, pk):
    if request.method == 'POST':
        news = get_object_or_404(News, pk=pk)
        content = request.POST.get('content')
        parent_id = request.POST.get('parent_id')
        
        if parent_id:
            parent_comment = get_object_or_404(Comment, id=parent_id)
            comment = Comment.objects.create(
                news=news,
                author=request.user,
                content=content,
                parent=parent_comment
            )
            # Create notification for reply
            if request.user != parent_comment.author:
                Notification.objects.create(
                    recipient=parent_comment.author,
                    notification_type='comment',
                    actor=request.user,
                    content_type=ContentType.objects.get_for_model(comment),
                    object_id=comment.id
                )
        else:
            comment = Comment.objects.create(
                news=news,
                author=request.user,
                content=content
            )
            # Create notification for comment
            if request.user != news.author:
                Notification.objects.create(
                    recipient=news.author,
                    notification_type='comment',
                    actor=request.user,
                    content_type=ContentType.objects.get_for_model(comment),
                    object_id=comment.id
                )
        
        return JsonResponse({
            'status': 'success',
            'comment_id': comment.id,
            'author': comment.author.username,
            'content': comment.content,
            'created_at': comment.created_at.strftime('%B %d, %Y %H:%M')
        })
    
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def share_news(request, pk):
    news = get_object_or_404(News, pk=pk)
    share = news.shares.create(user=request.user)
    
    # Create notification
    if request.user != news.author:
        Notification.objects.create(
            recipient=news.author,
            notification_type='share',
            actor=request.user,
            content_type=ContentType.objects.get_for_model(share),
            object_id=share.id
        )
    
    return JsonResponse({
        'status': 'success',
        'shares_count': news.shares.count()
    })

@login_required
def notifications_list(request):
    notifications = request.user.notifications.all()
    return render(request, 'news/notifications.html', {'notifications': notifications})

@login_required
def mark_notification_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'status': 'success'})

@login_required
def mark_all_notifications_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return JsonResponse({'status': 'success'})

def search_news(request):
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'all')  # all, news, users, hashtags
    
    # Initialize empty querysets
    news_list = News.objects.none()
    users_list = User.objects.none()
    hashtags_list = Hashtag.objects.none()
    
    original_query = query  # Keep original for display
    
    if query:
        # Check if query starts with @ for user search
        if query.startswith('@'):
            search_type = 'users'
            query = query[1:]  # Remove @ symbol
        # Check if query starts with # for hashtag search
        elif query.startswith('#'):
            search_type = 'hashtags'
            query = query[1:]  # Remove # symbol
        
        # Only search if we have a query after removing prefix
        if query:
            # Search based on type
            if search_type == 'all' or search_type == 'news':
                news_list = News.objects.select_related('author', 'author__profile').prefetch_related(
                    'images', 'likes', 'comments', 'hashtags'
                ).filter(
                    Q(title__icontains=query) |
                    Q(content__icontains=query) |
                    Q(hashtags__name__icontains=query)
                ).distinct().order_by('-created_at')
            
            if search_type == 'all' or search_type == 'users':
                users_list = User.objects.select_related('profile').filter(
                    Q(username__icontains=query) |
                    Q(first_name__icontains=query) |
                    Q(last_name__icontains=query)
                ).order_by('username')
            
            if search_type == 'all' or search_type == 'hashtags':
                hashtags_list = Hashtag.objects.filter(
                    name__icontains=query
                ).annotate(
                    news_count=Count('news_posts')
                ).order_by('-news_count')
    
    # Get counts before pagination
    news_count = news_list.count()
    users_count = users_list.count()
    hashtags_count = hashtags_list.count()
    
    # Pagination for news
    news_paginator = Paginator(news_list, 12)
    page = request.GET.get('page')
    news_articles = news_paginator.get_page(page)
    
    # Pagination for users
    users_paginator = Paginator(users_list, 20)
    users_page = users_paginator.get_page(page)
    
    # Pagination for hashtags
    hashtags_paginator = Paginator(hashtags_list, 20)
    hashtags_page = hashtags_paginator.get_page(page)
    
    context = {
        'news_articles': news_articles,
        'users': users_page,
        'hashtags': hashtags_page,
        'query': query if query else original_query,
        'search_type': search_type,
        'news_count': news_count,
        'users_count': users_count,
        'hashtags_count': hashtags_count,
    }
    
    return render(request, 'news/search_results.html', context)

@login_required
def follow_user(request, username):
    user_to_follow = get_object_or_404(User, username=username)
    
    if request.user == user_to_follow:
        messages.error(request, "You cannot follow yourself.")
        return JsonResponse({'status': 'error', 'message': 'You cannot follow yourself'})
    
    if request.method == 'POST':
        if request.user.profile.following.filter(user=user_to_follow).exists():
            # Unfollow
            request.user.profile.following.remove(user_to_follow.profile)
            is_following = False
            action = 'unfollowed'
        else:
            # Follow
            request.user.profile.following.add(user_to_follow.profile)
            is_following = True
            action = 'followed'
            
            # Create notification for the followed user
            Notification.objects.create(
                recipient=user_to_follow,
                notification_type='follow',
                actor=request.user,
                content_type=ContentType.objects.get_for_model(Profile),
                object_id=user_to_follow.profile.id
            )
        
        return JsonResponse({
            'status': 'success',
            'is_following': is_following,
            'follower_count': user_to_follow.profile.followers.count(),
            'message': f'Successfully {action} {user_to_follow.username}'
        })
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
def user_profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    user_profile = profile_user.profile
    news_list = News.objects.filter(author=profile_user).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(news_list, 10)
    page = request.GET.get('page')
    news_items = paginator.get_page(page)
    
    is_following = request.user.is_authenticated and request.user.profile.following.filter(user=profile_user).exists()
    
    context = {
        'profile_user': profile_user,
        'user_profile': user_profile,
        'news_items': news_items,
        'is_following': is_following,
        'followers_count': user_profile.followers.count(),
        'following_count': user_profile.following.count()
    }
    return render(request, 'news/user_profile.html', context)

@login_required
def followers_list(request, username):
    user = get_object_or_404(User, username=username)
    followers = user.profile.followers.all()
    return render(request, 'news/followers.html', {'user': user, 'followers': followers})

@login_required
def following_list(request, username):
    user = get_object_or_404(User, username=username)
    following = user.profile.following.all()
    return render(request, 'news/following.html', {'user': user, 'following': following})

@login_required
def edit_news(request, pk):
    news = get_object_or_404(News, pk=pk)
    
    # Check if user is the author
    if news.author != request.user:
        messages.error(request, "You don't have permission to edit this news article.")
        return redirect('news:news_detail', pk=pk)
    
    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES, instance=news)
        if form.is_valid():
            news = form.save(commit=False)
            
            # Handle media based on news type and media type
            media_type = form.cleaned_data.get('media_type')
            
            if news.news_type == 'short':
                if media_type == 'video' and request.FILES.get('video'):
                    news.video = request.FILES['video']
                elif media_type == 'image':
                    # Handle single image upload for short format
                    uploaded_images = request.FILES.getlist('images')
                    if uploaded_images:
                        # Delete existing images
                        news.images.all().delete()
                        NewsImage.objects.create(
                            news=news,
                            image=uploaded_images[0],
                            caption=f"Image for {news.title}"
                        )
                elif media_type == 'none':
                    # Remove all media
                    news.video = None
                    news.images.all().delete()
            else:  # Long format
                if request.FILES.get('video'):
                    news.video = request.FILES['video']
                
                # Handle multiple images
                uploaded_images = request.FILES.getlist('images')
                if uploaded_images:
                    news.images.all().delete()  # Remove existing images
                    for image in uploaded_images:
                        NewsImage.objects.create(
                            news=news,
                            image=image,
                            caption=f"Image for {news.title}"
                        )
            
            news.save()
            messages.success(request, 'News article updated successfully!')
            return redirect('news:news_detail', pk=news.pk)
    else:
        form = NewsForm(instance=news)
        # Set initial media type
        if news.news_type == 'short':
            if news.video:
                form.initial['media_type'] = 'video'
            elif news.images.exists():
                form.initial['media_type'] = 'image'
            else:
                form.initial['media_type'] = 'none'
    
    return render(request, 'news/edit_news.html', {'form': form, 'news': news})

@login_required
def delete_news(request, pk):
    news = get_object_or_404(News, pk=pk)
    
    # Check if user is the author
    if news.author != request.user:
        messages.error(request, "You don't have permission to delete this news article.")
        return redirect('news:news_detail', pk=pk)
    
    if request.method == 'POST':
        # Delete associated images and video
        news.images.all().delete()
        if news.video:
            news.video.delete()
        
        # Delete the news article
        news.delete()
        messages.success(request, 'News article deleted successfully!')
        return redirect('news:landing_page')
    
    return render(request, 'news/delete_news.html', {'news': news})

def world_news_api(request):
    page = int(request.GET.get('page', 1))
    api_key = settings.WORLD_NEWS_API_KEY
    
    try:
        response = requests.get(
            f'https://api.worldnewsapi.com/search-news',
            params={
                'api-key': api_key,
                'text': 'world',
                'number': 5,
                'offset': (page - 1) * 5
            }
        )
        if response.status_code == 200:
            data = response.json()
            return JsonResponse({
                'news': data.get('news', []),
                'has_more': len(data.get('news', [])) == 5
            })
    except Exception as e:
        print(f"Error fetching world news: {str(e)}")
    
    return JsonResponse({'news': [], 'has_more': False})

def indian_news_api(request):
    page = int(request.GET.get('page', 1))
    api_key = settings.WORLD_NEWS_API_KEY
    
    try:
        response = requests.get(
            f'https://api.worldnewsapi.com/search-news',
            params={
                'api-key': api_key,
                'text': 'India',
                'number': 5,
                'offset': (page - 1) * 5
            }
        )
        if response.status_code == 200:
            data = response.json()
            return JsonResponse({
                'news': data.get('news', []),
                'has_more': len(data.get('news', [])) == 5
            })
    except Exception as e:
        print(f"Error fetching Indian news: {str(e)}")
    
    return JsonResponse({'news': [], 'has_more': False})

def hashtag_view(request, tag_name):
    hashtag = get_object_or_404(Hashtag, name=tag_name)
    news_list = News.objects.filter(hashtags=hashtag).order_by('-created_at')
    
    paginator = Paginator(news_list, 12)  # Show 12 news articles per page
    page = request.GET.get('page')
    news_articles = paginator.get_page(page)
    
    context = {
        'hashtag': hashtag,
        'news_articles': news_articles,
    }
    
    return render(request, 'news/hashtag.html', context)

@login_required
def profile_settings(request):
    if request.method == 'POST' and request.FILES.get('avatar'):
        profile = request.user.profile
        profile.avatar = request.FILES['avatar']
        profile.save()
        messages.success(request, 'Profile photo updated successfully!')
        return redirect('news:profile_settings')
    
    return render(request, 'news/profile_settings.html')

def market_list(request):
    """View for the market list page"""
    return render(request, 'news/market_list.html')

def market_data_api(request):
    """API endpoint for market data"""
    market_data = get_market_data()
    return JsonResponse(market_data)

def user_search_api(request):
    """API endpoint for searching users for tagging"""
    query = request.GET.get('q', '')
    if query:
        users = User.objects.filter(username__icontains=query)[:5]
        return JsonResponse({
            'users': [{
                'username': user.username,
                'avatar': user.profile.avatar.url
            } for user in users]
        })
    return JsonResponse({'users': []})


# India States and UTs Data
INDIA_STATES = [
    {"name": "Andhra Pradesh", "code": "ap", "capital": "Amaravati", "region": "South"},
    {"name": "Arunachal Pradesh", "code": "ar", "capital": "Itanagar", "region": "Northeast"},
    {"name": "Assam", "code": "as", "capital": "Dispur", "region": "Northeast"},
    {"name": "Bihar", "code": "br", "capital": "Patna", "region": "East"},
    {"name": "Chhattisgarh", "code": "cg", "capital": "Raipur", "region": "Central"},
    {"name": "Goa", "code": "ga", "capital": "Panaji", "region": "West"},
    {"name": "Gujarat", "code": "gj", "capital": "Gandhinagar", "region": "West"},
    {"name": "Haryana", "code": "hr", "capital": "Chandigarh", "region": "North"},
    {"name": "Himachal Pradesh", "code": "hp", "capital": "Shimla", "region": "North"},
    {"name": "Jharkhand", "code": "jh", "capital": "Ranchi", "region": "East"},
    {"name": "Karnataka", "code": "ka", "capital": "Bengaluru", "region": "South"},
    {"name": "Kerala", "code": "kl", "capital": "Thiruvananthapuram", "region": "South"},
    {"name": "Madhya Pradesh", "code": "mp", "capital": "Bhopal", "region": "Central"},
    {"name": "Maharashtra", "code": "mh", "capital": "Mumbai", "region": "West"},
    {"name": "Manipur", "code": "mn", "capital": "Imphal", "region": "Northeast"},
    {"name": "Meghalaya", "code": "ml", "capital": "Shillong", "region": "Northeast"},
    {"name": "Mizoram", "code": "mz", "capital": "Aizawl", "region": "Northeast"},
    {"name": "Nagaland", "code": "nl", "capital": "Kohima", "region": "Northeast"},
    {"name": "Odisha", "code": "or", "capital": "Bhubaneswar", "region": "East"},
    {"name": "Punjab", "code": "pb", "capital": "Chandigarh", "region": "North"},
    {"name": "Rajasthan", "code": "rj", "capital": "Jaipur", "region": "West"},
    {"name": "Sikkim", "code": "sk", "capital": "Gangtok", "region": "Northeast"},
    {"name": "Tamil Nadu", "code": "tn", "capital": "Chennai", "region": "South"},
    {"name": "Telangana", "code": "tg", "capital": "Hyderabad", "region": "South"},
    {"name": "Tripura", "code": "tr", "capital": "Agartala", "region": "Northeast"},
    {"name": "Uttar Pradesh", "code": "up", "capital": "Lucknow", "region": "North"},
    {"name": "Uttarakhand", "code": "uk", "capital": "Dehradun", "region": "North"},
    {"name": "West Bengal", "code": "wb", "capital": "Kolkata", "region": "East"},
]

INDIA_UTS = [
    {"name": "Andaman and Nicobar", "code": "an", "type": "UT"},
    {"name": "Chandigarh", "code": "ch", "type": "UT"},
    {"name": "Dadra Nagar Haveli and Daman Diu", "code": "dd", "type": "UT"},
    {"name": "Delhi", "code": "dl", "type": "NCT"},
    {"name": "Jammu and Kashmir", "code": "jk", "type": "UT"},
    {"name": "Ladakh", "code": "la", "type": "UT"},
    {"name": "Lakshadweep", "code": "ld", "type": "UT"},
    {"name": "Puducherry", "code": "py", "type": "UT"},
]

# World Countries Data
WORLD_COUNTRIES = [
    {"name": "United States", "code": "us", "flag": "🇺🇸", "continent": "North America"},
    {"name": "United Kingdom", "code": "uk", "flag": "🇬🇧", "continent": "Europe"},
    {"name": "Japan", "code": "jp", "flag": "🇯🇵", "continent": "Asia"},
    {"name": "Germany", "code": "de", "flag": "🇩🇪", "continent": "Europe"},
    {"name": "France", "code": "fr", "flag": "🇫🇷", "continent": "Europe"},
    {"name": "China", "code": "cn", "flag": "🇨🇳", "continent": "Asia"},
    {"name": "Russia", "code": "ru", "flag": "🇷🇺", "continent": "Europe"},
    {"name": "Australia", "code": "au", "flag": "🇦🇺", "continent": "Oceania"},
    {"name": "Canada", "code": "ca", "flag": "🇨🇦", "continent": "North America"},
    {"name": "Brazil", "code": "br", "flag": "🇧🇷", "continent": "South America"},
    {"name": "South Korea", "code": "kr", "flag": "🇰🇷", "continent": "Asia"},
    {"name": "Italy", "code": "it", "flag": "🇮🇹", "continent": "Europe"},
    {"name": "Spain", "code": "es", "flag": "🇪🇸", "continent": "Europe"},
    {"name": "Mexico", "code": "mx", "flag": "🇲🇽", "continent": "North America"},
    {"name": "Indonesia", "code": "id", "flag": "🇮🇩", "continent": "Asia"},
    {"name": "Netherlands", "code": "nl", "flag": "🇳🇱", "continent": "Europe"},
    {"name": "Saudi Arabia", "code": "sa", "flag": "🇸🇦", "continent": "Asia"},
    {"name": "Turkey", "code": "tr", "flag": "🇹🇷", "continent": "Europe"},
    {"name": "Switzerland", "code": "ch", "flag": "🇨🇭", "continent": "Europe"},
    {"name": "Poland", "code": "pl", "flag": "🇵🇱", "continent": "Europe"},
    {"name": "Sweden", "code": "se", "flag": "🇸🇪", "continent": "Europe"},
    {"name": "Belgium", "code": "be", "flag": "🇧🇪", "continent": "Europe"},
    {"name": "Argentina", "code": "ar", "flag": "🇦🇷", "continent": "South America"},
    {"name": "United Arab Emirates", "code": "ae", "flag": "🇦🇪", "continent": "Asia"},
    {"name": "Thailand", "code": "th", "flag": "🇹🇭", "continent": "Asia"},
    {"name": "Israel", "code": "il", "flag": "🇮🇱", "continent": "Asia"},
    {"name": "Singapore", "code": "sg", "flag": "🇸🇬", "continent": "Asia"},
    {"name": "South Africa", "code": "za", "flag": "🇿🇦", "continent": "Africa"},
    {"name": "Egypt", "code": "eg", "flag": "🇪🇬", "continent": "Africa"},
    {"name": "Nigeria", "code": "ng", "flag": "🇳🇬", "continent": "Africa"},
    {"name": "Pakistan", "code": "pk", "flag": "🇵🇰", "continent": "Asia"},
    {"name": "Bangladesh", "code": "bd", "flag": "🇧🇩", "continent": "Asia"},
    {"name": "Vietnam", "code": "vn", "flag": "🇻🇳", "continent": "Asia"},
    {"name": "Philippines", "code": "ph", "flag": "🇵🇭", "continent": "Asia"},
    {"name": "Malaysia", "code": "my", "flag": "🇲🇾", "continent": "Asia"},
    {"name": "New Zealand", "code": "nz", "flag": "🇳🇿", "continent": "Oceania"},
    {"name": "Ireland", "code": "ie", "flag": "🇮🇪", "continent": "Europe"},
    {"name": "Norway", "code": "no", "flag": "🇳🇴", "continent": "Europe"},
    {"name": "Denmark", "code": "dk", "flag": "🇩🇰", "continent": "Europe"},
    {"name": "Finland", "code": "fi", "flag": "🇫🇮", "continent": "Europe"},
]

TOP_COUNTRIES = WORLD_COUNTRIES[:10]


def india_news_hub(request):
    """India News Hub - Shows all states and UTs"""
    import random
    
    # Add random news count for demo (in production, query actual news count)
    states_data = []
    for state in INDIA_STATES:
        state_copy = state.copy()
        state_copy['news_count'] = random.randint(5, 50)
        states_data.append(state_copy)
    
    uts_data = []
    for ut in INDIA_UTS:
        ut_copy = ut.copy()
        ut_copy['news_count'] = random.randint(3, 25)
        uts_data.append(ut_copy)
    
    # Get search query for filtering
    search_query = request.GET.get('q', '').strip().lower()
    
    if search_query:
        states_data = [s for s in states_data if search_query in s['name'].lower()]
        uts_data = [u for u in uts_data if search_query in u['name'].lower()]
    
    context = {
        'states': states_data,
        'uts': uts_data,
        'search_query': search_query,
        'total_states': len(INDIA_STATES),
        'total_uts': len(INDIA_UTS),
    }
    
    return render(request, 'news/india_news.html', context)


def india_state_news(request, state_code):
    """News for a specific Indian state - fetches from API"""
    from .news_api import fetch_india_news
    
    # Find the state/UT
    state = None
    for s in INDIA_STATES + INDIA_UTS:
        if s['code'] == state_code:
            state = s
            break
    
    if not state:
        messages.error(request, 'State not found')
        return redirect('news:india_news_hub')
    
    # Fetch real news from API
    page = int(request.GET.get('page', 1))
    api_response = fetch_india_news(state['name'], page_size=12, page=page)
    
    # Get news from API
    external_news = api_response.get('articles', []) if api_response.get('success') else []
    
    # Also get local news from database
    local_news = News.objects.filter(
        Q(title__icontains=state['name']) |
        Q(content__icontains=state['name'])
    ).order_by('-created_at')[:6]
    
    context = {
        'state': state,
        'external_news': external_news,
        'local_news': local_news,
        'news_count': api_response.get('total_results', 0),
        'news_source': api_response.get('source', 'unknown'),
        'from_cache': api_response.get('from_cache', False),
        'api_success': api_response.get('success', False),
    }
    
    return render(request, 'news/state_news.html', context)


def world_news_hub(request):
    """World News Hub - Shows all countries"""
    import random
    
    # Add random news count for demo
    countries_data = []
    for country in WORLD_COUNTRIES:
        country_copy = country.copy()
        country_copy['news_count'] = random.randint(10, 100)
        countries_data.append(country_copy)
    
    top_countries = countries_data[:10]
    
    # Get search query for filtering
    search_query = request.GET.get('q', '').strip().lower()
    
    if search_query:
        countries_data = [c for c in countries_data if search_query in c['name'].lower()]
    
    # Group by continent
    continents = {}
    for country in countries_data:
        continent = country['continent']
        if continent not in continents:
            continents[continent] = []
        continents[continent].append(country)
    
    context = {
        'countries': countries_data,
        'top_countries': top_countries,
        'continents': continents,
        'search_query': search_query,
        'total_countries': len(WORLD_COUNTRIES),
    }
    
    return render(request, 'news/world_news.html', context)


def world_country_news(request, country_code):
    """News for a specific country - fetches from API"""
    from .news_api import fetch_world_news
    
    # Find the country
    country = None
    for c in WORLD_COUNTRIES:
        if c['code'] == country_code:
            country = c
            break
    
    if not country:
        messages.error(request, 'Country not found')
        return redirect('news:world_news_hub')
    
    # Fetch real news from API
    page = int(request.GET.get('page', 1))
    api_response = fetch_world_news(country['name'], page_size=12, page=page)
    
    # Get news from API
    external_news = api_response.get('articles', []) if api_response.get('success') else []
    
    # Also get local news from database
    local_news = News.objects.filter(
        Q(title__icontains=country['name']) |
        Q(content__icontains=country['name'])
    ).order_by('-created_at')[:6]
    
    context = {
        'country': country,
        'external_news': external_news,
        'local_news': local_news,
        'news_count': api_response.get('total_results', 0),
        'news_source': api_response.get('source', 'unknown'),
        'from_cache': api_response.get('from_cache', False),
        'api_success': api_response.get('success', False),
    }
    
    return render(request, 'news/country_news.html', context)


# API Endpoints for AJAX
def api_fetch_news(request):
    """AJAX endpoint to fetch news for a region"""
    from .news_api import fetch_news
    
    query = request.GET.get('q', '')
    region_type = request.GET.get('type', 'general')  # india, world, general
    page = int(request.GET.get('page', 1))
    
    if not query:
        return JsonResponse({'success': False, 'error': 'Query required'})
    
    # Add context based on region type
    if region_type == 'india':
        query = f"{query} India news"
    elif region_type == 'world':
        query = f"{query} news"
    
    result = fetch_news(query, page_size=12, page=page)
    
    return JsonResponse(result)


def api_trending_news(request):
    """AJAX endpoint to fetch trending news"""
    from .news_api import fetch_trending_news
    
    country = request.GET.get('country', 'in')
    category = request.GET.get('category', 'general')
    
    result = fetch_trending_news(category=category, country=country, page_size=10)
    
    if result:
        return JsonResponse(result)
    return JsonResponse({'success': False, 'articles': [], 'error': 'Unable to fetch trending news'})


def for_you_feed(request):
    """Personalized For You feed page"""
    from .recommendation_engine import generate_personalized_feed
    
    user = request.user if request.user.is_authenticated else None
    
    # Initial load (page 1)
    feed_data = generate_personalized_feed(user, page=1, page_size=12)
    
    context = {
        'articles': feed_data.get('articles', []),
        'is_cold_start': feed_data.get('is_cold_start', True),
        'has_more': feed_data.get('has_more', False),
        'feed_source': feed_data.get('source', 'unknown'),
    }
    
    return render(request, 'news/for_you.html', context)


def api_for_you_feed(request):
    """AJAX endpoint for infinite scroll on For You feed"""
    from .recommendation_engine import generate_personalized_feed
    
    user = request.user if request.user.is_authenticated else None
    page = int(request.GET.get('page', 1))
    
    feed_data = generate_personalized_feed(user, page=page, page_size=12)
    
    return JsonResponse(feed_data)


def api_track_interaction(request):
    """AJAX endpoint to track user interactions for personalization"""
    from .recommendation_engine import track_user_interaction
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'})
    
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Login required'})
    
    import json
    try:
        data = json.loads(request.body)
        interaction_type = data.get('type', '')
        interaction_data = data.get('data', {})
        
        track_user_interaction(request.user, interaction_type, interaction_data)
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})



