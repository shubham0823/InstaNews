from django.conf import settings
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "news_website.settings")
django.setup()

from news.models import News
from news.forms import NewsForm
from django.core.files.uploadedfile import SimpleUploadedFile

news = News.objects.get(pk=21)
print(f"News 21: type={news.news_type}, video={news.video}, images={news.images.count()}")

# Simulate edit exactly how user submitted it: switching from video to image
data = {
    'title': news.title,
    'content': news.content,
    'news_type': 'short',
    'media_type': 'image',
}

files = {
    'images': SimpleUploadedFile("test_image.jpg", b"file_content", content_type="image/jpeg"),
    # User might not upload a video file when switching to image
}

form = NewsForm(data, files, instance=news)
print(f"Is valid? {form.is_valid()}")
print(f"Errors: {form.errors}")
