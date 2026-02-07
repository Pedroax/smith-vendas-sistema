/**
 * Interceptor global de fetch para forçar HTTPS em produção
 * Este código roda ANTES de qualquer fetch ser executado
 */

if (typeof window !== 'undefined') {
  const originalFetch = window.fetch;

  window.fetch = function(...args) {
    let url = args[0];

    // Se for string, verificar e corrigir
    if (typeof url === 'string') {
      // Se tiver smith-vendas-sistema-production e for HTTP, trocar para HTTPS
      if (url.includes('smith-vendas-sistema-production.up.railway.app') && url.startsWith('http://')) {
        url = url.replace('http://', 'https://');
        args[0] = url;
        console.log('🔒 Fetch interceptado e corrigido para HTTPS:', url);
      }
    }
    // Se for Request object
    else if (url instanceof Request) {
      const originalUrl = url.url;
      if (originalUrl.includes('smith-vendas-sistema-production.up.railway.app') && originalUrl.startsWith('http://')) {
        const newUrl = originalUrl.replace('http://', 'https://');
        url = new Request(newUrl, url);
        args[0] = url;
        console.log('🔒 Fetch interceptado e corrigido para HTTPS:', newUrl);
      }
    }

    return originalFetch.apply(this, args as any);
  };

  console.log('✅ Fetch interceptor instalado - todas requisições HTTP serão convertidas para HTTPS');
}

export {};
