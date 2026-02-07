'use client';

import { useEffect, useState } from 'react';
import { DndContext, DragEndEvent, DragOverlay, DragStartEvent, PointerSensor, useSensor, useSensors, useDroppable } from '@dnd-kit/core';
import { SortableContext, useSortable, verticalListSortingStrategy } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { Plus, Trash2, X, Calendar, User, FolderOpen, Loader2, CheckCircle2 } from 'lucide-react';
import { useToast } from '@/contexts/ToastContext';
import { API_URL } from '@/lib/api-config';

// --- Types ---
interface Task {
  id: string;
  titulo: string;
  descricao?: string | null;
  status: 'hoje' | 'esta_semana' | 'depois' | 'feito';
  prioridade: 'alta' | 'media' | 'baixa';
  prazo?: string | null;
  lead_id?: string | null;
  lead_nome?: string | null;
  project_id?: string | null;
  project_nome?: string | null;
  created_at: string;
}

interface Lead {
  id: string;
  nome: string;
  empresa?: string | null;
}

interface Project {
  id: string;
  nome: string;
}

// --- Constants ---
const COLUMNS: { id: Task['status']; label: string; emoji: string; accentColor: string }[] = [
  { id: 'hoje', label: 'Hoje', emoji: '🔥', accentColor: 'text-red-600' },
  { id: 'esta_semana', label: 'Esta Semana', emoji: '📅', accentColor: 'text-amber-600' },
  { id: 'depois', label: 'Depois', emoji: '📌', accentColor: 'text-indigo-600' },
  { id: 'feito', label: 'Feito', emoji: '✅', accentColor: 'text-emerald-600' },
];

const PRIORITY_STYLES: Record<string, { bg: string; text: string; label: string }> = {
  alta: { bg: 'bg-red-100', text: 'text-red-700', label: 'Alta' },
  media: { bg: 'bg-amber-100', text: 'text-amber-700', label: 'Média' },
  baixa: { bg: 'bg-blue-100', text: 'text-blue-700', label: 'Baixa' },
};

// --- Helpers ---
function isOverdue(prazo: string | null | undefined) {
  if (!prazo) return false;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const deadline = new Date(prazo.split('T')[0] + 'T00:00:00');
  return deadline < today;
}

function formatDate(dateStr: string) {
  const date = new Date(dateStr.split('T')[0] + 'T12:00:00');
  return date.toLocaleDateString('pt-BR', { day: 'numeric', month: 'short' });
}

// --- TaskCard (draggable) ---
function TaskCard({
  task,
  onEdit,
  onDelete,
  onStatusChange,
  isDragOverlay,
}: {
  task: Task;
  onEdit: (task: Task) => void;
  onDelete: (id: string) => void;
  onStatusChange: (id: string, status: string) => void;
  isDragOverlay?: boolean;
}) {
  const sortable = useSortable({ id: task.id, disabled: isDragOverlay });

  const style = isDragOverlay
    ? {}
    : {
        transform: CSS.Transform.toString(sortable.transform),
        transition: sortable.transition,
      };

  const pStyle = PRIORITY_STYLES[task.prioridade];
  const overdue = isOverdue(task.prazo) && task.status !== 'feito';

  return (
    <div
      ref={isDragOverlay ? undefined : sortable.setNodeRef}
      style={style}
      {...(isDragOverlay ? {} : sortable.attributes)}
      {...(isDragOverlay ? {} : sortable.listeners)}
      className={`bg-white rounded-xl p-3 shadow-sm border transition-all group
        ${isDragOverlay ? 'shadow-xl rotate-2' : 'cursor-grab active:cursor-grabbing hover:shadow-md'}
        ${sortable.isDragging ? 'opacity-40' : ''}
        ${overdue ? 'border-red-300' : 'border-gray-100'}
        ${task.status === 'feito' && !isDragOverlay ? 'opacity-60' : ''}
      `}
      onClick={() => !isDragOverlay && onEdit(task)}
    >
      {/* Title + Priority */}
      <div className="flex items-start justify-between gap-2">
        <p
          className={`text-sm font-medium leading-tight ${
            task.status === 'feito' ? 'text-gray-400 line-through' : 'text-gray-800'
          }`}
        >
          {task.titulo}
        </p>
        <span className={`text-xs font-medium px-2 py-0.5 rounded-full whitespace-nowrap flex-shrink-0 ${pStyle.bg} ${pStyle.text}`}>
          {pStyle.label}
        </span>
      </div>

      {/* Description */}
      {task.descricao && <p className="text-xs text-gray-500 mt-1.5 line-clamp-2">{task.descricao}</p>}

      {/* Meta */}
      <div className="mt-2 space-y-1">
        {task.prazo && (
          <div className={`flex items-center gap-1.5 text-xs ${overdue ? 'text-red-600 font-semibold' : 'text-gray-500'}`}>
            <Calendar className="w-3 h-3" />
            {overdue && <span>Atrasado — </span>}
            {formatDate(task.prazo)}
          </div>
        )}
        {task.lead_nome && (
          <div className="flex items-center gap-1.5 text-xs text-purple-600">
            <User className="w-3 h-3" />
            {task.lead_nome}
          </div>
        )}
        {task.project_nome && (
          <div className="flex items-center gap-1.5 text-xs text-indigo-600">
            <FolderOpen className="w-3 h-3" />
            {task.project_nome}
          </div>
        )}
      </div>

      {/* Hover actions */}
      {!isDragOverlay && (
        <div className="flex items-center justify-between mt-2.5 opacity-0 group-hover:opacity-100 transition-opacity">
          <select
            value={task.status}
            onChange={(e) => {
              e.stopPropagation();
              onStatusChange(task.id, e.target.value);
            }}
            onClick={(e) => e.stopPropagation()}
            className="text-xs text-gray-500 bg-gray-100 rounded-lg px-2 py-1 cursor-pointer border border-gray-200"
          >
            <option value="hoje">→ Hoje</option>
            <option value="esta_semana">→ Esta Semana</option>
            <option value="depois">→ Depois</option>
            <option value="feito">→ Feito</option>
          </select>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDelete(task.id);
            }}
            className="p-1 text-gray-400 hover:text-red-500 transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      )}
    </div>
  );
}

