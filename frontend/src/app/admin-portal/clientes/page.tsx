'use client';

import { useEffect, useState } from 'react';
import {
  Users, Search, Plus, Loader2, Mail, Phone, Building2,
  FolderKanban, X, CheckCircle2
} from 'lucide-react';
import Link from 'next/link';

import { adminFetch } from '@/lib/auth';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Client {
  id: string;
  nome: string;
  email: string;
  telefone?: string;
  empresa?: string;
  ativo: boolean;
  created_at: string;
}

export default function AdminClientesPage() {
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [created, setCreated] = useState(false);
  const [form, setForm] = useState({ nome: '', email: '', senha: '', telefone: '', empresa: '' });

  useEffect(() => {
    fetchClients();
  }, []);

  const fetchClients = async () => {
    try {
      const res = await adminFetch(`${API_URL}/api/portal/admin/clients`);
      if (res.ok) setClients(await res.json());
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const createClient = async () => {
    setCreating(true);
    try {
      const res = await adminFetch(`${API_URL}/api/portal/admin/clients`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      if (res.ok) {
        const newClient: Client = await res.json();
        setClients((prev) => [newClient, ...prev]);
        setCreated(true);
        setForm({ nome: '', email: '', senha: '', telefone: '', empresa: '' });
        setTimeout(() => {
          setCreated(false);
          setModalOpen(false);
        }, 1500);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setCreating(false);
    }
  };

  const filtered = clients.filter(
    (c) =>
      c.nome.toLowerCase().includes(search.toLowerCase()) ||
      c.email.toLowerCase().includes(search.toLowerCase()) ||
      (c.empresa || '').toLowerCase().includes(search.toLowerCase())
  );

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-purple-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Clientes</h1>
          <p className="text-gray-500 mt-1">{clients.length} cliente{clients.length !== 1 ? 's' : ''} cadastrado{clients.length !== 1 ? 's' : ''}</p>
        </div>
        <button
          onClick={() => setModalOpen(true)}
          className="flex items-center gap-2 px-5 py-2.5 bg-purple-600 text-white font-medium rounded-xl hover:bg-purple-700 transition-colors"
        >
          <Plus className="w-4 h-4" /> Novo Cliente
        </button>
      </div>

      {/* Search */}
      <div className="mb-6">
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Buscar clientes..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500"
          />
        </div>
      </div>

      {/* Client List */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        {filtered.length === 0 ? (
          <div className="p-12 text-center">
            <Users className="w-14 h-14 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-1">
              {search ? 'Nenhum cliente encontrado' : 'Sem clientes'}
            </h3>
            <p className="text-gray-500">
              {search ? 'Tente outro termo de busca' : 'Clique em "Novo Cliente" para criar'}
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {filtered.map((client) => (
              <div key={client.id} className="p-5 flex items-center gap-4">
                <div className="w-11 h-11 bg-gradient-to-br from-purple-500 to-fuchsia-500 rounded-xl flex items-center justify-center">
                  <span className="text-white font-bold text-sm">
                    {client.nome.split(' ').map((n) => n[0]).slice(0, 2).join('')}
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-gray-900">{client.nome}</h3>
                  <div className="flex flex-wrap gap-x-4 gap-y-1 mt-0.5">
                    <span className="flex items-center gap-1 text-sm text-gray-500">
                      <Mail className="w-3.5 h-3.5" /> {client.email}
                    </span>
                    {client.telefone && (
                      <span className="flex items-center gap-1 text-sm text-gray-500">
                        <Phone className="w-3.5 h-3.5" /> {client.telefone}
                      </span>
                    )}
                    {client.empresa && (
                      <span className="flex items-center gap-1 text-sm text-gray-500">
                        <Building2 className="w-3.5 h-3.5" /> {client.empresa}
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`flex items-center gap-1 text-xs font-medium px-2.5 py-1 rounded-full ${client.ativo ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
                    <span className={`w-1.5 h-1.5 rounded-full ${client.ativo ? 'bg-green-500' : 'bg-gray-400'}`} />
                    {client.ativo ? 'Ativo' : 'Inativo'}
                  </span>
                  <Link
                    href={`/admin-portal/projetos?client=${client.id}`}
                    className="flex items-center gap-1 text-sm text-purple-600 hover:text-purple-700"
                  >
                    <FolderKanban className="w-4 h-4" /> Projetos
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create Client Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/40" onClick={() => setModalOpen(false)} />
          <div className="relative bg-white rounded-2xl shadow-xl w-full max-w-md mx-4">
            <div className="p-6 border-b border-gray-100 flex items-center justify-between">
              <h2 className="font-bold text-gray-900 text-lg">Novo Cliente</h2>
              <button onClick={() => setModalOpen(false)} className="text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            {created ? (
              <div className="p-10 text-center">
                <CheckCircle2 className="w-14 h-14 text-green-500 mx-auto mb-3" />
                <p className="font-semibold text-gray-900">Cliente criado com sucesso!</p>
              </div>
            ) : (
              <div className="p-6 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">Nome</label>
                  <input
                    type="text"
                    value={form.nome}
                    onChange={(e) => setForm((f) => ({ ...f, nome: e.target.value }))}
                    placeholder="João Silva"
                    className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">Email</label>
                  <input
                    type="email"
                    value={form.email}
                    onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                    placeholder="joao@empresa.com"
                    className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">Senha</label>
                  <input
                    type="password"
                    value={form.senha}
                    onChange={(e) => setForm((f) => ({ ...f, senha: e.target.value }))}
                    placeholder="Mínimo 6 caracteres"
                    className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">Telefone</label>
                    <input
                      type="tel"
                      value={form.telefone}
                      onChange={(e) => setForm((f) => ({ ...f, telefone: e.target.value }))}
                      placeholder="(11) 99999-9999"
                      className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">Empresa</label>
                    <input
                      type="text"
                      value={form.empresa}
                      onChange={(e) => setForm((f) => ({ ...f, empresa: e.target.value }))}
                      placeholder="Empresa Ltda"
                      className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500"
                    />
                  </div>
                </div>

                <div className="flex gap-3 pt-2">
                  <button
                    onClick={createClient}
                    disabled={creating || !form.nome || !form.email || !form.senha}
                    className="flex-1 py-3 bg-purple-600 text-white font-medium rounded-xl hover:bg-purple-700 disabled:opacity-50 transition-colors"
                  >
                    {creating ? 'Criando...' : 'Criar Cliente'}
                  </button>
                  <button
                    onClick={() => setModalOpen(false)}
                    className="px-5 py-3 bg-gray-100 text-gray-600 font-medium rounded-xl hover:bg-gray-200 transition-colors"
                  >
                    Cancelar
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
