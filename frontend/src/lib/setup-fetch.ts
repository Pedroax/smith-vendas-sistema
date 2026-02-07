/**
 * Setup de fetch que DEVE rodar ANTES de qualquer outro código
 * Import este arquivo no TOPO do layout.tsx
 */

if (typeof window !== 'undefined') {
  const originalFetch = window.fetch;

  window.fetch = function(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
    let modifiedInput = input;
    let urlString = '';

    // Extrair URL
    if (typeof input === 'string') {
      urlString = input;
    } else if (input instanceof Request) {
      urlString = input.url;
    } else if (input instanceof URL) {
      urlString = input.href;
    }

    console.log('🚀 [FETCH-SETUP] Interceptando:', urlString);

    // Se for string e tiver railway.app com HTTP
    if (typeof input === 'string' && input.includes('railway.app') && input.startsWith('http://')) {
      modifiedInput = input.replace('http://', 'https://');
      console.log('🔒 [FETCH-SETUP] ✅ CORRIGIDO:', modifiedInput);
    }
    // Se for Request object
    else if (input instanceof Request && input.url.includes('railway.app') && input.url.startsWith('http://')) {
      const newUrl = input.url.replace('http://', 'https://');
      modifiedInput = new Request(newUrl, input);
      console.log('🔒 [FETCH-SETUP] ✅ CORRIGIDO:', newUrl);
    }
    // Se for URL object
    else if (input instanceof URL && input.href.includes('railway.app') && input.href.startsWith('http://')) {
      const newUrl = input.href.replace('http://', 'https://');
      modifiedInput = new URL(newUrl);
      console.log('🔒 [FETCH-SETUP] ✅ CORRIGIDO:', newUrl);
    }

    return originalFetch.call(this, modifiedInput, init);
  };

  console.log('✅ [FETCH-SETUP] Interceptor instalado globalmente');
}

export {};
