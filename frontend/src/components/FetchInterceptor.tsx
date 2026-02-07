'use client';

import { useEffect } from 'react';

/**
 * Componente que instala o interceptor de fetch
 * Deve ser incluído no layout raiz
 */
export function FetchInterceptor() {
  useEffect(() => {
    const originalFetch = window.fetch;

    window.fetch = function(input: RequestInfo | URL, init?: RequestInit) {
      let modifiedInput = input;

      // Se for string, verificar e corrigir
      if (typeof input === 'string') {
        // Se tiver railway.app e for HTTP, trocar para HTTPS
        if (input.includes('railway.app') && input.startsWith('http://')) {
          modifiedInput = input.replace('http://', 'https://');
          console.log('🔒 [INTERCEPTOR] Corrigido HTTP → HTTPS:', modifiedInput);
        }
      }
      // Se for Request object
      else if (input instanceof Request) {
        const originalUrl = input.url;
        if (originalUrl.includes('railway.app') && originalUrl.startsWith('http://')) {
          const newUrl = originalUrl.replace('http://', 'https://');
          modifiedInput = new Request(newUrl, input);
          console.log('🔒 [INTERCEPTOR] Corrigido HTTP → HTTPS:', newUrl);
        }
      }

      return originalFetch.call(this, modifiedInput, init);
    };

    console.log('✅ Fetch interceptor instalado globalmente');

    // Cleanup
    return () => {
      window.fetch = originalFetch;
    };
  }, []);

  return null; // Componente invisível
}