// --- TaskColumn (droppable) ---
function TaskColumn({
  id,
  label,
  emoji,
  accentColor,
  tasks,
  onAddTask,
  onEditTask,
  onDeleteTask,
  onStatusChange,
}: {
  id: string;
  label: string;
  emoji: string;
  accentColor: string;
  tasks: Task[];
  onAddTask: (status: string) => void;
  onEditTask: (task: Task) => void;
  onDeleteTask: (id: string) => void;
  onStatusChange: (id: string, status: string) => void;
}) {
  const { setNodeRef } = useDroppable({ id });

  return (
    <div className="bg-gray-100 rounded-2xl p-3 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-3 px-1">
        <div className="flex items-center gap-2">
          <span>{emoji}</span>
          <h3 className="font-semibold text-gray-700 text-sm">{label}</h3>
          <span className="text-xs bg-gray-200 text-gray-600 rounded-full px-2 py-0.5">{tasks.length}</span>
        </div>
        <button
          onClick={() => onAddTask(id)}
          className="p-1 text-gray-400 hover:text-purple-600 hover:bg-white rounded-lg transition-colors"
        >
          <Plus className="w-4 h-4" />
        </button>
      </div>

      {/* Droppable + Cards */}
      <div
        ref={setNodeRef}
        className="flex-1 min-h-[200px]"
        style={{ maxHeight: 'calc(100vh - 280px)', overflowY: 'auto' }}
      >
        <SortableContext items={tasks.map((t) => t.id)} strategy={verticalListSortingStrategy}>
          <div className="space-y-2">
            {tasks.map((task) => (
              <TaskCard
                key={task.id}
                task={task}
                onEdit={onEditTask}
                onDelete={onDeleteTask}
                onStatusChange={onStatusChange}
              />
            ))}
          </div>
        </SortableContext>

        {/* Empty state */}
        {tasks.length === 0 && (
          <div
            className="text-center py-6 border-2 border-dashed border-gray-200 rounded-xl cursor-pointer hover:border-purple-300 hover:bg-purple-50 transition-colors"
            onClick={() => onAddTask(id)}
          >
            <Plus className="w-5 h-5 text-gray-400 mx-auto mb-1" />
            <p className="text-xs text-gray-400">Adicionar tarefa</p>
          </div>
        )}
      </div>
    </div>
  );
}

