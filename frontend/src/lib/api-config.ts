/**
 * Configuração centralizada da API
 * Garante que sempre use HTTPS em produção
 */
export const getApiUrl = (): string => {
  // Se estiver em produção (vercel.app), FORÇAR HTTPS sempre
  if (typeof window !== 'undefined' && window.location.hostname.includes('vercel.app')) {
    return 'https://smith-vendas-sistema-production.up.railway.app';
  }

  const url = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  // Se não for localhost e estiver usando HTTP, forçar HTTPS
  if (!url.includes('localhost') && !url.includes('127.0.0.1') && url.startsWith('http://')) {
    return url.replace('http://', 'https://');
  }

  return url;
};

export const API_URL = getApiUrl();
