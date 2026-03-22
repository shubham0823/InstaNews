from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.contrib.auth.models import User
from news.serializers import UserSerializer
from rest_framework.views import APIView

class RegisterAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')

        if not username or not password or not email:
            return Response({'error': 'Please provide username, email, and password'}, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username already taken'}, status=status.HTTP_400_BAD_REQUEST)
            
        if User.objects.filter(email=email).exists():
            return Response({'error': 'Email already registered'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=username, email=email, password=password)
        return Response({
            'user': UserSerializer(user, context={'request': request}).data,
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)

class CurrentUserAPIView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


from django.shortcuts import get_object_or_404
from news.serializers import ProfileSerializer
class ProfileRetrieveAPIView(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = UserSerializer

    def get_object(self):
        username = self.kwargs['username']
        return get_object_or_404(User, username=username)

class FollowToggleAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, username):
        user_to_follow = get_object_or_404(User, username=username)
        if request.user == user_to_follow:
            return Response({'error': 'Cannot follow yourself'}, status=status.HTTP_400_BAD_REQUEST)
            
        profile = request.user.profile
        if profile.following.filter(user=user_to_follow).exists():
            profile.following.remove(user_to_follow.profile)
            action = 'unfollowed'
        else:
            profile.following.add(user_to_follow.profile)
            action = 'followed'
            
        return Response({
            'status': 'success', 
            'action': action,
            'followers_count': user_to_follow.profile.followers.count()
        })
