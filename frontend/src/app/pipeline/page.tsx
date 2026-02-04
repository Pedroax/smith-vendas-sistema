'use client';

import { useState, useEffect } from 'react';
import {
  DndContext,
  DragEndEvent,
  DragOverlay,
  DragStartEvent,
  PointerSensor,
  useSensor,
  useSensors,
  closestCorners,
  useDroppable,
  useDraggable,
} from '@dnd-kit/core';
import { Plus, Calendar, DollarSign, User, AlertCircle } from 'lucide-react';

// Types
type ProjectStatus = 'backlog' | 'em_andamento' | 'concluido';
type ProjectPriority = 'baixa' | 'media' | 'alta' | 'urgente';

interface Project {
  id: string;
  nome: string;
  descricao?: string;
  cliente_id?: string;
  cliente_nome?: string;
  status: ProjectStatus;
  prioridade: ProjectPriority;
  prazo?: string;
  valor?: number;
  responsavel?: string;
  tags: string[];
  notas?: string;
  progresso_percentual: number;
  created_at: string;
  updated_at: string;
}

// Priority colors
const priorityColors = {
  baixa: 'bg-gray-100 text-gray-700 border-gray-300',
  media: 'bg-blue-100 text-blue-700 border-blue-300',
  alta: 'bg-orange-100 text-orange-700 border-orange-300',
  urgente: 'bg-red-100 text-red-700 border-red-300',
};

const priorityLabels = {
  baixa: 'Baixa',
  media: 'Média',
  alta: 'Alta',
  urgente: 'Urgente',
};

// Column configuration
const columns: { id: ProjectStatus; title: string; color: string }[] = [
  { id: 'backlog', title: 'Backlog', color: 'bg-gray-50 border-gray-200' },
  { id: 'em_andamento', title: 'Em Andamento', color: 'bg-blue-50 border-blue-200' },
  { id: 'concluido', title: 'Concluído', color: 'bg-green-50 border-green-200' },
];

// Draggable Project Card Component
function DraggableProjectCard({ project }: { project: Project }) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: project.id,
    data: project,
  });

  const style = transform
    ? {
        transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`,
        opacity: isDragging ? 0.5 : 1,
      }
    : undefined;

  const isPastDue = project.prazo && new Date(project.prazo) < new Date() && project.status !== 'concluido';

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...listeners}
      {...attributes}
      className={`bg-white rounded-lg border-2 ${priorityColors[project.prioridade]} p-4 shadow-sm hover:shadow-md transition-shadow cursor-move`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-2">
        <h3 className="font-semibold text-gray-900 text-sm">{project.nome}</h3>
        <span className={`text-xs px-2 py-1 rounded-full ${priorityColors[project.prioridade]}`}>
          {priorityLabels[project.prioridade]}
        </span>
      </div>

      {/* Cliente */}
      {project.cliente_nome && (
        <p className="text-xs text-gray-600 mb-2">
          Cliente: {project.cliente_nome}
        </p>
      )}

      {/* Descrição */}
      {project.descricao && (
        <p className="text-xs text-gray-500 mb-3 line-clamp-2">{project.descricao}</p>
      )}

      {/* Metadata */}
      <div className="space-y-1.5">
        {project.responsavel && (
          <div className="flex items-center gap-1.5 text-xs text-gray-600">
            <User className="w-3.5 h-3.5" />
            <span>{project.responsavel}</span>
          </div>
        )}

        {project.prazo && (
          <div className={`flex items-center gap-1.5 text-xs ${isPastDue ? 'text-red-600 font-medium' : 'text-gray-600'}`}>
            {isPastDue && <AlertCircle className="w-3.5 h-3.5" />}
            <Calendar className="w-3.5 h-3.5" />
            <span>{new Date(project.prazo).toLocaleDateString('pt-BR')}</span>
          </div>
        )}

        {project.valor && (
          <div className="flex items-center gap-1.5 text-xs text-gray-600">
            <DollarSign className="w-3.5 h-3.5" />
            <span>R$ {project.valor.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</span>
          </div>
        )}
      </div>

      {/* Progress Bar */}
      {project.progresso_percentual > 0 && (
        <div className="mt-3">
          <div className="flex justify-between items-center mb-1">
            <span className="text-xs text-gray-500">Progresso</span>
            <span className="text-xs font-medium text-gray-700">{project.progresso_percentual}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-1.5">
            <div
              className="bg-blue-600 h-1.5 rounded-full transition-all"
              style={{ width: `${project.progresso_percentual}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
}

// Static Project Card (for overlay)
function ProjectCard({ project }: { project: Project }) {
  const isPastDue = project.prazo && new Date(project.prazo) < new Date() && project.status !== 'concluido';

  return (
    <div className={`bg-white rounded-lg border-2 ${priorityColors[project.prioridade]} p-4 shadow-sm`}>
      <div className="flex items-start justify-between mb-2">
        <h3 className="font-semibold text-gray-900 text-sm">{project.nome}</h3>
        <span className={`text-xs px-2 py-1 rounded-full ${priorityColors[project.prioridade]}`}>
          {priorityLabels[project.prioridade]}
        </span>
      </div>
      {project.cliente_nome && (
        <p className="text-xs text-gray-600 mb-2">Cliente: {project.cliente_nome}</p>
      )}
      {project.descricao && (
        <p className="text-xs text-gray-500 mb-3 line-clamp-2">{project.descricao}</p>
      )}
    </div>
  );
}

