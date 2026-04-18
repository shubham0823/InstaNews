from django import forms
from .models import News, NewsImage
from .widgets import MultipleFileInput
import magic
from django.contrib.auth.models import User

class NewsForm(forms.ModelForm):
    news_type = forms.ChoiceField(
        choices=[('short', 'Short Format'), ('long', 'Long Format')],
        widget=forms.RadioSelect(attrs={'class': 'sr-only'})
    )
    
    media_type = forms.ChoiceField(
        choices=[('none', 'No Media'), ('image', 'Image'), ('video', 'Video')],
        required=False,
        widget=forms.RadioSelect(attrs={'class': 'sr-only'})
    )
    
    images = forms.Field(
        required=False,
        widget=MultipleFileInput(attrs={
            'accept': 'image/*',
            'class': 'sr-only'
        }),
        help_text="Upload images"
    )
    
    video = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'accept': 'video/*',
            'class': 'sr-only'
        }),
        help_text="Upload video"
    )
    
    hashtags = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md',
            'placeholder': 'Add hashtags (separated by spaces)',
            'data-role': 'hashtag-input'
        }),
        help_text="Add hashtags starting with # (e.g., #news #trending)"
    )
    
    tagged_users = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md',
            'placeholder': 'Tag users (separated by spaces)',
            'data-role': 'user-tag-input'
        }),
        help_text="Tag users by their username (e.g., @user1 @user2)"
    )

    class Meta:
        model = News
        fields = ['title', 'content', 'news_type', 'video', 'hashtags', 'tagged_users']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md',
                'placeholder': 'Enter title'
            }),
            'content': forms.Textarea(attrs={
                'class': 'shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md',
                'placeholder': 'Write your news content here...',
                'rows': 5
            })
        }
    
    def clean(self):
        cleaned_data = super().clean()
        news_type = cleaned_data.get('news_type')
        content = cleaned_data.get('content')
        media_type = cleaned_data.get('media_type')
        images = self.files.getlist('images')
        video = cleaned_data.get('video')
        hashtags = cleaned_data.get('hashtags', '')
        tagged_users = cleaned_data.get('tagged_users', '')

        # Validate content length for short format
        if news_type == 'short' and content and len(content.split()) > 500:
            raise forms.ValidationError("Short format news cannot exceed 500 words.")

        # Validate media for short format
        if news_type == 'short':
            if media_type == 'image' and len(images) > 1:
                raise forms.ValidationError("Short format news can only have one image.")
            elif media_type == 'video' and video:
                # Add video length validation here if needed
                pass

        # Validate hashtags format
        if hashtags:
            hashtag_list = hashtags.split()
            for tag in hashtag_list:
                if not tag.startswith('#'):
                    raise forms.ValidationError(f"Hashtag '{tag}' must start with #")

        # Validate tagged users format and existence
        if tagged_users:
            tagged_list = tagged_users.split()
            for username in tagged_list:
                if not username.startswith('@'):
                    raise forms.ValidationError(f"Tagged user '{username}' must start with @")
                # Remove @ and check if user exists
                user = username[1:]
                if not User.objects.filter(username=user).exists():
                    raise forms.ValidationError(f"User '{user}' does not exist")

        return cleaned_data
    
    def clean_images(self):
        # Images are handled manually in the view via request.FILES.getlist('images')
        # Return whatever was submitted without standard FileField validation
        return self.files.getlist('images') if self.files else []
    
    def clean_video(self):
        video = self.cleaned_data.get('video')
        news_type = self.cleaned_data.get('news_type')
        media_type = self.cleaned_data.get('media_type')

        from django.core.files.uploadedfile import UploadedFile
        
        if video and isinstance(video, UploadedFile):
            if news_type == 'short' and media_type == 'video':
                # Check video duration using ffprobe
                try:
                    import subprocess
                    import tempfile
                    import os

                    # Create a temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
                        for chunk in video.chunks():
                            temp_file.write(chunk)
                        temp_file.flush()
                        
                        # Get video duration
                        result = subprocess.run([
                            'ffprobe', 
                            '-v', 'error', 
                            '-show_entries', 'format=duration', 
                            '-of', 'default=noprint_wrappers=1:nokey=1', 
                            temp_file.name
                        ], capture_output=True, text=True)
                        
                        duration = float(result.stdout)
                        if duration > 60:  # 60 seconds = 1 minute
                            raise forms.ValidationError('Video duration cannot exceed 1 minute for short format news.')
                        
                        # Clean up temporary file
                        os.unlink(temp_file.name)

                except Exception as e:
                    raise forms.ValidationError(f'Error processing video: {str(e)}. Please ensure it is a valid video file.')

            # Validate video mime type
            try:
                mime = magic.from_buffer(video.read(1024), mime=True)
                if not mime.startswith('video/'):
                    raise forms.ValidationError('Uploaded file is not a valid video.')
                video.seek(0)  # Reset file pointer
            except Exception as e:
                raise forms.ValidationError('Error validating video format.')

        return video
    
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if len(title) < 5:
            raise forms.ValidationError('Title must be at least 5 characters long.')
        return title
    
    def clean_content(self):
        content = self.cleaned_data.get('content')
        if len(content) < 20:
            raise forms.ValidationError('Content must be at least 20 characters long.')
        return content 