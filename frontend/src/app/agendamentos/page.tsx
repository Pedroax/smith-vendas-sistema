'use client';

import { useState, useEffect } from 'react';
import {
  Calendar as CalendarIcon, Clock, User, Building2, Phone, Video,
  Plus, ChevronLeft, ChevronRight, Filter, Search, Loader2,
  MapPin, Edit2, Trash2, CheckCircle, MessageSquare, X, Send
} from 'lucide-react';
import {
  format, startOfMonth, endOfMonth, eachDayOfInterval, isSameMonth,
  isSameDay, addMonths, subMonths, startOfWeek, endOfWeek, isToday,
  addDays, startOfDay, endOfDay
} from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { useToast } from '@/contexts/ToastContext';
import { apiClient } from '@/lib/api';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Lead {
  id: string;
  nome: string;
  telefone: string;
  email?: string;
  empresa?: string;
  status: string;
}

interface Appointment {
  id: string;
  lead_id: string;
  lead_nome?: string;
  tipo: 'reuniao' | 'ligacao' | 'follow_up' | 'demo' | 'apresentacao' | 'outro';
  titulo: string;
  descricao?: string;
  data_hora: string;
  duracao_minutos: number;
  status: 'agendado' | 'confirmado' | 'concluido' | 'cancelado' | 'remarcado';
  user_nome: string;
  location?: string;
  meeting_url?: string;
  observacoes?: string;
  created_at: string;
}

const appointmentTypes = [
  { value: 'reuniao', label: 'Reunião', icon: Video, color: 'text-purple-600 bg-purple-50' },
  { value: 'ligacao', label: 'Ligação', icon: Phone, color: 'text-green-600 bg-green-50' },
  { value: 'follow_up', label: 'Follow-up', icon: MessageSquare, color: 'text-blue-600 bg-blue-50' },
  { value: 'demo', label: 'Demo', icon: CheckCircle, color: 'text-orange-600 bg-orange-50' },
  { value: 'apresentacao', label: 'Apresentação', icon: User, color: 'text-pink-600 bg-pink-50' },
  { value: 'outro', label: 'Outro', icon: CalendarIcon, color: 'text-gray-600 bg-gray-50' },
];

