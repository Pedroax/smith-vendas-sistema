'use client';

import { Home, Users, MessageSquare, Calendar, BarChart3, Settings, Bot, Zap, Kanban, Globe, Package, CheckSquare, LogOut, DollarSign } from 'lucide-react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { adminAuth, type AdminUser } from '@/lib/auth';

const allMenuItems = [
  { icon: Home, label: 'Dashboard', href: '/dashboard', badge: null, roles: ['admin', 'marketing'] },
  { icon: Users, label: 'CRM', href: '/crm', badge: '5', roles: ['admin', 'marketing'] },
  { icon: MessageSquare, label: 'Conversas', href: '/conversas', badge: '3', roles: ['admin', 'marketing'] },
  { icon: Calendar, label: 'Agendamentos', href: '/agendamentos', badge: null, roles: ['admin', 'marketing'] },
  { icon: Kanban, label: 'Pipeline', href: '/pipeline', badge: null, roles: ['admin', 'marketing'] },
  { icon: CheckSquare, label: 'Tarefas', href: '/tarefas', badge: null, roles: ['admin', 'marketing'] },
  { icon: DollarSign, label: 'Financeiro', href: '/financeiro', badge: null, roles: ['admin'] },
  { icon: BarChart3, label: 'Analytics', href: '/analytics/dashboard', badge: null, roles: ['admin', 'marketing'] },
  { icon: Bot, label: 'Agente IA', href: '/agente', badge: '🔴', roles: ['admin'] },
  { icon: Globe, label: 'Portal', href: '/admin-portal', badge: null, roles: ['admin'] },
  { icon: Package, label: 'Templates', href: '/admin-portal/templates', badge: null, roles: ['admin'] },
];

const allBottomItems = [
  { icon: Zap, label: 'Integrações', href: '/integracoes', roles: ['admin'] },
  { icon: Settings, label: 'Configurações', href: '/configuracoes', roles: ['admin'] },
];

function getInitials(nome: string): string {
  return nome.split(' ').slice(0, 2).map(n => n[0]).join('').toUpperCase();
}

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<AdminUser | null>(null);

  useEffect(() => {
    setUser(adminAuth.getUser());
  }, []);

  const role = user?.role ?? 'admin';
  const menuItems = allMenuItems.filter(item => item.roles.includes(role));
  const bottomItems = allBottomItems.filter(item => item.roles.includes(role));

  const handleLogout = () => {
    adminAuth.clearTokens();
    router.replace('/login');
  };

  const isActive = (href: string) => {
    if (href === '/') return pathname === '/';
    return pathname?.startsWith(href);
  };

  return (
    <aside className="w-64 bg-gradient-to-b from-gray-900 to-gray-800 text-white flex flex-col h-screen fixed left-0 top-0 border-r border-gray-700/50">
      {/* Logo */}
      <div className="p-6 border-b border-gray-700/50">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl flex items-center justify-center">
              <Bot className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-lg">Smith 2.0</h1>
              <p className="text-xs text-gray-400">AutomateX</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="p-2 rounded-lg text-gray-400 hover:bg-red-500/10 hover:text-red-400 transition-all"
            title="Sair"
          >
            <LogOut className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Menu Principal */}
      <nav className="flex-1 p-4 space-y-1 overflow-y-auto [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const active = isActive(item.href);

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`
                flex items-center gap-3 px-4 py-3 rounded-lg transition-all
                ${active
                  ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-lg shadow-purple-500/50'
                  : 'text-gray-300 hover:bg-gray-700/50 hover:text-white'
                }
              `}
            >
              <Icon className="w-5 h-5" />
              <span className="flex-1 font-medium">{item.label}</span>
              {item.badge && (
                <span className={`
                  text-xs font-bold px-2 py-0.5 rounded-full
                  ${active ? 'bg-white/20' : 'bg-purple-500'}
                `}>
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Menu Inferior */}
      {bottomItems.length > 0 && (
        <div className="p-4 space-y-1 border-t border-gray-700/50">
          {bottomItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`
                  flex items-center gap-3 px-4 py-3 rounded-lg transition-all
                  ${active
                    ? 'bg-gray-700 text-white'
                    : 'text-gray-400 hover:bg-gray-700/50 hover:text-white'
                  }
                `}
              >
                <Icon className="w-5 h-5" />
                <span className="font-medium">{item.label}</span>
              </Link>
            );
          })}
        </div>
      )}

      {/* User Profile + Logout */}
      <div className="p-4 border-t border-gray-700/50 space-y-2">
        <div className="flex items-center gap-3 p-3 rounded-lg bg-gray-700/30">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-green-400 to-blue-500 flex items-center justify-center">
            <span className="text-sm font-bold">{user ? getInitials(user.nome) : '?'}</span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{user?.nome ?? '...'}</p>
            <p className="text-xs text-gray-400 capitalize">{user?.role ?? ''}</p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-gray-400 hover:bg-red-500/10 hover:text-red-400 transition-all"
        >
          <LogOut className="w-4 h-4" />
          <span className="text-sm font-medium">Sair</span>
        </button>
      </div>
    </aside>
  );
}
