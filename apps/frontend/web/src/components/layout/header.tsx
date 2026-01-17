'use client';

import * as DropdownMenu from '@radix-ui/react-dropdown-menu';
import { useAuth } from '@/hooks/use-auth';

export function Header() {
  const { user, logout } = useAuth();

  return (
    <header className="h-16 bg-white border-b border-gray-200 px-6 flex items-center justify-between">
      <div className="flex items-center">
        <h1 className="text-xl font-semibold">GeneralRAG</h1>
      </div>
      
      <DropdownMenu.Root>
        <DropdownMenu.Trigger className="flex items-center space-x-2 p-2 rounded hover:bg-gray-100">
          <div className="w-8 h-8 bg-gray-300 rounded-full"></div>
          <span>{user?.name || 'User'}</span>
        </DropdownMenu.Trigger>
        
        <DropdownMenu.Portal>
          <DropdownMenu.Content className="bg-white border border-gray-200 rounded-md shadow-lg p-1 min-w-[160px]">
            <DropdownMenu.Item className="px-3 py-2 text-sm hover:bg-gray-100 rounded cursor-pointer">
              Profile
            </DropdownMenu.Item>
            <DropdownMenu.Separator className="h-px bg-gray-200 my-1" />
            <DropdownMenu.Item 
              onClick={logout}
              className="px-3 py-2 text-sm hover:bg-gray-100 rounded cursor-pointer text-red-600"
            >
              Logout
            </DropdownMenu.Item>
          </DropdownMenu.Content>
        </DropdownMenu.Portal>
      </DropdownMenu.Root>
    </header>
  );
}