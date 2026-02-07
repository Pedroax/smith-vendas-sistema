/**
 * Configuração centralizada da API
 * SEMPRE usa HTTPS em produção (vercel.app)
 */

// Detectar se está em produção baseado na URL da página
const isProduction = () => {
  if (typeof window !== 'undefined') {
    return window.location.hostname.includes('vercel.app');
  }
  // No servidor, usar a variável de ambiente VERCEL
  return process.env.VERCEL === '1' || process.env.NEXT_PUBLIC_VERCEL_ENV === 'production';
};

export const getApiUrl = (): string => {
  // PRODUÇÃO: sempre usar HTTPS hardcoded
  if (isProduction()) {
    return 'https://smith-vendas-sistema-production.up.railway.app';
  }

  // DESENVOLVIMENTO: usar variável ou localhost
  const url = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  // Segurança extra: garantir HTTPS se não for localhost
  if (!url.includes('localhost') && !url.includes('127.0.0.1') && url.startsWith('http://')) {
    return url.replace('http://', 'https://');
  }

  return url;
};

// Exportar a URL como constante
export const API_URL = getApiUrl();

// Debug: mostrar URL no console (apenas no browser)
if (typeof window !== 'undefined') {
  console.log('🔧 API_URL configurado:', API_URL);
  console.log('🌍 Hostname:', window.location.hostname);
  console.log('🔒 isProduction:', isProduction());
}
