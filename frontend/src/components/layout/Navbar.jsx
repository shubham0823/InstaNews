import React from 'react';
import { Link } from 'react-router-dom';
import { Search, Bell, User as UserIcon } from 'lucide-react';

export default function Navbar() {
  const token = localStorage.getItem('access_token');

  return (
    <nav className="fixed top-0 w-full z-50 glass-panel border-b border-white/20 dark:border-gray-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          
          {/* Brand */}
          <Link to="/" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center shadow-lg">
              <span className="text-white font-bold text-lg leading-none">N</span>
            </div>
            <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-gray-900 to-gray-600 dark:from-white dark:to-gray-300">
              NewsHub
            </span>
          </Link>

          {/* Search (Desktop) */}
          <div className="hidden md:flex flex-1 max-w-md mx-8">
            <div className="relative w-full">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search className="h-4 w-4 text-gray-400" />
              </div>
              <input 
                type="text" 
                placeholder="Search news, topics, or people..." 
                className="w-full pl-10 pr-4 py-2 border-0 rounded-2xl bg-gray-100/80 dark:bg-gray-800/80 focus:ring-2 focus:ring-blue-500 focus:bg-white dark:focus:bg-gray-900 transition-all text-sm dark:text-gray-200 shadow-inner"
              />
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-4">
            {token ? (
              <>
                <button className="p-2 rounded-full text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800 transition-colors relative">
                  <Bell className="h-5 w-5" />
                  <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full border border-white dark:border-gray-900"></span>
                </button>
                <Link to="/profile/me" className="p-1.5 rounded-full border-2 border-transparent hover:border-blue-500 transition-colors">
                  <div className="w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center overflow-hidden">
                    <UserIcon className="h-5 w-5 text-gray-500 dark:text-gray-400" />
                  </div>
                </Link>
              </>
            ) : (
              <div className="flex gap-2">
                <Link to="/login" className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
                  Log in
                </Link>
                <Link to="/register" className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-xl shadow-md shadow-blue-500/20 transition-all active:scale-95">
                  Sign up
                </Link>
              </div>
            )}
          </div>

        </div>
      </div>
    </nav>
  );
}
