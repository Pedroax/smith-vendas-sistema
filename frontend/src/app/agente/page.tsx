'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader2, RotateCcw } from 'lucide-react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export default function AgentePage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [leadId, setLeadId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // Usar leadId existente ou criar novo telefone válido para cada sessão
      // Formato: 5511 + 9 dígitos (celular válido do Brasil)
      const randomDigits = Math.floor(Math.random() * 900000000) + 100000000; // 9 dígitos
      const sessionPhone = leadId || `5511${randomDigits}`;

      // Simular mensagem do WhatsApp via webhook
      const response = await fetch('http://localhost:8000/webhook/whatsapp', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          event: 'messages.upsert',
          data: {
            key: {
              remoteJid: `${sessionPhone}@s.whatsapp.net`,
              fromMe: false,
              id: `test-${Date.now()}`,
            },
            pushName: 'Lead Teste',
            message: {
              conversation: input,
            },
          },
        }),
      });

      const result = await response.json();

      if (result.status === 'processed') {
        // Buscar o lead atualizado para pegar a resposta da IA
        const leadResponse = await fetch(
          `http://localhost:8000/api/leads/${result.lead_id}`
        );
        const lead = await leadResponse.json();

        const assistantMessage: Message = {
          role: 'assistant',
          content: lead.ultima_mensagem_ia || 'Sem resposta',
          timestamp: new Date(),
        };

        setMessages((prev) => [...prev, assistantMessage]);
        setLeadId(result.lead_id);
      } else {
        throw new Error('Erro ao processar mensagem');
      }
    } catch (error) {
      console.error('Erro ao enviar mensagem:', error);
      const errorMessage: Message = {
        role: 'assistant',
        content: 'Erro ao processar sua mensagem. Tente novamente.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const resetConversation = () => {
    setMessages([]);
    setLeadId(null);
    setInput('');
  };

  return (
    <div className="p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <h1 className="text-3xl font-bold text-gray-900">
              Teste do Agente Smith
            </h1>
            <button
              onClick={resetConversation}
              className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors"
              title="Começar do zero (nova conversa)"
            >
              <RotateCcw className="w-4 h-4" />
              Resetar Conversa
            </button>
          </div>
          <p className="text-gray-600">
            Converse com o agente de vendas inteligente e veja como ele qualifica leads
          </p>
          {leadId && (
            <p className="text-sm text-gray-500 mt-2">
              Lead ID: <code className="bg-gray-100 px-2 py-1 rounded">{leadId}</code>
            </p>
          )}
        </div>

        {/* Chat Container */}
        <div className="bg-white rounded-lg shadow-lg flex flex-col h-[600px]">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {messages.length === 0 && (
              <div className="text-center text-gray-500 py-12">
                <Bot className="w-12 h-12 mx-auto mb-3 text-gray-400" />
                <p>Inicie uma conversa com o agente Smith</p>
                <p className="text-sm mt-2">
                  Experimente: "Olá, gostaria de saber mais sobre automação com IA"
                </p>
              </div>
            )}

            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex items-start gap-3 ${
                  message.role === 'user' ? 'flex-row-reverse' : ''
                }`}
              >
                <div
                  className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                    message.role === 'user'
                      ? 'bg-blue-500'
                      : 'bg-purple-500'
                  }`}
                >
                  {message.role === 'user' ? (
                    <User className="w-4 h-4 text-white" />
                  ) : (
                    <Bot className="w-4 h-4 text-white" />
                  )}
                </div>

                <div
                  className={`flex-1 max-w-[70%] ${
                    message.role === 'user' ? 'text-right' : ''
                  }`}
                >
                  <div
                    className={`inline-block px-4 py-2 rounded-lg ${
                      message.role === 'user'
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-100 text-gray-900'
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {message.timestamp.toLocaleTimeString('pt-BR', {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </p>
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-purple-500 flex items-center justify-center">
                  <Bot className="w-4 h-4 text-white" />
                </div>
                <div className="bg-gray-100 rounded-lg px-4 py-2">
                  <Loader2 className="w-5 h-5 text-gray-500 animate-spin" />
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="border-t p-4">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Digite sua mensagem..."
                disabled={isLoading}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:bg-gray-100"
              />
              <button
                onClick={sendMessage}
                disabled={!input.trim() || isLoading}
                className="px-6 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                <Send className="w-4 h-4" />
                Enviar
              </button>
            </div>
          </div>
        </div>

        {/* Instructions */}
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-semibold text-blue-900 mb-2">Como testar:</h3>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>1. O agente fará perguntas para qualificar o lead (BANT Framework)</li>
            <li>2. Responda sobre orçamento, autoridade, necessidade e timing</li>
            <li>3. Se qualificado, o agente gerará uma análise de ROI</li>
            <li>4. Acompanhe o status do lead na página de CRM</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
