'use client';

import { useEffect, useState } from 'react';
import { Loader2, User, Mail, Phone, Building2, Save, CheckCircle2 } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ClientData {
  id: string;
  nome: string;
  email: string;
  telefone?: string;
  empresa?: string;
  documento?: string;
  avatar_url?: string;
  created_at: string;
}

export default function ConfiguracoesPag() {
  const [client, setClient] = useState<ClientData | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [form, setForm] = useState({
    nome: '',
    email: '',
    telefone: '',
    empresa: '',
    documento: '',
  });

  useEffect(() => {
    fetchClient();
  }, []);

  const fetchClient = async () => {
    try {
      const token = localStorage.getItem('portal_access_token');
      const res = await fetch(`${API_URL}/api/portal/auth/me`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (res.ok) {
        const data: ClientData = await res.json();
        setClient(data);
        setForm({
          nome: data.nome || '',
          email: data.email || '',
          telefone: data.telefone || '',
          empresa: data.empresa || '',
          documento: data.documento || '',
        });
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field: string, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    setSaved(false);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const token = localStorage.getItem('portal_access_token');
      const res = await fetch(`${API_URL}/api/portal/auth/me`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(form),
      });
      if (res.ok) {
        const updated: ClientData = await res.json();
        setClient(updated);
        // Atualiza localStorage também
        localStorage.setItem('portal_client', JSON.stringify(updated));
        setSaved(true);
        setTimeout(() => setSaved(false), 3000);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-purple-500 animate-spin" />
      </div>
    );
  }

  const fields = [
    { key: 'nome', label: 'Nome Completo', icon: User, type: 'text', placeholder: 'João Silva' },
    { key: 'email', label: 'Email', icon: Mail, type: 'email', placeholder: 'joao@empresa.com' },
    { key: 'telefone', label: 'Telefone', icon: Phone, type: 'tel', placeholder: '(11) 99999-9999' },
    { key: 'empresa', label: 'Nome da Empresa', icon: Building2, type: 'text', placeholder: 'Empresa Ltda' },
    { key: 'documento', label: 'CPF / CNPJ', icon: User, type: 'text', placeholder: '000.000.000-00' },
  ];

  return (
    <div className="p-6 lg:p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Configurações</h1>
        <p className="text-gray-500 mt-1">Gerenciar seu perfil e dados de conta</p>
      </div>

      <div className="max-w-2xl">
        {/* Profile Card */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm">
          {/* Avatar Section */}
          <div className="p-6 border-b border-gray-100">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-fuchsia-500 rounded-2xl flex items-center justify-center">
                {client?.avatar_url ? (
                  <img
                    src={client.avatar_url}
                    alt={client.nome}
                    className="w-16 h-16 rounded-2xl object-cover"
                  />
                ) : (
                  <User className="w-8 h-8 text-white" />
                )}
              </div>
              <div>
                <h2 className="font-semibold text-gray-900 text-lg">{client?.nome}</h2>
                <p className="text-sm text-gray-500">{client?.empresa || client?.email}</p>
              </div>
            </div>
          </div>

          {/* Form */}
          <div className="p-6 space-y-5">
            {fields.map(({ key, label, icon: Icon, type, placeholder }) => (
              <div key={key}>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">{label}</label>
                <div className="relative">
                  <Icon className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4.5 h-4.5 text-gray-400" />
                  <input
                    type={type}
                    value={form[key as keyof typeof form]}
                    onChange={(e) => handleChange(key, e.target.value)}
                    placeholder={placeholder}
                    className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500"
                  />
                </div>
              </div>
            ))}
          </div>

          {/* Footer */}
          <div className="p-6 border-t border-gray-100 flex items-center justify-between">
            <p className="text-xs text-gray-400">
              Conta criada em {client ? new Date(client.created_at).toLocaleDateString('pt-BR') : ''}
            </p>
            <div className="flex items-center gap-3">
              {saved && (
                <span className="flex items-center gap-1.5 text-sm text-green-600">
                  <CheckCircle2 className="w-4 h-4" /> Salvo com sucesso
                </span>
              )}
              <button
                onClick={handleSave}
                disabled={saving}
                className="flex items-center gap-2 px-6 py-2.5 bg-purple-600 text-white font-medium rounded-xl hover:bg-purple-700 disabled:opacity-50 transition-colors"
              >
                <Save className="w-4 h-4" />
                {saving ? 'Salvando...' : 'Salvar'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