// --- Main Page ---
export default function TarefasPage() {
  const { showToast } = useToast();

  const [tasks, setTasks] = useState<Task[]>([]);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  const [modalOpen, setModalOpen] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [activeTask, setActiveTask] = useState<Task | null>(null);

  const [form, setForm] = useState({
    titulo: '',
    descricao: '',
    status: 'hoje',
    prioridade: 'media',
    prazo: '',
    lead_id: '',
    project_id: '',
  });

  // --- DnD sensors (same as CRM) ---
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 8 },
    })
  );

  // --- Fetch ---
  useEffect(() => {
    fetchAll();
  }, []);

  const fetchAll = async () => {
    try {
      const [tasksRes, leadsRes, projectsRes] = await Promise.all([
        fetch(`${API_URL}/api/tasks`),
        fetch(`${API_URL}/api/leads`),
        fetch(`${API_URL}/api/projects`),
      ]);
      if (tasksRes.ok) setTasks(await tasksRes.json());
      if (leadsRes.ok) setLeads(await leadsRes.json());
      if (projectsRes.ok) setProjects(await projectsRes.json());
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // --- DnD handlers ---
  const handleDragStart = (event: DragStartEvent) => {
    const task = tasks.find((t) => t.id === event.active.id);
    if (task) setActiveTask(task);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    setActiveTask(null);
    const { active, over } = event;
    if (!over) return;

    const taskId = active.id as string;
    const newStatus = over.id as string;
    const task = tasks.find((t) => t.id === taskId);

    if (task && task.status !== newStatus) {
      handleStatusChange(taskId, newStatus);
    }
  };

  // --- Modal ---
  const openModal = (task?: Task, defaultStatus?: string) => {
    if (task) {
      setEditingTask(task);
      setForm({
        titulo: task.titulo,
        descricao: task.descricao || '',
        status: task.status,
        prioridade: task.prioridade,
        prazo: task.prazo ? task.prazo.split('T')[0] : '',
        lead_id: task.lead_id || '',
        project_id: task.project_id || '',
      });
    } else {
      setEditingTask(null);
      setForm({
        titulo: '',
        descricao: '',
        status: defaultStatus || 'hoje',
        prioridade: 'media',
        prazo: '',
        lead_id: '',
        project_id: '',
      });
    }
    setModalOpen(true);
  };

  const closeModal = () => {
    setModalOpen(false);
    setEditingTask(null);
  };

  // --- Actions ---
  const handleSubmit = async () => {
    if (!form.titulo.trim()) {
      showToast('Título é obrigatório', 'error');
      return;
    }
    setSubmitting(true);
    try {
      const payload = {
        titulo: form.titulo,
        descricao: form.descricao || null,
        status: form.status,
        prioridade: form.prioridade,
        prazo: form.prazo || null,
        lead_id: form.lead_id || null,
        project_id: form.project_id || null,
      };

      const url = editingTask ? `${API_URL}/api/tasks/${editingTask.id}` : `${API_URL}/api/tasks`;
      const method = editingTask ? 'PUT' : 'POST';

      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        showToast(editingTask ? 'Tarefa atualizada!' : 'Tarefa criada!', 'success');
        closeModal();
        await fetchAll();
      } else {
        const err = await res.json().catch(() => ({ detail: 'Erro' }));
        showToast(err.detail || 'Erro ao salvar', 'error');
      }
    } catch (err) {
      console.error(err);
      showToast('Erro ao salvar tarefa', 'error');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (taskId: string) => {
    if (!confirm('Deletar esta tarefa?')) return;
    try {
      const res = await fetch(`${API_URL}/api/tasks/${taskId}`, { method: 'DELETE' });
      if (res.ok) {
        showToast('Tarefa deletada', 'success');
        setTasks((prev) => prev.filter((t) => t.id !== taskId));
      }
    } catch (err) {
      console.error(err);
      showToast('Erro ao deletar', 'error');
    }
  };

  const handleStatusChange = async (taskId: string, newStatus: string) => {
    // Optimistic update
    setTasks((prev) =>
      prev.map((t) => (t.id === taskId ? { ...t, status: newStatus as Task['status'] } : t))
    );
    try {
      await fetch(`${API_URL}/api/tasks/${taskId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      });
    } catch (err) {
      console.error(err);
      // Revert on failure
      await fetchAll();
    }
  };

  // --- Loading ---
  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 text-purple-600 animate-spin" />
      </div>
    );
  }

  // --- Render ---
  return (
    <div className="p-6 min-h-screen bg-gray-50">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Centro de Trabalho</h1>
          <p className="text-gray-500 text-sm mt-0.5">Suas tarefas e lembretes</p>
        </div>
        <button
          onClick={() => openModal()}
          className="flex items-center gap-2 px-4 py-2.5 bg-purple-600 text-white rounded-xl hover:bg-purple-700 transition-colors font-medium"
        >
          <Plus className="w-4 h-4" />
          Nova Tarefa
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        {COLUMNS.map((col) => {
          const count = tasks.filter((t) => t.status === col.id).length;
          return (
            <div key={col.id} className="bg-white rounded-xl p-4 border border-gray-100 shadow-sm">
              <div className="flex items-center gap-2 mb-1">
                <span>{col.emoji}</span>
                <span className="text-sm font-medium text-gray-600">{col.label}</span>
              </div>
              <p className={`text-2xl font-bold ${col.accentColor}`}>{count}</p>
            </div>
          );
        })}
      </div>

      {/* Kanban with DnD */}
      <DndContext sensors={sensors} onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
        <div className="grid grid-cols-4 gap-4">
          {COLUMNS.map((col) => (
            <TaskColumn
              key={col.id}
              id={col.id}
              label={col.label}
              emoji={col.emoji}
              accentColor={col.accentColor}
              tasks={tasks.filter((t) => t.status === col.id)}
              onAddTask={(status) => openModal(undefined, status)}
              onEditTask={(task) => openModal(task)}
              onDeleteTask={handleDelete}
              onStatusChange={handleStatusChange}
            />
          ))}
        </div>

        {/* Drag Overlay — ghost card while dragging */}
        <DragOverlay>
          {activeTask ? (
            <TaskCard
              task={activeTask}
              onEdit={() => {}}
              onDelete={() => {}}
              onStatusChange={() => {}}
              isDragOverlay
            />
          ) : null}
        </DragOverlay>
      </DndContext>

      {/* === Modal === */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/40" onClick={closeModal} />
          <div className="relative bg-white rounded-2xl shadow-xl w-full max-w-lg">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-100">
              <h2 className="text-lg font-bold text-gray-900">
                {editingTask ? 'Editar Tarefa' : 'Nova Tarefa'}
              </h2>
              <button onClick={closeModal} className="p-1 text-gray-400 hover:text-gray-600 transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Título *</label>
                <input
                  type="text"
                  value={form.titulo}
                  onChange={(e) => setForm((prev) => ({ ...prev, titulo: e.target.value }))}
                  placeholder="Ex: Criar agente IA para Empresa ABC"
                  className="w-full px-4 py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                  autoFocus
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Descrição</label>
                <textarea
                  value={form.descricao}
                  onChange={(e) => setForm((prev) => ({ ...prev, descricao: e.target.value }))}
                  placeholder="Detalhes da tarefa..."
                  rows={2}
                  className="w-full px-4 py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50 resize-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Coluna</label>
                  <select
                    value={form.status}
                    onChange={(e) => setForm((prev) => ({ ...prev, status: e.target.value }))}
                    className="w-full px-4 py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50 bg-white"
                  >
                    <option value="hoje">🔥 Hoje</option>
                    <option value="esta_semana">📅 Esta Semana</option>
                    <option value="depois">📌 Depois</option>
                    <option value="feito">✅ Feito</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Prioridade</label>
                  <select
                    value={form.prioridade}
                    onChange={(e) => setForm((prev) => ({ ...prev, prioridade: e.target.value }))}
                    className="w-full px-4 py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50 bg-white"
                  >
                    <option value="alta">🔴 Alta</option>
                    <option value="media">🟡 Média</option>
                    <option value="baixa">🔵 Baixa</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Prazo</label>
                <input
                  type="date"
                  value={form.prazo}
                  onChange={(e) => setForm((prev) => ({ ...prev, prazo: e.target.value }))}
                  className="w-full px-4 py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Lead (opcional)</label>
                <select
                  value={form.lead_id}
                  onChange={(e) => setForm((prev) => ({ ...prev, lead_id: e.target.value }))}
                  className="w-full px-4 py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50 bg-white"
                >
                  <option value="">Sem lead</option>
                  {leads.map((lead) => (
                    <option key={lead.id} value={lead.id}>
                      {lead.nome}{lead.empresa ? ` — ${lead.empresa}` : ''}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Projeto (opcional)</label>
                <select
                  value={form.project_id}
                  onChange={(e) => setForm((prev) => ({ ...prev, project_id: e.target.value }))}
                  className="w-full px-4 py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50 bg-white"
                >
                  <option value="">Sem projeto</option>
                  {projects.map((project) => (
                    <option key={project.id} value={project.id}>{project.nome}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="flex items-center gap-3 p-6 border-t border-gray-100">
              <button
                onClick={closeModal}
                className="flex-1 px-4 py-2.5 border border-gray-200 text-gray-700 rounded-xl hover:bg-gray-50 transition-colors font-medium"
              >
                Cancelar
              </button>
              <button
                onClick={handleSubmit}
                disabled={submitting || !form.titulo.trim()}
                className="flex-1 px-4 py-2.5 bg-purple-600 text-white rounded-xl hover:bg-purple-700 transition-colors font-medium disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {submitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Salvando...
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="w-4 h-4" />
                    {editingTask ? 'Atualizar' : 'Criar'}
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
