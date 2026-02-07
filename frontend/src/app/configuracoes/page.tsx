'use client';

import { useState } from 'react';
import { Settings, Bell, Lock, User, Shield, Save, CheckCircle2, Loader2 } from 'lucide-react';
import { useToast } from '@/contexts/ToastContext';

import { API_URL } from '@/lib/api-config';

const tabs = [
  { id: 'perfil', label: 'Perfil', icon: User },
  { id: 'notificacoes', label: 'Notificações', icon: Bell },
  { id: 'seguranca', label: 'Segurança', icon: Lock },
  { id: 'sistema', label: 'Sistema', icon: Shield },
];

export default function ConfiguracoesPage() {
  const { showToast } = useToast();
  const [activeTab, setActiveTab] = useState('perfil');
  const [saving, setSaving] = useState(false);

  const [perfil, setPerfil] = useState({
    nome: 'Pedro Machado',
    email: 'pedro@automatex.com.br',
    empresa: 'AutomateX',
    fone: '',
  });

  const [notificacoes, setNotificacoes] = useState({
    whatsapp: true,
    email: false,
    novosLeads: true,
    atualizacoes: true,
    agendamentos: true,
  });

  const [senha, setSenha] = useState({
    atual: '',
    nova: '',
    confirmar: '',
  });

  const handleSalvar = async () => {
    setSaving(true);
    try {
      // Simula salvamento
      await new Promise((resolve) => setTimeout(resolve, 800));
      showToast('Configurações salvas com sucesso!', 'success');
    } catch {
      showToast('Erro ao salvar configurações', 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleSenha = async () => {
    if (!senha.atual || !senha.nova || !senha.confirmar) {
      showToast('Preencha todos os campos', 'error');
      return;
    }
    if (senha.nova !== senha.confirmar) {
      showToast('As senhas não coincidem', 'error');
      return;
    }
    setSaving(true);
    try {
      await new Promise((resolve) => setTimeout(resolve, 800));
      showToast('Senha alterada com sucesso!', 'success');
      setSenha({ atual: '', nova: '', confirmar: '' });
    } catch {
      showToast('Erro ao alterar senha', 'error');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex-1 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="px-8 py-6">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-purple-100 rounded-xl">
              <Settings className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Configurações</h1>
              <p className="text-gray-500 mt-0.5">Personalize o sistema Smith 2.0</p>
            </div>
          </div>
        </div>
      </div>

      <div className="flex">
        {/* Sidebar Tabs */}
        <div className="w-64 border-r border-gray-200 bg-white min-h-[calc(100vh-120px)]">
          <nav className="p-4 space-y-1">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all text-left
                    ${isActive
                      ? 'bg-purple-50 text-purple-700'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                    }
                  `}
                >
                  <Icon className={`w-5 h-5 ${isActive ? 'text-purple-600' : ''}`} />
                  <span className="font-medium">{tab.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Content */}
        <div className="flex-1 p-8">
          {/* Perfil */}
          {activeTab === 'perfil' && (
            <div className="max-w-2xl space-y-6">
              <div>
                <h2 className="text-xl font-bold text-gray-900 mb-1">Dados do Perfil</h2>
                <p className="text-gray-500 text-sm">Atualize suas informações pessoais</p>
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-5">
                {/* Avatar */}
                <div className="flex items-center gap-4">
                  <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                    <span className="text-xl font-bold text-white">PM</span>
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900">{perfil.nome}</p>
                    <p className="text-sm text-gray-500">{perfil.empresa}</p>
                  </div>
                </div>

                <hr className="border-gray-100" />

                <div className="grid grid-cols-2 gap-5">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">Nome Completo</label>
                    <input
                      type="text"
                      value={perfil.nome}
                      onChange={(e) => setPerfil((p) => ({ ...p, nome: e.target.value }))}
                      className="w-full px-4 py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">Email</label>
                    <input
                      type="email"
                      value={perfil.email}
                      onChange={(e) => setPerfil((p) => ({ ...p, email: e.target.value }))}
                      className="w-full px-4 py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">Empresa</label>
                    <input
                      type="text"
                      value={perfil.empresa}
                      onChange={(e) => setPerfil((p) => ({ ...p, empresa: e.target.value }))}
                      className="w-full px-4 py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">Telefone</label>
                    <input
                      type="tel"
                      value={perfil.fone}
                      onChange={(e) => setPerfil((p) => ({ ...p, fone: e.target.value }))}
                      placeholder="(11) 99999-9999"
                      className="w-full px-4 py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                    />
                  </div>
                </div>

                <div className="flex justify-end pt-2">
                  <button
                    onClick={handleSalvar}
                    disabled={saving}
                    className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-xl hover:shadow-lg transition-all disabled:opacity-50"
                  >
                    {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                    {saving ? 'Salvando...' : 'Salvar'}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Notificações */}
          {activeTab === 'notificacoes' && (
            <div className="max-w-2xl space-y-6">
              <div>
                <h2 className="text-xl font-bold text-gray-900 mb-1">Notificações</h2>
                <p className="text-gray-500 text-sm">Controle como e quando você recebe notificações</p>
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-6">
                <div>
                  <h3 className="font-semibold text-gray-800 mb-4">Canais de Notificação</h3>
                  <div className="space-y-4">
                    {[
                      { key: 'whatsapp', label: 'WhatsApp', desc: 'Receba alertas via WhatsApp' },
                      { key: 'email', label: 'Email', desc: 'Receba alertas via email' },
                    ].map((item) => (
                      <div key={item.key} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                        <div>
                          <p className="font-medium text-gray-800">{item.label}</p>
                          <p className="text-sm text-gray-500">{item.desc}</p>
                        </div>
                        <button
                          onClick={() => setNotificacoes((n) => ({ ...n, [item.key]: !n[item.key as keyof typeof n] }))}
                          className={`relative w-11 h-6 rounded-full transition-colors ${
                            notificacoes[item.key as keyof typeof notificacoes] ? 'bg-purple-500' : 'bg-gray-300'
                          }`}
                        >
                          <span
                            className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform ${
                              notificacoes[item.key as keyof typeof notificacoes] ? 'translate-x-5' : ''
                            }`}
                          />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>

                <hr className="border-gray-100" />

                <div>
                  <h3 className="font-semibold text-gray-800 mb-4">Tipos de Alerta</h3>
                  <div className="space-y-4">
                    {[
                      { key: 'novosLeads', label: 'Novos Leads', desc: 'Quando um novo lead é criado' },
                      { key: 'atualizacoes', label: 'Atualizações', desc: 'Mudanças no status dos leads' },
                      { key: 'agendamentos', label: 'Agendamentos', desc: 'Lembretes de reuniões' },
                    ].map((item) => (
                      <div key={item.key} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                        <div>
                          <p className="font-medium text-gray-800">{item.label}</p>
                          <p className="text-sm text-gray-500">{item.desc}</p>
                        </div>
                        <button
                          onClick={() => setNotificacoes((n) => ({ ...n, [item.key]: !n[item.key as keyof typeof n] }))}
                          className={`relative w-11 h-6 rounded-full transition-colors ${
                            notificacoes[item.key as keyof typeof notificacoes] ? 'bg-purple-500' : 'bg-gray-300'
                          }`}
                        >
                          <span
                            className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform ${
                              notificacoes[item.key as keyof typeof notificacoes] ? 'translate-x-5' : ''
                            }`}
                          />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="flex justify-end pt-2">
                  <button
                    onClick={handleSalvar}
                    disabled={saving}
                    className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-xl hover:shadow-lg transition-all disabled:opacity-50"
                  >
                    {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                    {saving ? 'Salvando...' : 'Salvar'}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Segurança */}
          {activeTab === 'seguranca' && (
            <div className="max-w-2xl space-y-6">
              <div>
                <h2 className="text-xl font-bold text-gray-900 mb-1">Segurança</h2>
                <p className="text-gray-500 text-sm">Gerenciar senha e configurações de segurança</p>
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-5">
                <h3 className="font-semibold text-gray-800">Alterar Senha</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">Senha Atual</label>
                    <input
                      type="password"
                      value={senha.atual}
                      onChange={(e) => setSenha((s) => ({ ...s, atual: e.target.value }))}
                      placeholder="••••••••"
                      className="w-full px-4 py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">Nova Senha</label>
                    <input
                      type="password"
                      value={senha.nova}
                      onChange={(e) => setSenha((s) => ({ ...s, nova: e.target.value }))}
                      placeholder="••••••••"
                      className="w-full px-4 py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">Confirmar Nova Senha</label>
                    <input
                      type="password"
                      value={senha.confirmar}
                      onChange={(e) => setSenha((s) => ({ ...s, confirmar: e.target.value }))}
                      placeholder="••••••••"
                      className="w-full px-4 py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                    />
                  </div>
                </div>
                <div className="flex justify-end pt-2">
                  <button
                    onClick={handleSenha}
                    disabled={saving}
                    className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-xl hover:shadow-lg transition-all disabled:opacity-50"
                  >
                    {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Lock className="w-4 h-4" />}
                    {saving ? 'Salvando...' : 'Alterar Senha'}
                  </button>
                </div>
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold text-gray-800">Sessões Ativas</h3>
                    <p className="text-sm text-gray-500">Visualize e gerencie suas sessões</p>
                  </div>
                </div>
                <div className="mt-4 p-4 bg-gray-50 rounded-lg flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-800">Navegador Atual</p>
                    <p className="text-xs text-gray-500">Esta sessão</p>
                  </div>
                  <span className="flex items-center gap-1.5 text-xs font-medium text-green-700 bg-green-50 px-2 py-1 rounded-full">
                    <CheckCircle2 className="w-3 h-3" /> Ativa
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Sistema */}
          {activeTab === 'sistema' && (
            <div className="max-w-2xl space-y-6">
              <div>
                <h2 className="text-xl font-bold text-gray-900 mb-1">Informações do Sistema</h2>
                <p className="text-gray-500 text-sm">Detalhes técnicos do Smith 2.0</p>
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <div className="space-y-4">
                  {[
                    { label: 'Versão do Sistema', value: 'Smith 2.0.0' },
                    { label: 'Framework Backend', value: 'FastAPI (Python)' },
                    { label: 'Framework Frontend', value: 'Next.js 16' },
                    { label: 'Banco de Dados', value: 'Supabase (PostgreSQL)' },
                    { label: 'IA Utilizada', value: 'OpenAI GPT-4o' },
                    { label: 'WhatsApp', value: 'Evolution API' },
                  ].map((item) => (
                    <div key={item.label} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                      <p className="text-sm text-gray-600">{item.label}</p>
                      <p className="text-sm font-semibold text-gray-900">{item.value}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <h3 className="font-semibold text-gray-800 mb-4">Ambiente</h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-600">API Backend</p>
                    <code className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded font-mono">
                      {API_URL}
                    </code>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-600">Ambiente</p>
                    <span className="text-xs font-semibold text-green-700 bg-green-50 px-2 py-1 rounded">Production</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
