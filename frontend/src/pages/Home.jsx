import React, { useEffect, useState } from 'react';
import axios from '../api/axios';
import NewsCard from '../components/news/NewsCard';
import { Skeleton } from '../components/ui/Skeleton';

export default function Home() {
  const [posts, setPosts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const isAuthenticated = !!localStorage.getItem('access_token');

  useEffect(() => {
    const fetchFeed = async () => {
      try {
        // If logged in, fetch targeted feed, otherwise fetch global explore feed
        const endpoint = isAuthenticated ? 'news/feed/' : 'news/explore/';
        const { data } = await axios.get(endpoint);
        setPosts(data);
      } catch (error) {
        console.error('Error fetching feed:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchFeed();
  }, [isAuthenticated]);

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      {/* Header Section */}
      <header className="mb-8">
        <h1 className="text-3xl font-extrabold text-gray-900 dark:text-white">
          {isAuthenticated ? 'For You' : 'Top Stories'}
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400 font-medium">
          {isAuthenticated ? 'Personalized updates from people you follow.' : 'Discover breaking news worldwide.'}
        </p>
      </header>

      {/* Feed Layout */}
      <div className="space-y-6">
        {isLoading ? (
          <>
            <Skeleton className="w-full h-96" />
            <Skeleton className="w-full h-80" />
            <Skeleton className="w-full h-96" />
          </>
        ) : posts.length > 0 ? (
          posts.map(post => <NewsCard key={post.id} post={post} />)
        ) : (
          <div className="glass-panel p-12 text-center rounded-3xl">
            <h3 className="text-xl font-bold text-gray-900 dark:text-white">No posts to show</h3>
            <p className="mt-2 text-gray-500">Your feed is surprisingly empty.</p>
          </div>
        )}
      </div>
    </div>
  );
}
