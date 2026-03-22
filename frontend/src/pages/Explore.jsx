import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Globe, MapPin, Search } from 'lucide-react';
import axios from '../api/axios';
import NewsCard from '../components/news/NewsCard';
import { Skeleton } from '../components/ui/Skeleton';

export default function Explore() {
  const [searchParams, setSearchParams] = useSearchParams();
  const currentGeo = searchParams.get('geo') || 'global';
  const searchQuery = searchParams.get('q') || '';
  
  const [posts, setPosts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchExplore = async () => {
      setIsLoading(true);
      try {
        const { data } = await axios.get(`news/explore/?geo=${currentGeo}&q=${searchQuery}`);
        setPosts(data);
      } catch (error) {
        console.error('Explore failed:', error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchExplore();
  }, [currentGeo, searchQuery]);

  const handleGeoSwitch = (geo) => {
    const params = new URLSearchParams(searchParams);
    params.set('geo', geo);
    setSearchParams(params);
  };

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      {/* Search Header */}
      <header className="glass-panel p-6 rounded-3xl space-y-6">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-extrabold text-gray-900 dark:text-white flex items-center gap-3">
              Explore
            </h1>
            <p className="mt-1 text-gray-600 dark:text-gray-400">
              Discover what's trending across the network.
            </p>
          </div>
          
          {/* Geo Toggles */}
          <div className="flex bg-gray-100 dark:bg-gray-800 p-1.5 rounded-xl self-stretch md:self-auto">
            <button
              onClick={() => handleGeoSwitch('global')}
              className={`flex-1 md:flex-none flex items-center justify-center gap-2 px-5 py-2.5 rounded-lg font-bold text-sm transition-all ${
                currentGeo === 'global'
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'text-gray-500 hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              <Globe className="w-4 h-4" /> Global
            </button>
            <button
              onClick={() => handleGeoSwitch('india')}
              className={`flex-1 md:flex-none flex items-center justify-center gap-2 px-5 py-2.5 rounded-lg font-bold text-sm transition-all ${
                currentGeo === 'india'
                  ? 'bg-orange-600 text-white shadow-md'
                  : 'text-gray-500 hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              <MapPin className="w-4 h-4" /> India
            </button>
          </div>
        </div>
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
            <h3 className="text-xl font-bold text-gray-900 dark:text-white">Nothing found</h3>
            <p className="mt-2 text-gray-500">There are no trending stories in this category right now.</p>
          </div>
        )}
      </div>
    </div>
  );
}
