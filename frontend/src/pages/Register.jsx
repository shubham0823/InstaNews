import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/Button';

export default function Register() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleRegister = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    
    try {
      await axios.post('http://127.0.0.1:8000/api/accounts/register/', {
        username,
        email,
        password
      });
      
      // Auto login after registration
      const { data } = await axios.post('http://127.0.0.1:8000/api/accounts/login/', {
        username,
        password
      });
      
      localStorage.setItem('access_token', data.access);
      localStorage.setItem('refresh_token', data.refresh);
      
      navigate('/');
      window.location.reload();
    } catch (err) {
      setError(err.response?.data?.error || 'Something went wrong during registration.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 glass-panel p-10 rounded-3xl animate-fade-in relative overflow-hidden">
        
        <div className="absolute top-0 left-0 -mt-10 -ml-10 w-40 h-40 bg-indigo-500 rounded-full blur-3xl opacity-20 pointer-events-none"></div>
        <div className="absolute bottom-0 right-0 -mb-10 -mr-10 w-40 h-40 bg-blue-500 rounded-full blur-3xl opacity-20 pointer-events-none"></div>

        <div>
          <h2 className="mt-6 text-center text-4xl font-extrabold text-gray-900 dark:text-white">
            Join NewsHub
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600 dark:text-gray-400">
            Create an account to personalize your global feed.
          </p>
        </div>
        
        <form className="mt-8 space-y-6 relative z-10" onSubmit={handleRegister}>
          {error && (
            <div className="bg-red-50 dark:bg-red-900/30 text-red-500 p-4 rounded-xl text-sm font-medium text-center border border-red-200 dark:border-red-800">
              {error}
            </div>
          )}
          
          <div className="space-y-4">
            <Input
              label="Username"
              type="text"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="unique_handle"
            />
            <Input
              label="Email Address"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@domain.com"
            />
            <Input
              label="Password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Create a strong password"
            />
          </div>

          <Button type="submit" className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 shadow-indigo-500/20" size="lg" isLoading={isLoading}>
            Create Account
          </Button>
          
          <p className="text-center text-sm font-medium text-gray-600 dark:text-gray-400">
            Already have an account?{' '}
            <Link to="/login" className="text-blue-600 hover:text-blue-500 transition-colors">
              Sign in securely
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