export default function AgendamentosPage() {
  const { showToast } = useToast();

  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [viewMode, setViewMode] = useState<'calendar' | 'list'>('calendar');

  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);

  // Modal state
  const [showModal, setShowModal] = useState(false);
  const [editingAppointment, setEditingAppointment] = useState<Appointment | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Form state
  const [formData, setFormData] = useState<{
    lead_id: string;
    tipo: 'reuniao' | 'ligacao' | 'follow_up' | 'demo' | 'apresentacao' | 'outro';
    titulo: string;
    descricao: string;
    data_hora: string;
    duracao_minutos: number;
    location: string;
    meeting_url: string;
    observacoes: string;
    user_nome: string;
  }>({
    lead_id: '',
    tipo: 'reuniao',
    titulo: '',
    descricao: '',
    data_hora: '',
    duracao_minutos: 60,
    location: '',
    meeting_url: '',
    observacoes: '',
    user_nome: 'Pedro Machado'
  });

  useEffect(() => {
    fetchData();
  }, [currentMonth]);

  const fetchData = async () => {
    setLoading(true);
    try {
      // Fetch leads
      const leadsData = await apiClient.getLeads();
      setLeads(leadsData);

      // Fetch appointments for current month
      const monthStart = startOfMonth(currentMonth);
      const monthEnd = endOfMonth(currentMonth);

      const res = await fetch(
        `${API_URL}/api/appointments?start_date=${monthStart.toISOString()}&end_date=${monthEnd.toISOString()}`
      );

      if (res.ok) {
        const data = await res.json();
        setAppointments(data);
      }
    } catch (err) {
      console.error(err);
      showToast('Erro ao carregar dados', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.lead_id || !formData.titulo || !formData.data_hora) {
      showToast('Preencha os campos obrigatórios', 'warning');
      return;
    }

    setSubmitting(true);
    try {
      const url = editingAppointment
        ? `${API_URL}/api/appointments/${editingAppointment.id}`
        : `${API_URL}/api/appointments`;

      const method = editingAppointment ? 'PUT' : 'POST';

      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      if (res.ok) {
        const appointment = await res.json();

        if (editingAppointment) {
          setAppointments(prev => prev.map(a => a.id === appointment.id ? appointment : a));
          showToast('Agendamento atualizado!', 'success');
        } else {
          setAppointments(prev => [...prev, appointment]);
          showToast('Agendamento criado!', 'success');
        }

        closeModal();
      } else {
        showToast('Erro ao salvar agendamento', 'error');
      }
    } catch (err) {
      console.error(err);
      showToast('Erro ao salvar agendamento', 'error');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (appointmentId: string) => {
    if (!confirm('Deseja realmente deletar este agendamento?')) return;

    try {
      const res = await fetch(`${API_URL}/api/appointments/${appointmentId}`, {
        method: 'DELETE',
      });

      if (res.ok) {
        setAppointments(prev => prev.filter(a => a.id !== appointmentId));
        showToast('Agendamento deletado', 'success');
      } else {
        showToast('Erro ao deletar agendamento', 'error');
      }
    } catch (err) {
      console.error(err);
      showToast('Erro ao deletar agendamento', 'error');
    }
  };

  const handleMarkComplete = async (appointmentId: string) => {
    try {
      const res = await fetch(`${API_URL}/api/appointments/${appointmentId}/complete`, {
        method: 'POST',
      });

      if (res.ok) {
        const appointment = await res.json();
        setAppointments(prev => prev.map(a => a.id === appointment.id ? appointment : a));
        showToast('Agendamento marcado como concluído', 'success');
      } else {
        showToast('Erro ao atualizar agendamento', 'error');
      }
    } catch (err) {
      console.error(err);
      showToast('Erro ao atualizar agendamento', 'error');
    }
  };

  const openModal = (appointment?: Appointment) => {
    if (appointment) {
      setEditingAppointment(appointment);
      setFormData({
        lead_id: appointment.lead_id,
        tipo: appointment.tipo,
        titulo: appointment.titulo,
        descricao: appointment.descricao || '',
        data_hora: appointment.data_hora.slice(0, 16), // Format for datetime-local input
        duracao_minutos: appointment.duracao_minutos,
        location: appointment.location || '',
        meeting_url: appointment.meeting_url || '',
        observacoes: appointment.observacoes || '',
        user_nome: appointment.user_nome
      });
    } else {
      setEditingAppointment(null);
      const defaultDate = selectedDate || new Date();
      const dateString = format(defaultDate, "yyyy-MM-dd'T'HH:mm");

      setFormData({
        lead_id: '',
        tipo: 'reuniao',
        titulo: '',
        descricao: '',
        data_hora: dateString,
        duracao_minutos: 60,
        location: '',
        meeting_url: '',
        observacoes: '',
        user_nome: 'Pedro Machado'
      });
    }
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setEditingAppointment(null);
  };

  // Calendar logic
  const monthStart = startOfMonth(currentMonth);
  const monthEnd = endOfMonth(currentMonth);
  const calendarStart = startOfWeek(monthStart);
  const calendarEnd = endOfWeek(monthEnd);
  const calendarDays = eachDayOfInterval({ start: calendarStart, end: calendarEnd });

  const getAppointmentsForDay = (day: Date) => {
    return appointments.filter(a => {
      const appointmentDate = new Date(a.data_hora);
      return isSameDay(appointmentDate, day);
    });
  };

  const selectedDayAppointments = selectedDate
    ? getAppointmentsForDay(selectedDate)
    : [];

  const todayAppointments = appointments.filter(a => isToday(new Date(a.data_hora)));

  const upcomingAppointments = appointments
    .filter(a => {
      const date = new Date(a.data_hora);
      return date >= new Date() && a.status !== 'cancelado' && a.status !== 'concluido';
    })
    .sort((a, b) => new Date(a.data_hora).getTime() - new Date(b.data_hora).getTime());

  const getTypeConfig = (tipo: string) => {
    return appointmentTypes.find(t => t.value === tipo) || appointmentTypes[0];
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="w-8 h-8 text-purple-600 animate-spin" />
      </div>
    );
  }

  return (
    <div className="flex-1 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="px-8 py-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-1">
                Agendamentos
              </h1>
              <p className="text-gray-500">
                Gerencie suas reuniões e compromissos
              </p>
            </div>

            <div className="flex items-center gap-3">
              {/* View Toggle */}
              <div className="flex items-center gap-2 bg-gray-100 p-1 rounded-lg">
                <button
                  onClick={() => setViewMode('calendar')}
                  className={`flex items-center gap-2 px-4 py-2 rounded-md font-medium text-sm transition-all ${
                    viewMode === 'calendar'
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <CalendarIcon className="w-4 h-4" />
                  Calendário
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className={`flex items-center gap-2 px-4 py-2 rounded-md font-medium text-sm transition-all ${
                    viewMode === 'list'
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <Filter className="w-4 h-4" />
                  Lista
                </button>
              </div>

              {/* New Appointment */}
              <button
                onClick={() => openModal()}
                className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:shadow-lg transition-all"
              >
                <Plus className="w-5 h-5" />
                <span className="font-medium">Novo Agendamento</span>
              </button>
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-4 gap-4">
            <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-4 border border-blue-200">
              <div className="flex items-center justify-between mb-2">
                <div className="p-2 bg-blue-500 rounded-lg">
                  <CalendarIcon className="w-5 h-5 text-white" />
                </div>
              </div>
              <div className="text-2xl font-bold text-blue-900">{appointments.length}</div>
              <div className="text-xs text-blue-600 font-medium">Total de Agendamentos</div>
            </div>

            <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-xl p-4 border border-green-200">
              <div className="flex items-center justify-between mb-2">
                <div className="p-2 bg-green-500 rounded-lg">
                  <Clock className="w-5 h-5 text-white" />
                </div>
              </div>
              <div className="text-2xl font-bold text-green-900">{todayAppointments.length}</div>
              <div className="text-xs text-green-600 font-medium">Hoje</div>
            </div>

            <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl p-4 border border-purple-200">
              <div className="flex items-center justify-between mb-2">
                <div className="p-2 bg-purple-500 rounded-lg">
                  <CheckCircle className="w-5 h-5 text-white" />
                </div>
              </div>
              <div className="text-2xl font-bold text-purple-900">{upcomingAppointments.length}</div>
              <div className="text-xs text-purple-600 font-medium">Próximos</div>
            </div>

            <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-xl p-4 border border-orange-200">
              <div className="flex items-center justify-between mb-2">
                <div className="p-2 bg-orange-500 rounded-lg">
                  <CheckCircle className="w-5 h-5 text-white" />
                </div>
              </div>
              <div className="text-2xl font-bold text-orange-900">
                {appointments.filter(a => a.status === 'concluido').length}
              </div>
              <div className="text-xs text-orange-600 font-medium">Concluídos</div>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-8">
        {viewMode === 'calendar' ? (
          <div className="grid grid-cols-3 gap-6">
            {/* Calendar */}
            <div className="col-span-2 bg-white rounded-xl border border-gray-200 p-6">
              {/* Calendar Header */}
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-gray-900">
                  {format(currentMonth, 'MMMM yyyy', { locale: ptBR })}
                </h2>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setCurrentMonth(subMonths(currentMonth, 1))}
                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    <ChevronLeft className="w-5 h-5 text-gray-600" />
                  </button>
                  <button
                    onClick={() => setCurrentMonth(new Date())}
                    className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    Hoje
                  </button>
                  <button
                    onClick={() => setCurrentMonth(addMonths(currentMonth, 1))}
                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    <ChevronRight className="w-5 h-5 text-gray-600" />
                  </button>
                </div>
              </div>

              {/* Calendar Grid */}
              <div className="grid grid-cols-7 gap-1">
                {/* Days of week */}
                {['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'].map((day) => (
                  <div key={day} className="text-center text-xs font-semibold text-gray-500 py-2">
                    {day}
                  </div>
                ))}

                {/* Calendar days */}
                {calendarDays.map((day, idx) => {
                  const dayAppointments = getAppointmentsForDay(day);
                  const isCurrentMonth = isSameMonth(day, currentMonth);
                  const isDayToday = isToday(day);
                  const isSelected = selectedDate && isSameDay(day, selectedDate);

                  return (
                    <button
                      key={idx}
                      onClick={() => setSelectedDate(day)}
                      className={`
                        aspect-square p-2 rounded-lg border transition-all relative
                        ${!isCurrentMonth ? 'text-gray-300 bg-gray-50' : 'text-gray-900'}
                        ${isDayToday ? 'border-purple-500 bg-purple-50 font-bold' : 'border-gray-200'}
                        ${isSelected ? 'bg-purple-100 border-purple-500 ring-2 ring-purple-200' : 'hover:bg-gray-50'}
                      `}
                    >
                      <div className="text-sm">{format(day, 'd')}</div>
                      {dayAppointments.length > 0 && (
                        <div className="absolute bottom-1 left-1/2 -translate-x-1/2 flex gap-0.5">
                          {dayAppointments.slice(0, 3).map((_, i) => (
                            <div key={i} className="w-1.5 h-1.5 bg-purple-500 rounded-full" />
                          ))}
                        </div>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Sidebar - Appointments do dia selecionado */}
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h3 className="text-lg font-bold text-gray-900 mb-4">
                {selectedDate
                  ? format(selectedDate, "dd 'de' MMMM", { locale: ptBR })
                  : 'Selecione um dia'}
              </h3>

              {selectedDate && selectedDayAppointments.length === 0 ? (
                <div className="text-center py-8">
                  <CalendarIcon className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                  <p className="text-sm text-gray-500 mb-4">Nenhum agendamento</p>
                  <button
                    onClick={() => openModal()}
                    className="text-sm text-purple-600 hover:text-purple-700 font-medium"
                  >
                    + Criar agendamento
                  </button>
                </div>
              ) : (
                <div className="space-y-3">
                  {selectedDayAppointments.map((appointment) => {
                    const config = getTypeConfig(appointment.tipo);
                    const Icon = config.icon;

                    return (
                      <div
                        key={appointment.id}
                        className="p-4 bg-gray-50 rounded-lg border border-gray-200 hover:shadow-md transition-shadow"
                      >
                        <div className="flex items-start gap-3 mb-2">
                          <div className={`flex-shrink-0 w-8 h-8 rounded-lg ${config.color} flex items-center justify-center`}>
                            <Icon className="w-4 h-4" />
                          </div>
                          <div className="flex-1">
                            <div className="font-semibold text-gray-900">{appointment.titulo}</div>
                            <div className="text-xs text-gray-500 mt-1">
                              {format(new Date(appointment.data_hora), 'HH:mm')} • {appointment.duracao_minutos}min
                            </div>
                          </div>
                        </div>

                        <div className="text-sm text-gray-700 mb-2">{appointment.lead_nome}</div>

                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => openModal(appointment)}
                            className="flex-1 px-3 py-1.5 text-xs bg-white border border-gray-200 rounded hover:bg-gray-50 transition-colors"
                          >
                            Editar
                          </button>
                          <button
                            onClick={() => handleDelete(appointment.id)}
                            className="px-3 py-1.5 text-xs text-red-600 hover:bg-red-50 rounded transition-colors"
                          >
                            <Trash2 className="w-3 h-3" />
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        ) : (
          /* List View */
          <div className="bg-white rounded-xl border border-gray-200">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-bold text-gray-900">Próximos Agendamentos</h2>
            </div>
            <div className="divide-y divide-gray-200">
              {upcomingAppointments.length === 0 ? (
                <div className="text-center py-12">
                  <CalendarIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-600 font-medium mb-4">Nenhum agendamento futuro</p>
                  <button
                    onClick={() => openModal()}
                    className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                  >
                    Criar Agendamento
                  </button>
                </div>
              ) : (
                upcomingAppointments.map((appointment) => {
                  const config = getTypeConfig(appointment.tipo);
                  const Icon = config.icon;

                  return (
                    <div key={appointment.id} className="p-6 hover:bg-gray-50 transition-colors">
                      <div className="flex items-start gap-4">
                        {/* Icon */}
                        <div className={`w-12 h-12 rounded-lg ${config.color} flex items-center justify-center flex-shrink-0`}>
                          <Icon className="w-6 h-6" />
                        </div>

                        {/* Info */}
                        <div className="flex-1">
                          <div className="flex items-start justify-between mb-2">
                            <div>
                              <div className="font-bold text-gray-900 text-lg">{appointment.titulo}</div>
                              <div className="text-sm text-gray-600 mt-1">{appointment.lead_nome}</div>
                            </div>
                            <div className="flex items-center gap-2">
                              {appointment.status === 'agendado' && (
                                <button
                                  onClick={() => handleMarkComplete(appointment.id)}
                                  className="p-2 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                                  title="Marcar como concluído"
                                >
                                  <CheckCircle className="w-4 h-4" />
                                </button>
                              )}
                              <button
                                onClick={() => openModal(appointment)}
                                className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                              >
                                <Edit2 className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => handleDelete(appointment.id)}
                                className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                          <div className="grid grid-cols-2 gap-4 text-sm">
                            <div className="flex items-center gap-2 text-gray-600">
                              <Clock className="w-4 h-4" />
                              {format(new Date(appointment.data_hora), "dd/MM/yyyy 'às' HH:mm", { locale: ptBR })}
                            </div>
                            <div className="flex items-center gap-2 text-gray-600">
                              <span className="px-2 py-1 bg-gray-100 rounded text-xs font-medium">
                                {config.label}
                              </span>
                              {appointment.duracao_minutos}min
                            </div>
                          </div>
                          {appointment.location && (
                            <div className="flex items-center gap-2 text-gray-600 text-sm mt-2">
                              <MapPin className="w-4 h-4" />
                              {appointment.location}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        )}
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-2xl font-bold text-gray-900">
                {editingAppointment ? 'Editar Agendamento' : 'Novo Agendamento'}
              </h2>
              <button
                onClick={closeModal}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Lead *
                  </label>
                  <select
                    value={formData.lead_id}
                    onChange={(e) => setFormData(prev => ({ ...prev, lead_id: e.target.value }))}
                    required
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                  >
                    <option value="">Selecione um lead</option>
                    {leads.map(lead => (
                      <option key={lead.id} value={lead.id}>
                        {lead.nome} {lead.empresa && `- ${lead.empresa}`}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Tipo *
                  </label>
                  <select
                    value={formData.tipo}
                    onChange={(e) => setFormData(prev => ({ ...prev, tipo: e.target.value as any }))}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                  >
                    {appointmentTypes.map(type => (
                      <option key={type.value} value={type.value}>{type.label}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Duração (minutos) *
                  </label>
                  <input
                    type="number"
                    value={formData.duracao_minutos}
                    onChange={(e) => setFormData(prev => ({ ...prev, duracao_minutos: parseInt(e.target.value) }))}
                    min="15"
                    step="15"
                    required
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                  />
                </div>

                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Título *
                  </label>
                  <input
                    type="text"
                    value={formData.titulo}
                    onChange={(e) => setFormData(prev => ({ ...prev, titulo: e.target.value }))}
                    placeholder="Ex: Apresentação de proposta"
                    required
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                  />
                </div>

                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Data e Hora *
                  </label>
                  <input
                    type="datetime-local"
                    value={formData.data_hora}
                    onChange={(e) => setFormData(prev => ({ ...prev, data_hora: e.target.value }))}
                    required
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Local
                  </label>
                  <input
                    type="text"
                    value={formData.location}
                    onChange={(e) => setFormData(prev => ({ ...prev, location: e.target.value }))}
                    placeholder="Endereço ou sala"
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Link da Reunião
                  </label>
                  <input
                    type="url"
                    value={formData.meeting_url}
                    onChange={(e) => setFormData(prev => ({ ...prev, meeting_url: e.target.value }))}
                    placeholder="https://meet.google.com/..."
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                  />
                </div>

                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Descrição
                  </label>
                  <textarea
                    value={formData.descricao}
                    onChange={(e) => setFormData(prev => ({ ...prev, descricao: e.target.value }))}
                    placeholder="Detalhes sobre o agendamento..."
                    rows={2}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500/50 resize-none"
                  />
                </div>

                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Observações
                  </label>
                  <textarea
                    value={formData.observacoes}
                    onChange={(e) => setFormData(prev => ({ ...prev, observacoes: e.target.value }))}
                    placeholder="Observações internas..."
                    rows={2}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500/50 resize-none"
                  />
                </div>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="submit"
                  disabled={submitting}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 transition-colors"
                >
                  {submitting ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Send className="w-4 h-4" />
                  )}
                  {editingAppointment ? 'Atualizar' : 'Criar'} Agendamento
                </button>
                <button
                  type="button"
                  onClick={closeModal}
                  className="px-4 py-2.5 border border-gray-200 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Cancelar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
