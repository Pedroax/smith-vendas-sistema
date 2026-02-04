'use client';

import { WebSocketProvider } from './WebSocketProvider';
import { ToastProvider } from '@/contexts/ToastContext';

export function ClientProviders({ children }: { children: React.ReactNode }) {
  return (
    <ToastProvider>
      <WebSocketProvider>
        {children}
      </WebSocketProvider>
    </ToastProvider>
  );
}
