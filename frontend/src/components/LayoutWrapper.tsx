'use client';

import { useEffect, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { Sidebar } from './Sidebar';
import TopBar from './TopBar';
import { InstallPWA } from './InstallPWA';
import { adminAuth, refreshAdminToken } from '@/lib/auth';

// Rotas que não precisam de autenticação
const PUBLIC_ROUTES = ['/login', '/portal'];

function isPublicRoute(pathname: string | null): boolean {
  if (!pathname) return false;
  return PUBLIC_ROUTES.some((route) => pathname.startsWith(route));
}

export function LayoutWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    async function checkAuth() {
      if (isPublicRoute(pathname)) {
        setChecking(false);
        return;
      }

      if (adminAuth.isAuthenticated()) {
        setChecking(false);
        return;
      }

      // Tenta renovar via refresh token
      const newToken = await refreshAdminToken();
      if (newToken) {
        setChecking(false);
        return;
      }

      // Sem autenticação válida
      router.replace('/login');
    }

    checkAuth();
  }, [pathname, router]);

  // Evita flash de conteúdo enquanto verifica auth
  if (checking && !isPublicRoute(pathname)) {
    return null;
  }

  // Portal e login: sem layout interno
  if (isPublicRoute(pathname)) {
    return (
      <>
        {children}
        <InstallPWA />
      </>
    );
  }

  // Páginas do Smith 2.0
  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />
      <div className="flex-1 ml-64">
        <TopBar />
        <main className="pt-16">
          {children}
        </main>
      </div>
      <InstallPWA />
    </div>
  );
}