// Droppable Kanban Column Component
function DroppableKanbanColumn({
  column,
  projects,
}: {
  column: { id: ProjectStatus; title: string; color: string };
  projects: Project[];
}) {
  const { setNodeRef, isOver } = useDroppable({
    id: column.id,
  });

  return (
    <div className="flex-1 min-w-[320px]">
      <div
        ref={setNodeRef}
        className={`rounded-lg border-2 ${column.color} p-4 transition-all ${isOver ? 'ring-2 ring-blue-500 ring-offset-2' : ''}`}
      >
        {/* Column Header */}
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-gray-900 text-lg">{column.title}</h2>
          <span className="bg-gray-200 text-gray-700 text-xs font-medium px-2.5 py-1 rounded-full">
            {projects.length}
          </span>
        </div>

        {/* Project Cards */}
        <div className="space-y-3 min-h-[400px]">
          {projects.map((project) => (
            <DraggableProjectCard key={project.id} project={project} />
          ))}

          {projects.length === 0 && (
            <div className="text-center text-gray-400 text-sm py-8">
              Nenhum projeto
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function PipelinePage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeProject, setActiveProject] = useState<Project | null>(null);

  // Fetch projects
  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch('http://localhost:8000/api/projects/');

      if (!response.ok) {
        throw new Error('Erro ao buscar projetos');
      }

      const data = await response.json();
      setProjects(data);
    } catch (err) {
      console.error('Erro ao buscar projetos:', err);
      setError(err instanceof Error ? err.message : 'Erro desconhecido');
    } finally {
      setIsLoading(false);
    }
  };

  // Drag and drop sensors
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    })
  );

  // Handle drag start
  const handleDragStart = (event: DragStartEvent) => {
    const { active } = event;
    const project = projects.find((p) => p.id === active.id);
    if (project) {
      setActiveProject(project);
    }
  };

  // Handle drag end
  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;

    setActiveProject(null);

    if (!over) return;

    const projectId = active.id as string;
    const newStatus = over.id as ProjectStatus;

    const project = projects.find((p) => p.id === projectId);
    if (!project || project.status === newStatus) return;

    // Optimistically update UI
    setProjects((prev) =>
      prev.map((p) => (p.id === projectId ? { ...p, status: newStatus } : p))
    );

    // Update backend
    try {
      const response = await fetch(`http://localhost:8000/api/projects/${projectId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: newStatus }),
      });

      if (!response.ok) {
        throw new Error('Erro ao atualizar projeto');
      }

      const updatedProject = await response.json();
      console.log('Projeto atualizado:', updatedProject);
    } catch (err) {
      console.error('Erro ao atualizar projeto:', err);
      // Rollback on error
      setProjects((prev) =>
        prev.map((p) => (p.id === projectId ? project : p))
      );
      alert('Erro ao atualizar projeto. Tente novamente.');
    }
  };

  // Group projects by status
  const projectsByStatus = columns.reduce((acc, column) => {
    acc[column.id] = projects.filter((p) => p.status === column.id);
    return acc;
  }, {} as Record<ProjectStatus, Project[]>);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Carregando projetos...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className="text-gray-900 font-semibold mb-2">Erro ao carregar projetos</p>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={fetchProjects}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Tentar Novamente
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Pipeline de Projetos</h1>
            <p className="text-gray-600 mt-1">Gerencie seus projetos em um quadro Kanban</p>
          </div>
          <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
            <Plus className="w-5 h-5" />
            Novo Projeto
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-4 gap-4 mt-6">
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <p className="text-sm text-gray-600">Total de Projetos</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">{projects.length}</p>
          </div>
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <p className="text-sm text-gray-600">Em Andamento</p>
            <p className="text-2xl font-bold text-blue-600 mt-1">{projectsByStatus.em_andamento.length}</p>
          </div>
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <p className="text-sm text-gray-600">Concluídos</p>
            <p className="text-2xl font-bold text-green-600 mt-1">{projectsByStatus.concluido.length}</p>
          </div>
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <p className="text-sm text-gray-600">Valor Total</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">
              R$ {projects.reduce((sum, p) => sum + (p.valor || 0), 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
            </p>
          </div>
        </div>
      </div>

      {/* Kanban Board */}
      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
      >
        <div className="flex gap-4 overflow-x-auto pb-4">
          {columns.map((column) => (
            <DroppableKanbanColumn key={column.id} column={column} projects={projectsByStatus[column.id]} />
          ))}
        </div>

        {/* Drag Overlay */}
        <DragOverlay>
          {activeProject ? (
            <div className="opacity-50">
              <ProjectCard project={activeProject} />
            </div>
          ) : null}
        </DragOverlay>
      </DndContext>
    </div>
  );
}
