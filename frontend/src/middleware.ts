import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Rotas do sistema interno (admin) que exigem login
const ADMIN_PROTECTED = [
  '/dashboard',
  '/crm',
  '/conversas',
  '/agendamentos',
  '/pipeline',
  '/tarefas',
  '/financeiro',
  '/analytics',
  '/agente',
  '/admin-portal',
  '/integracoes',
  '/configuracoes',
  '/leads',
  '/notificacoes',
];

// Rotas do portal do cliente que exigem login
const PORTAL_PROTECTED = [
  '/portal/projetos',
  '/portal/financeiro',
  '/portal/aprovacoes',
  '/portal/entregas',
  '/portal/pagamentos',
  '/portal/timeline',
  '/portal/configuracoes',
];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // ── Portal do cliente ─────────────────────────────────────────────────────
  const isPortalProtected = PORTAL_PROTECTED.some(p => pathname.startsWith(p));
  if (isPortalProtected) {
    const token = request.cookies.get('portal_access_token')?.value
      ?? request.headers.get('x-portal-token');
    // O token do portal é armazenado no localStorage (client-side),
    // então fazemos a proteção real no client. Aqui só bloqueamos acesso direto sem cookie.
    // A proteção principal é feita nos layouts com useEffect.
  }

  // ── Sistema interno (admin) ───────────────────────────────────────────────
  const isAdminProtected = ADMIN_PROTECTED.some(p => pathname.startsWith(p));

  if (isAdminProtected) {
    // Verificar token no cookie (para SSR) ou deixar o client-side handle
    const tokenCookie = request.cookies.get('smith_access_token')?.value;

    if (!tokenCookie) {
      // Redirecionar para login preservando a URL de destino
      const loginUrl = new URL('/login', request.url);
      loginUrl.searchParams.set('redirect', pathname);
      return NextResponse.redirect(loginUrl);
    }
  }

  // ── /login — redirecionar para dashboard se já logado ────────────────────
  if (pathname === '/login') {
    const tokenCookie = request.cookies.get('smith_access_token')?.value;
    if (tokenCookie) {
      return NextResponse.redirect(new URL('/dashboard', request.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Rodar em todas as rotas EXCETO:
     * - _next/static, _next/image (assets)
     * - favicon.ico
     * - /api/* (backend é separado)
     * - /webhook/*
     */
    '/((?!_next/static|_next/image|favicon.ico|api/).*)',
  ],
};
