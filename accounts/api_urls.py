from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import api_views

app_name = 'accounts_api'

urlpatterns = [
    path('register/', api_views.RegisterAPIView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/', api_views.CurrentUserAPIView.as_view(), name='current_user'),
    path('profile/<str:username>/', api_views.ProfileRetrieveAPIView.as_view(), name='profile_detail'),
    path('profile/<str:username>/follow/', api_views.FollowToggleAPIView.as_view(), name='follow_toggle'),
]
