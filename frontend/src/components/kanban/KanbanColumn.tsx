'use client';

import { useDroppable } from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable';
import { Lead, LeadStatus } from '@/types/lead';
import { LeadCard } from './LeadCard';

interface KanbanColumnProps {
  id: LeadStatus;
  title: string;
  color: string;
  leads: Lead[];
  count: number;
}

export function KanbanColumn({ id, title, color, leads, count }: KanbanColumnProps) {
  const { setNodeRef } = useDroppable({ id });

  return (
    <div className="flex-shrink-0 w-80">
      {/* Column Header */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-semibold text-gray-900 text-sm flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${color}`}></div>
            {title}
          </h3>
          <span className="bg-gray-100 text-gray-600 text-xs font-medium px-2.5 py-1 rounded-full">
            {count}
          </span>
        </div>
        <div className={`h-1 rounded-full ${color}`}></div>
      </div>

      {/* Cards Container */}
      <div
        ref={setNodeRef}
        className="space-y-3 min-h-[500px] bg-gray-50/50 rounded-xl p-3 border-2 border-dashed border-gray-200"
      >
        <SortableContext items={leads.map(l => l.id)} strategy={verticalListSortingStrategy}>
          {leads.map((lead) => (
            <LeadCard key={lead.id} lead={lead} />
          ))}
        </SortableContext>

        {leads.length === 0 && (
          <div className="flex items-center justify-center h-32 text-gray-400 text-sm">
            Nenhum lead nesta etapa
          </div>
        )}
      </div>
    </div>
  );
}
