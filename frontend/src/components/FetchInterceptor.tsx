'use client';

import { useEffect } from 'react';

/**
 * Componente que instala o interceptor de fetch
 * Deve ser incluído no layout raiz
 */
export function FetchInterceptor() {
  useEffect(() => {
    const originalFetch = window.fetch;

    window.fetch = function(...args: any[]) {
      let url = args[0];

      // Se for string, verificar e corrigir
      if (typeof url === 'string') {
        // Se tiver railway.app e for HTTP, trocar para HTTPS
        if (url.includes('railway.app') && url.startsWith('http://')) {
          url = url.replace('http://', 'https://');
          args[0] = url;
          console.log('🔒 [INTERCEPTOR] Corrigido HTTP → HTTPS:', url);
        }
      }
      // Se for Request object
      else if (url instanceof Request) {
        const originalUrl = url.url;
        if (originalUrl.includes('railway.app') && originalUrl.startsWith('http://')) {
          const newUrl = originalUrl.replace('http://', 'https://');
          url = new Request(newUrl, url);
          args[0] = url;
          console.log('🔒 [INTERCEPTOR] Corrigido HTTP → HTTPS:', newUrl);
        }
      }

      return originalFetch.apply(this, args);
    };

    console.log('✅ Fetch interceptor instalado globalmente');

    // Cleanup
    return () => {
      window.fetch = originalFetch;
    };
  }, []);

  return null; // Componente invisível
}
