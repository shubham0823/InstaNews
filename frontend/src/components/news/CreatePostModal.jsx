import React, { useState, useRef } from 'react';
import { X, Image as ImageIcon, Video, Hash, Globe, MapPin } from 'lucide-react';
import axios from '../../api/axios';
import { Button } from '../ui/Button';

export default function CreatePostModal({ isOpen, onClose, onSuccess }) {
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [newsType, setNewsType] = useState('short');
  const [geoCategory, setGeoCategory] = useState('global');
  const [hashtags, setHashtags] = useState('');
  const [taggedUsers, setTaggedUsers] = useState('');
  const [mediaFiles, setMediaFiles] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  
  const fileInputRef = useRef(null);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    
    // Switch to FormData to handle multipart forms securely via Axios
    const formData = new FormData();
    formData.append('title', title);
    formData.append('content', content);
    formData.append('news_type', newsType);
    formData.append('geo_category', geoCategory);
    formData.append('hashtags_text', hashtags);
    formData.append('tagged_users_text', taggedUsers);
    
    // Append all media files
    Array.from(mediaFiles).forEach((file) => {
      // Assuming DRF processes 'images' array. Wait, my serializer checks request.FILES.getlist('images')
      // and request.data.get('video')
      if (file.type.startsWith('video/')) {
        formData.append('video', file);
      } else {
        formData.append('images', file);
      }
    });

    try {
      await axios.post('news/posts/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      if (onSuccess) onSuccess();
      onClose();
    } catch (err) {
      console.error('Failed to create post:', err);
      alert('Error creating post. Check console.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files) {
      setMediaFiles((prev) => [...prev, ...Array.from(e.target.files)]);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-2xl bg-white dark:bg-gray-900 rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between bg-white dark:bg-gray-900 sticky top-0 z-10">
          <h2 className="text-xl font-extrabold text-gray-900 dark:text-white">Create News</h2>
          <button onClick={onClose} className="p-2 -mr-2 text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable Body */}
        <div className="p-6 overflow-y-auto custom-scrollbar">
          <form id="create-post-form" onSubmit={handleSubmit} className="space-y-6">
            
            <input
              type="text"
              required
              placeholder="What's breaking right now?"
              className="w-full text-2xl font-bold bg-transparent border-0 border-b border-transparent focus:border-blue-500 focus:ring-0 placeholder-gray-400 px-0 py-2 transition-colors dark:text-white outline-none"
              value={title}
              onChange={e => setTitle(e.target.value)}
            />

            <textarea
              required
              rows={4}
              placeholder="Share the full story..."
              className="w-full text-base bg-transparent border-0 focus:ring-0 px-0 py-2 resize-none text-gray-700 dark:text-gray-300 placeholder-gray-400 focus:outline-none"
              value={content}
              onChange={e => setContent(e.target.value)}
            />

            {/* Media Previews */}
            {mediaFiles.length > 0 && (
              <div className="flex gap-4 overflow-x-auto pb-2 custom-scrollbar">
                {mediaFiles.map((f, i) => (
                  <div key={i} className="relative w-32 h-32 shrink-0 rounded-2xl overflow-hidden group shadow-md border border-gray-200 dark:border-gray-800">
                    <img src={URL.createObjectURL(f)} alt="Preview" className="w-full h-full object-cover" />
                    <button type="button" onClick={() => setMediaFiles(mediaFiles.filter((_, idx) => idx !== i))} className="absolute top-2 right-2 p-1.5 bg-black/50 hover:bg-black/70 rounded-full text-white backdrop-blur-md opacity-0 group-hover:opacity-100 transition-opacity">
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}

            {/* Toggles */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-3">
                <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">Format</label>
                <div className="flex bg-gray-100 dark:bg-gray-800 p-1.5 rounded-xl">
                  <button type="button" onClick={() => setNewsType('short')} className={`flex-1 py-1.5 text-sm font-semibold rounded-lg transition-all ${newsType === 'short' ? 'bg-white text-blue-600 shadow dark:bg-gray-700 dark:text-white' : 'text-gray-500'}`}>Short</button>
                  <button type="button" onClick={() => setNewsType('long')} className={`flex-1 py-1.5 text-sm font-semibold rounded-lg transition-all ${newsType === 'long' ? 'bg-white text-blue-600 shadow dark:bg-gray-700 dark:text-white' : 'text-gray-500'}`}>Long</button>
                </div>
              </div>
              <div className="space-y-3">
                <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">Audience</label>
                <div className="flex bg-gray-100 dark:bg-gray-800 p-1.5 rounded-xl">
                  <button type="button" onClick={() => setGeoCategory('global')} className={`flex-1 py-1.5 text-sm font-semibold rounded-lg transition-all flex items-center justify-center gap-1.5 ${geoCategory === 'global' ? 'bg-white text-blue-600 shadow dark:bg-gray-700 dark:text-white' : 'text-gray-500'}`}><Globe className="w-4 h-4" /> Global</button>
                  <button type="button" onClick={() => setGeoCategory('india')} className={`flex-1 py-1.5 text-sm font-semibold rounded-lg transition-all flex items-center justify-center gap-1.5 ${geoCategory === 'india' ? 'bg-white text-orange-600 shadow dark:bg-gray-700 dark:text-white' : 'text-gray-500'}`}><MapPin className="w-4 h-4" /> India</button>
                </div>
              </div>
            </div>

            {/* Tags section */}
            <div className="space-y-4 pt-4 border-t border-gray-100 dark:border-gray-800">
              <div className="flex items-center gap-3">
                <Hash className="w-5 h-5 text-gray-400" />
                <input type="text" placeholder="Tags (e.g. #technology #AI)" className="flex-1 bg-transparent border-0 text-sm focus:ring-0 placeholder-gray-400 dark:text-white outline-none" value={hashtags} onChange={e => setHashtags(e.target.value)} />
              </div>
              <div className="flex items-center gap-3">
                <span className="text-gray-400 font-extrabold px-1">@</span>
                <input type="text" placeholder="Tag users (e.g. @janedoe)" className="flex-1 bg-transparent border-0 text-sm focus:ring-0 placeholder-gray-400 dark:text-white outline-none" value={taggedUsers} onChange={e => setTaggedUsers(e.target.value)} />
              </div>
            </div>

            <input type="file" multiple accept="image/*,video/*" className="hidden" ref={fileInputRef} onChange={handleFileChange} />
          </form>
        </div>

        {/* Footer Actions */}
        <div className="px-6 py-4 bg-gray-50 dark:bg-gray-800/50 border-t border-gray-100 dark:border-gray-800 flex items-center justify-between rounded-b-3xl">
          <div className="flex items-center gap-2">
            <button type="button" onClick={() => fileInputRef.current?.click()} className="p-2.5 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-xl transition-colors tooltip" title="Attach Image">
              <ImageIcon className="w-5 h-5" />
            </button>
            <button type="button" onClick={() => fileInputRef.current?.click()} className="p-2.5 text-purple-600 hover:bg-purple-50 dark:hover:bg-purple-900/20 rounded-xl transition-colors tooltip" title="Attach Video">
              <Video className="w-5 h-5" />
            </button>
          </div>
          <Button type="submit" form="create-post-form" isLoading={isLoading} className="px-8 shadow-blue-500/25">
            Post Story
          </Button>
        </div>
      </div>
    </div>
  );
}
