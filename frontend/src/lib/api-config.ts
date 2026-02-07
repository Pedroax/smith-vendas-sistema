/**
 * Configuração centralizada da API
 * Garante que sempre use HTTPS em produção
 */
export const getApiUrl = (): string => {
  const url = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  // Se não for localhost e estiver usando HTTP, forçar HTTPS
  if (!url.includes('localhost') && !url.includes('127.0.0.1') && url.startsWith('http://')) {
    return url.replace('http://', 'https://');
  }

  return url;
};

export const API_URL = getApiUrl();
