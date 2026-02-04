'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import {
  LayoutDashboard, FolderKanban, Clock, FileCheck, MessageSquare,
  CreditCard, Settings, LogOut, User, ChevronRight
} from 'lucide-react';

interface Client {
  id: string;
  nome: string;
  email: string;
  empresa?: string;
  avatar_url?: string;
}

export default function PortalLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [client, setClient] = useState<Client | null>(null);

  // Páginas que não precisam de autenticação
  const publicPages = ['/portal/login', '/portal/register', '/portal/projeto/'];
  const isPublicPage = publicPages.some(page => pathname?.startsWith(page));

  useEffect(() => {
    if (!isPublicPage) {
      const token = localStorage.getItem('portal_token');
      const clientData = localStorage.getItem('portal_client');

      if (!token || !clientData) {
        router.push('/portal/login');
        return;
      }

      try {
        setClient(JSON.parse(clientData));
      } catch (e) {
        router.push('/portal/login');
      }
    }
  }, [pathname, router, isPublicPage]);

  const handleLogout = () => {
    localStorage.removeItem('portal_token');
    localStorage.removeItem('portal_client');
    router.push('/portal/login');
  };

  // Se for página pública, renderiza sem layout
  if (isPublicPage) {
    return <>{children}</>;
  }

  const menuItems = [
    { href: '/portal', icon: LayoutDashboard, label: 'Dashboard', exact: true },
    { href: '/portal/projetos', icon: FolderKanban, label: 'Meus Projetos' },
    { href: '/portal/timeline', icon: Clock, label: 'Timeline' },
    { href: '/portal/entregas', icon: FileCheck, label: 'Entregas' },
    { href: '/portal/aprovacoes', icon: MessageSquare, label: 'Aprovações' },
    { href: '/portal/pagamentos', icon: CreditCard, label: 'Pagamentos' },
    { href: '/portal/configuracoes', icon: Settings, label: 'Configurações' },
  ];

  const isActive = (href: string, exact?: boolean) => {
    if (exact) {
      return pathname === href;
    }
    return pathname?.startsWith(href);
  };

  return (
    <>
      {/* Sidebar - SEMPRE VISÍVEL como no Smith 2.0 */}
      <aside className="w-72 bg-white border-r border-gray-200 flex flex-col h-screen fixed left-0 top-0 z-50">
        {/* Logo */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-fuchsia-500 rounded-xl flex items-center justify-center shadow-lg shadow-purple-500/20">
              <span className="text-white font-bold text-lg">A</span>
            </div>
            <div>
              <h1 className="font-bold text-gray-900 text-lg">Ax ai</h1>
              <p className="text-xs text-gray-500">Portal do Cliente</p>
            </div>
          </div>
        </div>

        {/* User Info */}
        {client && (
          <div className="p-4 mx-4 mt-4 bg-gray-50 rounded-xl">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-gray-600 to-gray-800 rounded-full flex items-center justify-center">
                {client.avatar_url ? (
                  <img
                    src={client.avatar_url}
                    alt={client.nome}
                    className="w-10 h-10 rounded-full object-cover"
                  />
                ) : (
                  <User className="w-5 h-5 text-white" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-gray-900 truncate">{client.nome}</p>
                <p className="text-xs text-gray-500 truncate">{client.empresa || client.email}</p>
              </div>
            </div>
          </div>
        )}

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.href, item.exact);

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`
                  flex items-center gap-3 px-4 py-3 rounded-xl transition-all
                  ${active
                    ? 'bg-purple-50 text-purple-600 font-medium'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  }
                `}
              >
                <Icon className={`w-5 h-5 ${active ? 'text-purple-500' : ''}`} />
                <span>{item.label}</span>
                {active && <ChevronRight className="w-4 h-4 ml-auto" />}
              </Link>
            );
          })}
        </nav>

        {/* Logout */}
        <div className="p-4 border-t border-gray-200">
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 px-4 py-3 w-full rounded-xl text-gray-600 hover:bg-red-50 hover:text-red-600 transition-all"
          >
            <LogOut className="w-5 h-5" />
            <span>Sair</span>
          </button>
        </div>
      </aside>

      {/* Main Content - margem fixa à esquerda */}
      <main className="ml-72 min-h-screen">
        {children}
      </main>
    </>
  );
}
