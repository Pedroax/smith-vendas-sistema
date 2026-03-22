'use client';

import { useEffect } from 'react';
import { adminAuth } from '@/lib/auth';

/**
 * Inicialização client-side:
 * - Sincroniza token do localStorage para cookie (para o middleware Edge)
 * - Instala interceptor HTTP→HTTPS para Railway (uma única vez)
 */
export function ClientInit() {
  useEffect(() => {
    // 1. Sync token localStorage → cookie (para o middleware Edge conseguir ler)
    const token = adminAuth.getAccessToken();
    if (token) {
      document.cookie = `smith_access_token=${token}; path=/; max-age=86400; SameSite=Lax`;
    }

    // 2. Interceptor HTTP→HTTPS para Railway (só instala uma vez)
    if ((window as any).__FETCH_INTERCEPTOR_INSTALLED__) return;

    const originalFetch = window.fetch;
    window.fetch = function(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
      if (typeof input === 'string' && input.includes('railway.app') && input.startsWith('http://')) {
        input = input.replace('http://', 'https://');
      } else if (input instanceof Request && input.url.includes('railway.app') && input.url.startsWith('http://')) {
        input = new Request(input.url.replace('http://', 'https://'), input);
      } else if (input instanceof URL && input.href.includes('railway.app') && input.href.startsWith('http://')) {
        input = new URL(input.href.replace('http://', 'https://'));
      }
      return originalFetch.call(this, input, init);
    };
    (window as any).__FETCH_INTERCEPTOR_INSTALLED__ = true;
  }, []);

  return null;
}
