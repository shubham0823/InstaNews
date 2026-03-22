import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { Home, Compass, User, PenTool, Hash, Settings } from 'lucide-react';
import CreatePostModal from '../news/CreatePostModal';

export default function Sidebar() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const token = localStorage.getItem('access_token');
  
  const navLinks = [
    { to: '/', label: 'Home', icon: Home, exact: true },
    { to: '/explore', label: 'Explore', icon: Compass },
    { to: '/trending', label: 'Trending Tags', icon: Hash },
    ...(token ? [
      { to: '/profile/me', label: 'My Profile', icon: User },
      { to: '/settings', label: 'Settings', icon: Settings },
    ] : []),
  ];

  return (
    <aside className="w-full glass-panel rounded-3xl p-4 pt-6 space-y-6 min-h-[70vh]">
      <div className="space-y-2">
        {navLinks.map(({ to, label, icon: Icon, exact }) => (
          <NavLink
            key={to}
            to={to}
            end={exact}
            className={({ isActive }) => 
              `flex items-center gap-4 px-4 py-3 rounded-2xl font-medium transition-all ${
                isActive 
                  ? 'bg-blue-600 shadow-md shadow-blue-500/20 text-white' 
                  : 'text-gray-600 hover:bg-white dark:text-gray-400 dark:hover:bg-gray-800 hover:text-blue-600 dark:hover:text-white'
              }`
            }
          >
            <Icon className="w-5 h-5" />
            <span className="text-base">{label}</span>
          </NavLink>
        ))}
      </div>

      {token && (
        <div className="pt-6 border-t border-gray-100 dark:border-gray-800">
          <button 
            onClick={() => setIsModalOpen(true)}
            className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white px-4 py-3.5 rounded-2xl font-bold shadow-lg shadow-blue-500/30 hover:shadow-blue-500/50 transition-all hover:-translate-y-0.5"
          >
            <PenTool className="w-5 h-5" />
            <span>Create News</span>
          </button>
        </div>
      )}
      
      <CreatePostModal 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)} 
        onSuccess={() => window.location.reload()} 
      />
      
      {/* Mini Footer */}
      <div className="absolute bottom-6 left-6 right-6 text-xs text-gray-400 text-center space-x-3">
        <a href="#" className="hover:text-blue-500">Privacy</a>
        <a href="#" className="hover:text-blue-500">Terms</a>
        <a href="#" className="hover:text-blue-500">© 2026 NewsHub</a>
      </div>
    </aside>
  );
}
