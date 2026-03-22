import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Heart, MessageCircle, Share2, Globe, MapPin } from 'lucide-react';
import { Button } from '../ui/Button';
import axios from '../../api/axios';

export default function NewsCard({ post }) {
  const [likesCount, setLikesCount] = useState(post.likes_count || 0);
  const [isLiked, setIsLiked] = useState(post.is_liked || false);

  const toggleLike = async () => {
    try {
      const { data } = await axios.post(`news/posts/${post.id}/like/`);
      setIsLiked(data.action === 'liked');
      setLikesCount(data.likes_count);
    } catch (e) {
      console.error('Like failed', e);
      // Optional: Redirect to login or show toast
    }
  };

  const isIndia = post.geo_category === 'india';

  return (
    <article className="glass-panel rounded-3xl overflow-hidden animate-fade-in group">
      {/* Header */}
      <div className="p-4 sm:p-5 flex items-start justify-between">
        <div className="flex items-center gap-3">
          <Link to={`/profile/${post.author?.username}`} className="shrink-0">
            {post.author?.avatar ? (
              <img src={post.author.avatar} alt={post.author.username} className="w-10 h-10 rounded-xl object-cover" />
            ) : (
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-gray-200 to-gray-300 flex items-center justify-center text-gray-600 font-bold">
                {post.author?.username?.charAt(0).toUpperCase()}
              </div>
            )}
          </Link>
          <div>
            <Link to={`/profile/${post.author?.username}`} className="font-bold text-gray-900 dark:text-gray-100 hover:text-blue-600 dark:hover:text-blue-400">
              {post.author?.username}
            </Link>
            <p className="text-xs text-gray-500 flex items-center gap-1.5 mt-0.5">
              <span>{new Date(post.created_at).toLocaleDateString()}</span>
              <span>•</span>
              <span className={`inline-flex items-center gap-1 font-medium ${isIndia ? 'text-orange-600 dark:text-orange-400' : 'text-blue-600 dark:text-blue-400'}`}>
                {isIndia ? <MapPin className="w-3 h-3" /> : <Globe className="w-3 h-3" />}
                {isIndia ? 'India Trending' : 'Global Trending'}
              </span>
            </p>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="px-4 sm:px-5 pb-3">
        <h3 className="text-xl font-bold mb-2 text-gray-900 dark:text-white leading-tight">
          {post.title}
        </h3>
        <p className="text-gray-600 dark:text-gray-300 text-sm whitespace-pre-wrap line-clamp-3">
          {post.content}
        </p>

        {/* Tags */}
        <div className="mt-4 flex flex-wrap gap-2">
          {post.hashtags?.map((tag) => (
            <Link key={tag.id} to={`/explore?q=${tag.name}`} className="text-xs font-semibold px-2.5 py-1 bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400 rounded-lg hover:bg-blue-100 transition-colors">
              #{tag.name}
            </Link>
          ))}
          {post.tagged_users?.map((user) => (
            <Link key={user.id} to={`/profile/${user.username}`} className="text-xs font-semibold px-2.5 py-1 bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors">
              @{user.username}
            </Link>
          ))}
        </div>
      </div>

      {/* Media (16:9) */}
      {(post.video || (post.images && post.images.length > 0)) && (
        <div className="relative w-full aspect-video bg-gray-100 dark:bg-gray-900 overflow-hidden">
          {post.video ? (
            <video 
              src={post.video} 
              className="w-full h-full object-contain"
              controls
              playsInline
            />
          ) : (
            <img 
              src={post.images[0].image} 
              alt={post.title} 
              className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-[1.02]"
            />
          )}
        </div>
      )}

      {/* Actions */}
      <div className="px-4 py-3 sm:px-5 border-t border-gray-100 dark:border-gray-800 flex items-center justify-between">
        <div className="flex gap-2 text-gray-500 dark:text-gray-400">
          <Button variant="ghost" size="icon" onClick={toggleLike} className={isLiked ? 'text-red-500 bg-red-50 dark:bg-red-500/10 hover:text-red-600' : ''}>
            <Heart className={`w-5 h-5 ${isLiked ? 'fill-current' : ''}`} />
            <span className="ml-2 text-sm font-medium">{likesCount}</span>
          </Button>
          <Button variant="ghost" size="icon">
            <MessageCircle className="w-5 h-5" />
            <span className="ml-2 text-sm font-medium">{post.comments_count || 0}</span>
          </Button>
          <Button variant="ghost" size="icon">
            <Share2 className="w-5 h-5" />
            <span className="ml-2 text-sm font-medium">{post.shares_count || 0}</span>
          </Button>
        </div>
        <Button variant="outline" size="sm">
          Read Story
        </Button>
      </div>
    </article>
  );
}
