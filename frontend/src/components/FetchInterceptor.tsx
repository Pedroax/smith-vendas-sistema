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
      let urlString = '';

      // Se for string
      if (typeof input === 'string') {
        urlString = input;
        console.log('🌐 [INTERCEPTOR] Fetch detectado (string):', urlString);

        // Se tiver railway.app e for HTTP, trocar para HTTPS
        if (urlString.includes('railway.app') && urlString.startsWith('http://')) {
          modifiedInput = urlString.replace('http://', 'https://');
          console.log('🔒 [INTERCEPTOR] ✅ CORRIGIDO HTTP → HTTPS:', modifiedInput);
        } else if (urlString.includes('railway.app')) {
          console.log('✅ [INTERCEPTOR] Já está HTTPS:', urlString);
        }
      }
      // Se for Request object
      else if (input instanceof Request) {
        urlString = input.url;
        console.log('🌐 [INTERCEPTOR] Fetch detectado (Request):', urlString);

        if (urlString.includes('railway.app') && urlString.startsWith('http://')) {
          const newUrl = urlString.replace('http://', 'https://');
          modifiedInput = new Request(newUrl, input);
          console.log('🔒 [INTERCEPTOR] ✅ CORRIGIDO HTTP → HTTPS:', newUrl);
        } else if (urlString.includes('railway.app')) {
          console.log('✅ [INTERCEPTOR] Já está HTTPS:', urlString);
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
