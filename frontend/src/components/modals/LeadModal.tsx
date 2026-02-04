'use client';

import { useState, useEffect } from 'react';
import { Lead, LeadOrigin } from '@/types/lead';
import { X, Save, Loader2 } from 'lucide-react';
import { useLeadsStore } from '@/store/useLeadsStore';
import { CreateLeadData } from '@/lib/api';

interface LeadModalProps {
  isOpen: boolean;
  onClose: () => void;
  lead?: Lead | null;
}

export function LeadModal({ isOpen, onClose, lead }: LeadModalProps) {
  const { createLead, updateLead, isLoading } = useLeadsStore();
  const [formData, setFormData] = useState({
    nome: '',
    telefone: '',
    empresa: '',
    email: '',
    origem: 'whatsapp' as LeadOrigin,
    notas: '',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (lead) {
      setFormData({
        nome: lead.nome,
        telefone: lead.telefone,
        empresa: lead.empresa || '',
        email: lead.email || '',
        origem: lead.origem,
        notas: lead.notas || '',
      });
    } else {
      setFormData({
        nome: '',
        telefone: '',
        empresa: '',
        email: '',
        origem: 'whatsapp',
        notas: '',
      });
    }
    setErrors({});
  }, [lead, isOpen]);

  const validate = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.nome.trim()) {
      newErrors.nome = 'Nome é obrigatório';
    }

    if (!formData.telefone.trim()) {
      newErrors.telefone = 'Telefone é obrigatório';
    } else if (!/^\+?\d{10,15}$/.test(formData.telefone.replace(/\s/g, ''))) {
      newErrors.telefone = 'Telefone inválido (ex: +5511999999999)';
    }

    if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Email inválido';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) return;

    try {
      if (lead) {
        // Atualizar lead existente
        await updateLead(lead.id, {
          nome: formData.nome,
          empresa: formData.empresa || undefined,
          email: formData.email || undefined,
          notas: formData.notas || undefined,
        });
      } else {
        // Criar novo lead
        const newLeadData: CreateLeadData = {
          nome: formData.nome,
          telefone: formData.telefone,
          empresa: formData.empresa || undefined,
          email: formData.email || undefined,
          origem: formData.origem,
          notas: formData.notas || undefined,
        };

        await createLead(newLeadData);
      }

      onClose();
    } catch (error) {
      console.error('Erro ao salvar lead:', error);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 bg-gradient-to-r from-purple-500 to-pink-500">
          <h2 className="text-2xl font-bold text-white">
            {lead ? 'Editar Lead' : 'Novo Lead'}
          </h2>
          <button
            onClick={onClose}
            className="p-2 text-white/80 hover:text-white hover:bg-white/20 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          {/* Nome */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Nome Completo <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.nome}
              onChange={(e) => setFormData({ ...formData, nome: e.target.value })}
              className={`w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all ${
                errors.nome ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="João Silva"
            />
            {errors.nome && (
              <p className="mt-1 text-sm text-red-500">{errors.nome}</p>
            )}
          </div>

          {/* Telefone e Empresa */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Telefone <span className="text-red-500">*</span>
              </label>
              <input
                type="tel"
                value={formData.telefone}
                onChange={(e) => setFormData({ ...formData, telefone: e.target.value })}
                className={`w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all ${
                  errors.telefone ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="+5511999999999"
                disabled={!!lead} // Não permitir editar telefone
              />
              {errors.telefone && (
                <p className="mt-1 text-sm text-red-500">{errors.telefone}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Empresa
              </label>
              <input
                type="text"
                value={formData.empresa}
                onChange={(e) => setFormData({ ...formData, empresa: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all"
                placeholder="Tech Corp Ltda"
              />
            </div>
          </div>

          {/* Email */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Email
            </label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className={`w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all ${
                errors.email ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="joao@techcorp.com"
            />
            {errors.email && (
              <p className="mt-1 text-sm text-red-500">{errors.email}</p>
            )}
          </div>

          {/* Origem */}
          {!lead && (
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Origem <span className="text-red-500">*</span>
              </label>
              <select
                value={formData.origem}
                onChange={(e) => setFormData({ ...formData, origem: e.target.value as LeadOrigin })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all"
              >
                <option value="whatsapp">WhatsApp</option>
                <option value="instagram">Instagram</option>
                <option value="site">Site</option>
                <option value="indicacao">Indicação</option>
                <option value="outro">Outro</option>
              </select>
            </div>
          )}

          {/* Notas */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Notas
            </label>
            <textarea
              value={formData.notas}
              onChange={(e) => setFormData({ ...formData, notas: e.target.value })}
              rows={4}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all resize-none"
              placeholder="Observações sobre o lead..."
            />
          </div>
        </form>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-200 bg-gray-50">
          <button
            type="button"
            onClick={onClose}
            className="px-6 py-3 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors font-medium"
          >
            Cancelar
          </button>
          <button
            onClick={handleSubmit}
            disabled={isLoading}
            className="px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:shadow-lg transition-all font-medium flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Salvando...
              </>
            ) : (
              <>
                <Save className="w-5 h-5" />
                {lead ? 'Salvar Alterações' : 'Criar Lead'}
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
