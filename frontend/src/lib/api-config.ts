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
export const API_URL = isLocalhost ? API_URL_DEV : API_URL_PRODUCTION;

// Debug
if (typeof window !== 'undefined') {
  console.log('🔧 API_URL:', API_URL);
  console.log('🌍 Hostname:', window.location.hostname);
  console.log('📍 isLocalhost:', isLocalhost);
}
