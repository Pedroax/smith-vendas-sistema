'use client';

import { useEffect } from 'react';

/**
 * Componente que FORÇA a instalação do fetch interceptor
 * DEVE ser usado no layout principal
 */
export function ClientInit() {
  useEffect(() => {
    if (typeof window === 'undefined') return;

    // Verificar se já foi instalado
    if ((window as any).__FETCH_INTERCEPTOR_INSTALLED__) {
      console.log('⚠️ Interceptor já instalado');
      return;
    }

    const originalFetch = window.fetch;

    window.fetch = function(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
      let modifiedInput = input;
      let urlString = '';

      // Extrair URL
      if (typeof input === 'string') {
        urlString = input;
        console.log('🌐 [CLIENT-INIT] Interceptou fetch:', urlString);

        // Se tiver railway.app com HTTP, trocar para HTTPS
        if (input.includes('railway.app') && input.startsWith('http://')) {
          modifiedInput = input.replace('http://', 'https://');
          console.log('🔒 [CLIENT-INIT] ✅ CORRIGIDO HTTP→HTTPS:', modifiedInput);
        }
      } else if (input instanceof Request) {
        urlString = input.url;
        console.log('🌐 [CLIENT-INIT] Interceptou fetch (Request):', urlString);

        if (input.url.includes('railway.app') && input.url.startsWith('http://')) {
          const newUrl = input.url.replace('http://', 'https://');
          modifiedInput = new Request(newUrl, input);
          console.log('🔒 [CLIENT-INIT] ✅ CORRIGIDO HTTP→HTTPS:', newUrl);
        }
      } else if (input instanceof URL) {
        urlString = input.href;
        console.log('🌐 [CLIENT-INIT] Interceptou fetch (URL):', urlString);

        if (input.href.includes('railway.app') && input.href.startsWith('http://')) {
          const newUrl = input.href.replace('http://', 'https://');
          modifiedInput = new URL(newUrl);
          console.log('🔒 [CLIENT-INIT] ✅ CORRIGIDO HTTP→HTTPS:', newUrl);
        }
      }

      return originalFetch.call(this, modifiedInput, init);
    };

    (window as any).__FETCH_INTERCEPTOR_INSTALLED__ = true;
    console.log('✅ [CLIENT-INIT] Fetch interceptor instalado com sucesso!');
  }, []); // Executa UMA VEZ ao montar

  return null;
}
