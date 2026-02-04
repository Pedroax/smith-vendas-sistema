'use client';

import { useState, useEffect } from 'react';
import { Zap, MessageCircle, Calendar, CheckCircle2, AlertCircle, XCircle, ExternalLink, RefreshCw, Loader2 } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface WebhookStatus {
  webhook: string;
  whatsapp_connection: string;
  total_leads: number;
  timestamp: string;
}

export default function IntegracosPage() {
  const [webhookStatus, setWebhookStatus] = useState<WebhookStatus | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchStatus = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/webhook/whatsapp/status`);
      if (res.ok) {
        setWebhookStatus(await res.json());
      }
    } catch (err) {
      console.error('Erro ao buscar status webhook:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const whatsappConnected = webhookStatus?.whatsapp_connection === 'connected';
  const webhookActive = webhookStatus?.webhook === 'active';

  return (
    <div className="flex-1 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Integrações</h1>
              <p className="text-gray-500 mt-1">Conecte suas ferramentas favoritas ao Smith 2.0</p>
            </div>
            <button
              onClick={fetchStatus}
              disabled={loading}
              className="p-2.5 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
              title="Atualizar status"
            >
              <RefreshCw className={`w-5 h-5 text-gray-600 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      <div className="p-8 space-y-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-white rounded-xl p-5 border border-gray-200">
            <div className="flex items-center gap-3 mb-3">
              <div className="p-2.5 bg-green-100 rounded-lg">
                <Zap className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Integrações Ativas</p>
                <p className="text-2xl font-bold text-gray-900">
                  {loading ? '—' : (whatsappConnected ? 1 : 0) + 0}
                </p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-xl p-5 border border-gray-200">
            <div className="flex items-center gap-3 mb-3">
              <div className="p-2.5 bg-purple-100 rounded-lg">
                <MessageCircle className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Leads via WhatsApp</p>
                <p className="text-2xl font-bold text-gray-900">
                  {loading ? '—' : webhookStatus?.total_leads ?? 0}
                </p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-xl p-5 border border-gray-200">
            <div className="flex items-center gap-3 mb-3">
              <div className="p-2.5 bg-blue-100 rounded-lg">
                <Calendar className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Calendários</p>
                <p className="text-2xl font-bold text-gray-900">0</p>
              </div>
            </div>
          </div>
        </div>

        {/* WhatsApp / Evolution Integration */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="p-6 border-b border-gray-100">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl flex items-center justify-center">
                  <MessageCircle className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-gray-900">WhatsApp (Evolution API)</h2>
                  <p className="text-sm text-gray-500">Receba e responda mensagens do WhatsApp automaticamente</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {loading ? (
                  <Loader2 className="w-4 h-4 text-gray-400 animate-spin" />
                ) : whatsappConnected ? (
                  <span className="flex items-center gap-1.5 text-sm font-medium text-green-700 bg-green-50 border border-green-200 px-3 py-1 rounded-full">
                    <CheckCircle2 className="w-4 h-4" /> Conectado
                  </span>
                ) : (
                  <span className="flex items-center gap-1.5 text-sm font-medium text-yellow-700 bg-yellow-50 border border-yellow-200 px-3 py-1 rounded-full">
                    <AlertCircle className="w-4 h-4" /> Aguardando configuração
                  </span>
                )}
              </div>
            </div>
          </div>
          <div className="p-6 space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Status do Webhook</p>
                <div className="flex items-center gap-2">
                  {loading ? (
                    <Loader2 className="w-4 h-4 text-gray-400 animate-spin" />
                  ) : webhookActive ? (
                    <>
                      <CheckCircle2 className="w-4 h-4 text-green-500" />
                      <span className="text-sm font-semibold text-green-700">Ativo</span>
                    </>
                  ) : (
                    <>
                      <XCircle className="w-4 h-4 text-red-500" />
                      <span className="text-sm font-semibold text-red-700">Inativo</span>
                    </>
                  )}
                </div>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Conexão WhatsApp</p>
                <div className="flex items-center gap-2">
                  {loading ? (
                    <Loader2 className="w-4 h-4 text-gray-400 animate-spin" />
                  ) : whatsappConnected ? (
                    <>
                      <CheckCircle2 className="w-4 h-4 text-green-500" />
                      <span className="text-sm font-semibold text-green-700">Online</span>
                    </>
                  ) : (
                    <>
                      <AlertCircle className="w-4 h-4 text-yellow-500" />
                      <span className="text-sm font-semibold text-yellow-700">Não conectado</span>
                    </>
                  )}
                </div>
              </div>
            </div>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm text-blue-800">
                <strong>Webhook URL:</strong> Configure esta URL na Evolution API para receber mensagens do WhatsApp:
              </p>
              <code className="block mt-2 text-xs bg-blue-100 text-blue-900 px-3 py-2 rounded font-mono break-all">
                {API_URL}/webhook/whatsapp
              </code>
            </div>
          </div>
        </div>

        {/* Google Calendar */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="p-6 border-b border-gray-100">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-cyan-600 rounded-xl flex items-center justify-center">
                  <Calendar className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-gray-900">Google Calendar</h2>
                  <p className="text-sm text-gray-500">Agendar reuniões automaticamente no seu calendário</p>
                </div>
              </div>
              <span className="flex items-center gap-1.5 text-sm font-medium text-yellow-700 bg-yellow-50 border border-yellow-200 px-3 py-1 rounded-full">
                <AlertCircle className="w-4 h-4" /> Aguardando credenciais
              </span>
            </div>
          </div>
          <div className="p-6">
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <p className="text-sm text-yellow-800">
                Para habilitar a integração com Google Calendar, adicione o arquivo <strong>google_credentials.json</strong> no diretório do backend e configure a variável <strong>GOOGLE_CALENDAR_ID</strong>.
              </p>
            </div>
          </div>
        </div>

        {/* Facebook Lead Ads */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="p-6 border-b border-gray-100">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-xl flex items-center justify-center">
                  <span className="text-white font-bold text-lg">f</span>
                </div>
                <div>
                  <h2 className="text-lg font-bold text-gray-900">Facebook Lead Ads</h2>
                  <p className="text-sm text-gray-500">Captura automática de leads do Facebook</p>
                </div>
              </div>
              <span className="flex items-center gap-1.5 text-sm font-medium text-yellow-700 bg-yellow-50 border border-yellow-200 px-3 py-1 rounded-full">
                <AlertCircle className="w-4 h-4" /> Aguardando configuração
              </span>
            </div>
          </div>
          <div className="p-6">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm text-blue-800">
                <strong>Webhook URL:</strong> Configure esta URL nos webhooks do Facebook:
              </p>
              <code className="block mt-2 text-xs bg-blue-100 text-blue-900 px-3 py-2 rounded font-mono break-all">
                {API_URL}/webhook/facebook
              </code>
            </div>
          </div>
        </div>

        {/* OpenAI / IA */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="p-6 border-b border-gray-100">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-gradient-to-br from-purple-600 to-pink-600 rounded-xl flex items-center justify-center">
                  <span className="text-white font-bold text-sm">AI</span>
                </div>
                <div>
                  <h2 className="text-lg font-bold text-gray-900">OpenAI (Smith IA)</h2>
                  <p className="text-sm text-gray-500">Motor de inteligência artificial do agente Smith</p>
                </div>
              </div>
              <span className="flex items-center gap-1.5 text-sm font-medium text-green-700 bg-green-50 border border-green-200 px-3 py-1 rounded-full">
                <CheckCircle2 className="w-4 h-4" /> Configurado
              </span>
            </div>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Modelo</p>
                <p className="text-sm font-semibold text-gray-800">GPT-4o</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">API Key</p>
                <p className="text-sm font-semibold text-gray-800">sk-•••••••••••••</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
