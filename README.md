# NewsHub - Social News Platform

A modern news platform that combines traditional news aggregation with social media features. Users can create, share, and interact with news in both short and long formats.

## Features

- User authentication and profiles
- Short and long format news posts
- Image and video support
- Social features (likes, comments, shares)
- Follow system
- World news integration via World News API
- Trending news section
- Stock market updates
- Responsive design using Tailwind CSS

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd news-website
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the project root and add:
```
WORLD_NEWS_API_KEY=your_api_key_here
SECRET_KEY=your_django_secret_key
DEBUG=True
```

5. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

6. Create a superuser:
```bash
python manage.py createsuperuser
```

7. Run the development server:
```bash
python manage.py runserver
```

Visit `http://localhost:8000` to access the application.

## Project Structure

- `news/` - Main application directory
  - `models.py` - Database models
  - `views.py` - View functions
  - `urls.py` - URL routing
  - `admin.py` - Admin interface configuration
  - `signals.py` - Signal handlers

- `templates/` - HTML templates
  - `base.html` - Base template
  - `news/` - News-specific templates

- `static/` - Static files (CSS, JavaScript, images)

- `media/` - User-uploaded files
  - `avatars/` - User profile pictures
  - `news_images/` - News post images
  - `news_videos/` - News post videos