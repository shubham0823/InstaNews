from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from news.models import Profile, News
from .forms import CustomUserCreationForm, CustomAuthenticationForm, ProfileEditForm

def register(request):
    if request.user.is_authenticated:
        return redirect('news:landing_page')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('news:landing_page')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

def user_login(request):
    if request.user.is_authenticated:
        return redirect('news:landing_page')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, 'Logged in successfully!')
            
            # Redirect to next page if specified
            next_page = request.GET.get('next')
            if next_page:
                return redirect(next_page)
            return redirect('news:landing_page')
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def user_logout(request):
    logout(request)
    messages.success(request, 'Logged out successfully!')
    return redirect('news:landing_page')

@login_required
def profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    # Get user's news posts
    user_news = News.objects.filter(author=request.user).order_by('-created_at')
    
    # Get user's reshared news
    reshared_news = News.objects.filter(shares__user=request.user).order_by('-shares__shared_at')
    
    context = {
        'u_form': u_form,
        'p_form': p_form,
        'user_news': user_news,
        'reshared_news': reshared_news
    }
    return render(request, 'accounts/profile.html', context)

@login_required
def user_profile(request, username):
    user = get_object_or_404(User, username=username)
    user_news = News.objects.filter(author=user).order_by('-created_at')
    reshared_news = News.objects.filter(shares__user=user).order_by('-shares__shared_at')
    
    # Check if the current user follows this user
    is_following = False
    if request.user.is_authenticated:
        is_following = request.user.profile.following.filter(user=user).exists()
    
    context = {
        'profile_user': user,
        'user_news': user_news,
        'reshared_news': reshared_news,
        'is_following': is_following
    }
    return render(request, 'accounts/user_profile.html', context)

@login_required
def follow_toggle(request, username):
    user_to_follow = get_object_or_404(User, username=username)
    
    if request.user == user_to_follow:
        messages.warning(request, 'You cannot follow yourself.')
        return redirect('user_profile', username=username)
    
    if request.user.profile.following.filter(user=user_to_follow).exists():
        request.user.profile.following.remove(user_to_follow.profile)
        action = 'unfollowed'
    else:
        request.user.profile.following.add(user_to_follow.profile)
        action = 'followed'
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'action': action,
            'followers_count': user_to_follow.profile.followers.count()
        })
    
    messages.success(request, f'You have {action} {user_to_follow.username}!')
    return redirect('user_profile', username=username)

@login_required
def followers_list(request, username):
    user = get_object_or_404(User, username=username)
    followers = user.profile.followers.all()
    return render(request, 'accounts/followers_list.html', {
        'profile_user': user,
        'followers': followers
    })

@login_required
def following_list(request, username):
    user = get_object_or_404(User, username=username)
    following = user.profile.following.all()
    return render(request, 'accounts/following_list.html', {
        'profile_user': user,
        'following': following
    })

@login_required
def profile_edit(request):
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            
            # If password was changed, log the user out
            if form.cleaned_data.get('new_password'):
                messages.info(request, 'Please log in again with your new password.')
                return redirect('login')
            
            return redirect('news:user_profile', username=request.user.username)
    else:
        form = ProfileEditForm(instance=request.user.profile)
    
    return render(request, 'accounts/profile_edit.html', {'form': form})

def password_reset_request(request):
    if request.method == 'POST':
        email = request.POST.get('email', '')
        users = User.objects.filter(email=email)
        
        if users.exists():
            user = users[0]
            subject = "Password Reset Requested"
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            email_template_name = "accounts/password_reset_email.html"
            context = {
                "email": user.email,
                'domain': request.get_host(),
                'site_name': 'NewsHub',
                "uid": uid,
                "user": user,
                'token': token,
                'protocol': 'https' if request.is_secure() else 'http',
            }
            
            email_body = render_to_string(email_template_name, context)
            
            send_mail(
                subject,
                email_body,
                'noreply@newshub.com',
                [user.email],
                fail_silently=False,
            )
            
            messages.success(request, 'Password reset email has been sent.')
            return redirect('accounts:login')
            
    return render(request, 'accounts/password_reset.html')

def password_reset_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')
            
            if not password1 or not password2:
                messages.error(request, 'Please enter both passwords.')
                return render(request, 'accounts/password_reset_confirm.html')
            
            if password1 != password2:
                messages.error(request, 'Passwords do not match.')
                return render(request, 'accounts/password_reset_confirm.html')
            
            # Password validation
            if len(password1) < 8:
                messages.error(request, 'Password must be at least 8 characters long.')
                return render(request, 'accounts/password_reset_confirm.html')
            
            if password1.isdigit():
                messages.error(request, 'Password cannot be entirely numeric.')
                return render(request, 'accounts/password_reset_confirm.html')
            
            if password1.lower() == user.username.lower():
                messages.error(request, 'Password cannot be too similar to your username.')
                return render(request, 'accounts/password_reset_confirm.html')
            
            # If all validations pass, set the new password
            user.set_password(password1)
            user.save()
            messages.success(request, 'Your password has been reset successfully. You can now log in with your new password.')
            return redirect('accounts:login')
        
        return render(request, 'accounts/password_reset_confirm.html')
    else:
        messages.error(request, 'The reset link is invalid or has expired.')
        return redirect('accounts:login')
