# NewsHub — Premium Social News Platform

NewsHub is a bleeding-edge news platform that merges traditional news aggregation with modern social media mechanics. It features a fully decoupled architecture with a **Django REST Framework (DRF)** backend and a **React (Vite)** Single Page Application (SPA) frontend, designed for high performance and premium UI/UX.

---

## 🚀 Tech Stack

### Backend (API Engine)
- **Django 5.1** & **Django REST Framework**
- **JWT (SimpleJWT)** — Secure stateless authentication
- **PostgreSQL** — Production database support (via `dj-database-url`)
- **WhiteNoise** — Efficient static file serving
- **Common APIs** — NewsAPI, World News API, Finnhub Financial API

### Frontend (SPA)
- **React 18** (Vite-powered)
- **Tailwind CSS** — Modern utility-first styling with Glassmorphism
- **Framer Motion** — Fluid page transitions and micro-interactions
- **React Query (TanStack)** — Powerful server-state management
- **Axios** — Custom interceptors for automatic JWT handling
- **Lucide React** — Crisp, consistent iconography

---

## ✨ Core Features

- **Decoupled Architecture**: Blazing fast SPA frontend communicating via REST APIs.
- **Dual Trending Carousels**: Real-time "India Trending" vs "World Trending" news sections with velocity scoring.
- **Interactive Feed**: Personalized "For You" feed based on your follow network.
- **Post Composition**: Advanced modal-based creator supporting high-res **Video** and **Multiple Images**.
- **Social Ecosystem**: Likes, comments, shares, and a robust user follow system.
- **Dynamic Profiles**: Rich user profiles with unique bios, follower counts, and post history.
- **Geo-Smart Logic**: Automatic categorization of news into regional and global buckets.
- **Market Ticker**: Real-time stock and crypto market updates via financial APIs.

---

## 🛠️ Local Development Setup

### 1. Backend Setup
```bash
# Clone the repository
git clone <repository-url>
cd InstaNews

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations and start server
python manage.py migrate
python manage.py runserver
```

### 2. Frontend Setup
On a separate terminal:
```bash
cd frontend
npm install
npm run dev
```
The application will be available at `http://localhost:5173`.

---

## 🔑 Environment Variables

The project uses a `.env` file for configuration. See `.env.example` for the full template.

| Key | Description |
|---|---|
| `SECRET_KEY` | Django secret key for security |
| `DEBUG` | Set to `False` in production |
| `DATABASE_URL` | PostgreSQL connection string |
| `NEWS_API_KEY` | Key from newsapi.org |
| `WORLD_NEWS_API_KEY` | Key from worldnewsapi.com |
| `FINNHUB_API_KEY` | Key from finnhub.io |

---

## ☁️ Deployment (Vercel)

This project is optimized for deployment on **Vercel**.

1. **Connect Repository**: Sync your GitHub/GitLab repo to Vercel.
2. **Environment Variables**: Add all keys from `.env.example` to Vercel's Environment Variables settings.
3. **Build Settings**: Vercel will automatically detect `vercel.json` and build both the Python backend and React frontend.
4. **PostgreSQL**: Connect a Vercel Postgres or Neon database and provide the `DATABASE_URL`.

---

## 📁 Project Structure

```text
InstaNews/
├── accounts/           # User & Profile logic
├── news/               # News, Trending & Social logic
├── news_website/       # Django project core configuration
├── frontend/           # React SPA (Vite, Tailwind, Framer)
│   ├── src/components/ # Atomic UI & News components
│   └── src/pages/      # Route-level pages (Home, Explore, Login)
├── templates/          # Backend fallback templates
├── static/             # Global static assets
├── vercel.json         # Deployment configuration
└── .env.example        # Configuration template
```

---

## 🛡️ License
Distributed under the MIT License. See `LICENSE` for more information.