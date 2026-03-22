import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { MapPin, Users } from 'lucide-react';
import axios from '../api/axios';
import NewsCard from '../components/news/NewsCard';
import { Button } from '../components/ui/Button';
import { Skeleton } from '../components/ui/Skeleton';

export default function Profile() {
  const { username } = useParams();
  const [profile, setProfile] = useState(null);
  const [posts, setPosts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isFollowing, setIsFollowing] = useState(false);
  const [followersCount, setFollowersCount] = useState(0);

  const currentUser = localStorage.getItem('username') || ''; // Optional: stored on login
  
  useEffect(() => {
    const fetchProfileData = async () => {
      setIsLoading(true);
      try {
        const targetUsername = username === 'me' ? 'me' : username; 
        // Note: For "me", the backend needs a specific 'me' override or we use CurrentUserAPI
        // Since api/accounts/me/ exists, let's logic switch
        
        let profileData;
        if (username === 'me') {
          const res = await axios.get('accounts/me/');
          profileData = res.data;
        } else {
          const res = await axios.get(`accounts/profile/${username}/`);
          profileData = res.data;
        }
        
        setProfile(profileData);
        setFollowersCount(profileData.profile?.followers_count || 0);

        // Fetch user posts
        const postsRes = await axios.get(`news/explore/?author=${profileData.username}`);
        setPosts(postsRes.data);

      } catch (error) {
        console.error('Failed to fetch profile', error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchProfileData();
  }, [username]);

  const toggleFollow = async () => {
    try {
      const { data } = await axios.post(`accounts/profile/${profile.username}/follow/`);
      setIsFollowing(data.action === 'followed');
      setFollowersCount(data.followers_count);
    } catch (e) {
      console.error(e);
    }
  };

  if (isLoading) {
    return (
      <div className="max-w-3xl mx-auto space-y-6">
        <Skeleton className="w-full h-64" />
        <Skeleton className="w-full h-80" />
      </div>
    );
  }

  if (!profile) return <div className="text-center p-12 text-xl font-bold">User Not Found</div>;

  const isOwnProfile = username === 'me' || currentUser === profile.username;

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      {/* Profile Header */}
      <div className="glass-panel p-6 sm:p-10 rounded-3xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500 rounded-full blur-3xl opacity-10 pointer-events-none"></div>
        
        <div className="flex flex-col sm:flex-row items-center gap-6 sm:gap-8 relative z-10">
          <div className="w-32 h-32 rounded-3xl bg-gray-100 dark:bg-gray-800 shadow-xl border-4 border-white dark:border-gray-800 overflow-hidden shrink-0">
            {profile.avatar ? (
              <img src={profile.avatar} alt={profile.username} className="w-full h-full object-cover" />
            ) : (
              <div className="w-full h-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-4xl font-black text-white">
                {profile.username.charAt(0).toUpperCase()}
              </div>
            )}
          </div>
          
          <div className="flex-1 text-center sm:text-left space-y-2">
            <h1 className="text-3xl font-extrabold text-gray-900 dark:text-white">{profile.username}</h1>
            <p className="text-gray-600 dark:text-gray-300 max-w-lg">{profile.bio || 'This user prefers to keep an air of mystery about them.'}</p>
            
            <div className="flex flex-wrap items-center justify-center sm:justify-start gap-4 text-sm font-semibold text-gray-500 pt-2">
              <span className="flex items-center gap-1.5"><MapPin className="w-4 h-4" /> {profile.country || 'Global'}</span>
              <span className="flex items-center gap-1.5"><Users className="w-4 h-4 text-blue-500" /> {followersCount} Followers</span>
              <span className="flex items-center gap-1.5"><Users className="w-4 h-4 text-green-500" /> {profile.profile?.following_count || 0} Following</span>
            </div>
          </div>
          
          {!isOwnProfile && (
            <div className="shrink-0">
              <Button 
                onClick={toggleFollow} 
                variant={isFollowing ? 'outline' : 'primary'} 
                className="w-full sm:w-auto px-8 py-3 rounded-xl shadow-lg"
              >
                {isFollowing ? 'Following' : 'Follow'}
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Feed */}
      <div className="space-y-6">
        <h3 className="text-xl font-bold text-gray-900 dark:text-white px-2">Published Stories ({posts.length})</h3>
        {posts.length > 0 ? (
          posts.map(post => <NewsCard key={post.id} post={post} />)
        ) : (
          <div className="glass-panel p-12 text-center rounded-3xl">
            <p className="text-gray-500 font-medium">No stories published yet.</p>
          </div>
        )}
      </div>
    </div>
  );
}
