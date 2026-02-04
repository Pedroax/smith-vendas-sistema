'use client';

import { useState, useEffect, useRef } from 'react';
import { Search, Loader2, Users, Calendar, MessageSquare, Briefcase, X } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useToast } from '@/contexts/ToastContext';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface SearchResult {
  id: string;
  type: 'lead' | 'project' | 'interaction' | 'appointment';
  title: string;
  subtitle: string;
  link: string;
  [key: string]: any;
}

interface SearchResponse {
  query: string;
  total: number;
  results: {
    leads: SearchResult[];
    projects: SearchResult[];
    interactions: SearchResult[];
    appointments: SearchResult[];
  };
}

const typeConfig = {
  lead: { icon: Users, color: 'text-blue-600 bg-blue-50', label: 'Lead' },
  project: { icon: Briefcase, color: 'text-purple-600 bg-purple-50', label: 'Projeto' },
  interaction: { icon: MessageSquare, color: 'text-green-600 bg-green-50', label: 'Interação' },
  appointment: { icon: Calendar, color: 'text-orange-600 bg-orange-50', label: 'Agendamento' },
};

export default function GlobalSearch() {
  const router = useRouter();
  const { showToast } = useToast();

  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);

  const searchRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const debounceRef = useRef<NodeJS.Timeout | undefined>(undefined);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Keyboard shortcut: Ctrl+K or Cmd+K
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        inputRef.current?.focus();
        setShowDropdown(true);
      }

      // ESC to close
      if (e.key === 'Escape') {
        setShowDropdown(false);
        inputRef.current?.blur();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  useEffect(() => {
    if (query.length < 2) {
      setResults(null);
      setShowDropdown(false);
      return;
    }

    // Debounce search
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    debounceRef.current = setTimeout(() => {
      performSearch(query);
    }, 300);

    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [query]);

  const performSearch = async (searchQuery: string) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/search?q=${encodeURIComponent(searchQuery)}`);
      if (res.ok) {
        const data = await res.json();
        setResults(data);
        setShowDropdown(true);
      } else {
        showToast('Erro ao buscar', 'error');
      }
    } catch (err) {
      console.error('Erro na busca:', err);
      showToast('Erro ao buscar', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleResultClick = (result: SearchResult) => {
    router.push(result.link);
    setShowDropdown(false);
    setQuery('');
    setResults(null);
  };

  const handleClear = () => {
    setQuery('');
    setResults(null);
    setShowDropdown(false);
  };

  const allResults = results
    ? [
        ...results.results.leads,
        ...results.results.projects,
        ...results.results.interactions,
        ...results.results.appointments,
      ]
    : [];

  return (
    <div ref={searchRef} className="relative flex-1 max-w-2xl">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => query.length >= 2 && setShowDropdown(true)}
          placeholder="Buscar leads, projetos, clientes... (Ctrl+K)"
          className="w-full pl-10 pr-10 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-transparent"
        />
        {query && (
          <button
            onClick={handleClear}
            className="absolute right-3 top-1/2 -translate-y-1/2 p-1 hover:bg-gray-100 rounded transition-colors"
          >
            <X className="w-4 h-4 text-gray-400" />
          </button>
        )}
        {loading && (
          <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-purple-600 animate-spin" />
        )}
      </div>

      {/* Dropdown Results */}
      {showDropdown && results && (
        <div className="absolute top-full mt-2 w-full bg-white rounded-xl shadow-2xl border border-gray-200 z-50 max-h-96 overflow-y-auto">
          {allResults.length === 0 ? (
            <div className="text-center py-8 px-4">
              <Search className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-sm text-gray-500">Nenhum resultado encontrado para "{query}"</p>
            </div>
          ) : (
            <div className="py-2">
              {/* Header */}
              <div className="px-4 py-2 border-b border-gray-100">
                <p className="text-xs font-semibold text-gray-500">
                  {results.total} resultado{results.total !== 1 ? 's' : ''} encontrado{results.total !== 1 ? 's' : ''}
                </p>
              </div>

              {/* Leads */}
              {results.results.leads.length > 0 && (
                <div>
                  <div className="px-4 py-2">
                    <p className="text-xs font-bold text-gray-400 uppercase">Leads</p>
                  </div>
                  {results.results.leads.map((result) => (
                    <ResultItem
                      key={result.id}
                      result={result}
                      onClick={() => handleResultClick(result)}
                    />
                  ))}
                </div>
              )}

              {/* Projects */}
              {results.results.projects.length > 0 && (
                <div className="border-t border-gray-100">
                  <div className="px-4 py-2">
                    <p className="text-xs font-bold text-gray-400 uppercase">Projetos</p>
                  </div>
                  {results.results.projects.map((result) => (
                    <ResultItem
                      key={result.id}
                      result={result}
                      onClick={() => handleResultClick(result)}
                    />
                  ))}
                </div>
              )}

              {/* Interactions */}
              {results.results.interactions.length > 0 && (
                <div className="border-t border-gray-100">
                  <div className="px-4 py-2">
                    <p className="text-xs font-bold text-gray-400 uppercase">Interações</p>
                  </div>
                  {results.results.interactions.map((result) => (
                    <ResultItem
                      key={result.id}
                      result={result}
                      onClick={() => handleResultClick(result)}
                    />
                  ))}
                </div>
              )}

              {/* Appointments */}
              {results.results.appointments.length > 0 && (
                <div className="border-t border-gray-100">
                  <div className="px-4 py-2">
                    <p className="text-xs font-bold text-gray-400 uppercase">Agendamentos</p>
                  </div>
                  {results.results.appointments.map((result) => (
                    <ResultItem
                      key={result.id}
                      result={result}
                      onClick={() => handleResultClick(result)}
                    />
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

interface ResultItemProps {
  result: SearchResult;
  onClick: () => void;
}

function ResultItem({ result, onClick }: ResultItemProps) {
  const config = typeConfig[result.type];
  const Icon = config.icon;

  return (
    <button
      onClick={onClick}
      className="w-full px-4 py-3 hover:bg-gray-50 transition-colors flex items-start gap-3 text-left"
    >
      <div className={`flex-shrink-0 w-10 h-10 rounded-lg ${config.color} flex items-center justify-center`}>
        <Icon className="w-5 h-5" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <h4 className="text-sm font-semibold text-gray-900 truncate">{result.title}</h4>
          <span className={`px-2 py-0.5 rounded text-xs font-medium ${config.color}`}>
            {config.label}
          </span>
        </div>
        <p className="text-xs text-gray-600 truncate">{result.subtitle}</p>
      </div>
    </button>
  );
}
