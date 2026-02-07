/**
 * Configuração da API
 * HARDCODED HTTPS com interceptor integrado
 */

// Declaração de tipo para a flag do interceptor
declare global {
  interface Window {
    __FETCH_INTERCEPTOR_INSTALLED__?: boolean;
  }
}

// INTERCEPTOR DE FETCH - RODA ASSIM QUE O ARQUIVO É IMPORTADO
if (typeof window !== 'undefined' && !window.__FETCH_INTERCEPTOR_INSTALLED__) {
  const originalFetch = window.fetch;

  window.fetch = function(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
    let modifiedInput = input;
    let urlString = '';

    // Extrair URL
    if (typeof input === 'string') {
      urlString = input;
      // Se tiver railway.app com HTTP, trocar para HTTPS
      if (input.includes('railway.app') && input.startsWith('http://')) {
        modifiedInput = input.replace('http://', 'https://');
        console.log('🔒 [API-CONFIG] CORRIGIDO HTTP→HTTPS:', modifiedInput);
      }
    } else if (input instanceof Request) {
      urlString = input.url;
      if (input.url.includes('railway.app') && input.url.startsWith('http://')) {
        const newUrl = input.url.replace('http://', 'https://');
        modifiedInput = new Request(newUrl, input);
        console.log('🔒 [API-CONFIG] CORRIGIDO HTTP→HTTPS:', newUrl);
      }
    } else if (input instanceof URL) {
      urlString = input.href;
      if (input.href.includes('railway.app') && input.href.startsWith('http://')) {
        const newUrl = input.href.replace('http://', 'https://');
        modifiedInput = new URL(newUrl);
        console.log('🔒 [API-CONFIG] CORRIGIDO HTTP→HTTPS:', newUrl);
      }
    }

    return originalFetch.call(this, modifiedInput, init);
  };

  window.__FETCH_INTERCEPTOR_INSTALLED__ = true;
  console.log('✅ [API-CONFIG] Fetch interceptor instalado');
}

// HARDCODED - SEMPRE HTTPS em produção
const API_URL_PRODUCTION = 'https://smith-vendas-sistema-production.up.railway.app';
const API_URL_DEV = 'http://localhost:8000';

// Detectar ambiente
const isLocalhost = typeof window !== 'undefined'
  ? window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  : false;

// Exportar URL - SEMPRE HTTPS exceto localhost
export const API_URL = isLocalhost ? API_URL_DEV : API_URL_PRODUCTION;

// Debug
if (typeof window !== 'undefined') {
  console.log('🔧 [CLIENT] API_URL:', API_URL);
  console.log('🌍 Hostname:', window.location.hostname);
} else {
  console.log('🖥️  [SERVER SSR] API_URL:', API_URL);
}
