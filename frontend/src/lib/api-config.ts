/**
 * Configuração da API
 * HARDCODED para evitar problemas de Mixed Content
 */

// HARDCODED - SEM VARIÁVEL DE AMBIENTE
const API_URL_PRODUCTION = 'https://smith-vendas-sistema-production.up.railway.app';
const API_URL_DEV = 'http://localhost:8000';

// Detectar se está em localhost
const isLocalhost = typeof window !== 'undefined'
  ? window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  : false;

// Exportar URL - SEMPRE HTTPS exceto localhost
const computedUrl = isLocalhost ? API_URL_DEV : API_URL_PRODUCTION;

// GARANTIR que é HTTPS em produção
export const API_URL = computedUrl.startsWith('http://') && !isLocalhost
  ? computedUrl.replace('http://', 'https://')
  : computedUrl;

// Debug detalhado
if (typeof window !== 'undefined') {
  console.log('🔧 API_URL (FINAL):', API_URL);
  console.log('🔧 computedUrl:', computedUrl);
  console.log('🔧 API_URL_PRODUCTION:', API_URL_PRODUCTION);
  console.log('🌍 Hostname:', window.location.hostname);
  console.log('📍 isLocalhost:', isLocalhost);
  console.log('🔒 Starts with HTTPS?', API_URL.startsWith('https://'));
}
