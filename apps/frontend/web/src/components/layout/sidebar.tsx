'use client';

import { useUIStore } from '@/stores/ui-store';
import { useAuth } from '@/hooks/use-auth';

export function Sidebar() {
  const { sidebarOpen, setSidebarOpen } = useUIStore();
  const { user } = useAuth();

  if (!sidebarOpen) {
    return (
      <button 
        onClick={() => setSidebarOpen(true)}
        className="fixed top-4 left-4 z-50 p-2 bg-gray-800 text-white rounded"
      >
        ☰
      </button>
    );
  }

  return (
    <div className="fixed left-0 top-0 h-full w-64 bg-gray-900 text-white p-4 z-40">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-lg font-semibold">Chats</h2>
        <button onClick={() => setSidebarOpen(false)}>✕</button>
      </div>
      
      <button className="w-full mb-4 p-2 bg-blue-600 rounded hover:bg-blue-700">
        New Chat
      </button>
      
      <div className="mb-6">
        <h3 className="text-sm text-gray-400 mb-2">History</h3>
        <div className="space-y-1">
          {/* Chat history items would go here */}
        </div>
      </div>
      
      {user?.role === 'admin' && (
        <a href="/admin" className="block p-2 text-gray-300 hover:text-white">
          Admin
        </a>
      )}
    </div>
  );
}