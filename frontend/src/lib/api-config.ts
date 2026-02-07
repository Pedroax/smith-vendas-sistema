/**
 * Configuração da API
 * HARDCODED HTTPS - funciona no CLIENT e SERVER (SSR)
 */

// HARDCODED - SEMPRE HTTPS em produção
const API_URL_PRODUCTION = 'https://smith-vendas-sistema-production.up.railway.app';
const API_URL_DEV = 'http://localhost:8000';

// Detectar ambiente
// SERVER (SSR): sem window → assume produção → HTTPS
// CLIENT: verifica hostname
const isLocalhost = typeof window !== 'undefined'
  ? window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  : false; // No servidor Next.js SSR, sempre usa produção (HTTPS)

// Exportar URL - SEMPRE HTTPS exceto localhost
export const API_URL = isLocalhost ? API_URL_DEV : API_URL_PRODUCTION;

// Debug
if (typeof window !== 'undefined') {
  console.log('🔧 [CLIENT] API_URL:', API_URL);
  console.log('🌍 Hostname:', window.location.hostname);
} else {
  console.log('🖥️  [SERVER SSR] API_URL:', API_URL);
}
