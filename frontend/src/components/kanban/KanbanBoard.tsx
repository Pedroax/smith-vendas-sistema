'use client';

import { DndContext, DragEndEvent, DragOverlay, DragStartEvent, PointerSensor, useSensor, useSensors } from '@dnd-kit/core';
import { useState } from 'react';
import { KanbanColumn } from './KanbanColumn';
import { LeadCard } from './LeadCard';
import { useLeadsStore } from '@/store/useLeadsStore';
import { Lead, LeadStatus } from '@/types/lead';

const columns = [
  { id: 'novo' as LeadStatus, title: 'Novo Lead', color: 'bg-blue-500' },
  { id: 'contato_inicial' as LeadStatus, title: 'Contato Inicial', color: 'bg-yellow-500' },
  { id: 'qualificando' as LeadStatus, title: 'Qualificando', color: 'bg-indigo-500' },
  { id: 'qualificado' as LeadStatus, title: 'Qualificado', color: 'bg-purple-500' },
  { id: 'agendamento_marcado' as LeadStatus, title: 'Reunião Agendada', color: 'bg-pink-500' },
  { id: 'ganho' as LeadStatus, title: 'Ganho', color: 'bg-green-500' },
  { id: 'perdido' as LeadStatus, title: 'Perdido', color: 'bg-red-500' },
];

export function KanbanBoard() {
  const { leads, updateLeadStatus } = useLeadsStore();
  const [activeLead, setActiveLead] = useState<Lead | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    })
  );

  const handleDragStart = (event: DragStartEvent) => {
    const lead = leads.find((l) => l.id === event.active.id);
    if (lead) {
      setActiveLead(lead);
    }
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (!over) {
      setActiveLead(null);
      return;
    }

    const leadId = active.id as string;
    const newStatus = over.id as LeadStatus;

    updateLeadStatus(leadId, newStatus);
    setActiveLead(null);
  };

  const getLeadsByStatus = (status: LeadStatus) => {
    return leads.filter((lead) => lead.status === status);
  };

  return (
    <DndContext
      sensors={sensors}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
    >
      <div className="flex gap-6 overflow-x-auto pb-6 px-6">
        {columns.map((column) => {
          const columnLeads = getLeadsByStatus(column.id);
          return (
            <KanbanColumn
              key={column.id}
              id={column.id}
              title={column.title}
              color={column.color}
              leads={columnLeads}
              count={columnLeads.length}
            />
          );
        })}
      </div>

      <DragOverlay>
        {activeLead ? (
          <div className="rotate-3 opacity-90">
            <LeadCard lead={activeLead} />
          </div>
        ) : null}
      </DragOverlay>
    </DndContext>
  );
}
