'use client';

import NotificationBell from './NotificationBell';
import GlobalSearch from './GlobalSearch';

export default function TopBar() {
  return (
    <div className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-8 fixed top-0 right-0 left-64 z-40">
      {/* Global Search */}
      <GlobalSearch />

      {/* Right Side - Notifications */}
      <div className="flex items-center gap-4">
        <NotificationBell />

        {/* User Avatar (placeholder) */}
        <div className="flex items-center gap-3 pl-4 border-l border-gray-200">
          <div className="text-right">
            <p className="text-sm font-medium text-gray-900">Pedro Machado</p>
            <p className="text-xs text-gray-500">Admin</p>
          </div>
          <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center text-white font-bold">
            PM
          </div>
        </div>
      </div>
    </div>
  );
}
