'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Bot, Loader2 } from 'lucide-react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export default function LandingPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [leadId, setLeadId] = useState<string | null>(null);
  const [sessionPhone, setSessionPhone] = useState<string | null>(null);
  const [hasStarted, setHasStarted] = useState(false);
  const [showCalendar, setShowCalendar] = useState(false);
  const [calendarUrl, setCalendarUrl] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Reinicializar Calendly quando o widget for ativado
  useEffect(() => {
    if (showCalendar && calendarUrl) {
      console.log('🔄 Reinicializando Calendly widget');
      // Aguardar um pouco para garantir que o DOM está pronto
      setTimeout(() => {
        // @ts-ignore
        if (window.Calendly) {
          console.log('✅ Calendly API disponível');
          // Inicializar widget manualmente
          const widgetElement = document.querySelector('.calendly-inline-widget');
          if (widgetElement) {
            // @ts-ignore
            window.Calendly.initInlineWidget({
              url: calendarUrl,
              parentElement: widgetElement,
            });
            console.log('✅ Calendly widget inicializado manualmente');
          } else {
            console.error('❌ Elemento .calendly-inline-widget não encontrado');
          }
        } else {
          console.warn('⚠️ Calendly API ainda não está disponível');
        }
      }, 500);
    }
  }, [showCalendar, calendarUrl]);

  // Carregar script e CSS do Calendly
  useEffect(() => {
    // Carregar CSS
    const existingCSS = document.querySelector('link[href="https://assets.calendly.com/assets/external/widget.css"]');
    if (!existingCSS) {
      const link = document.createElement('link');
      link.href = 'https://assets.calendly.com/assets/external/widget.css';
      link.rel = 'stylesheet';
      document.head.appendChild(link);
      console.log('✅ CSS do Calendly carregado');
    }

    // Carregar script
    const existingScript = document.querySelector('script[src="https://assets.calendly.com/assets/external/widget.js"]');
    if (!existingScript) {
      const script = document.createElement('script');
      script.src = 'https://assets.calendly.com/assets/external/widget.js';
      script.async = true;
      script.onload = () => {
        console.log('✅ Calendly script carregado com sucesso');
      };
      script.onerror = () => {
        console.error('❌ Erro ao carregar script do Calendly');
      };
      document.body.appendChild(script);
    } else {
      console.log('✅ Script do Calendly já existe no documento');
    }
  }, []);

  // Enviar primeira mensagem automaticamente ao carregar a página
  useEffect(() => {
    if (!hasStarted) {
      setHasStarted(true);
      setTimeout(async () => {
        const randomDigits = Math.floor(Math.random() * 900000000) + 100000000;
        const phone = `5511${randomDigits}`;
        setSessionPhone(phone);

        try {
          const response = await fetch('http://localhost:8000/webhook/whatsapp', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              event: 'messages.upsert',
              source: 'website',
              data: {
                key: {
                  remoteJid: `${phone}@s.whatsapp.net`,
                  fromMe: false,
                  id: `init-${Date.now()}`,
                },
                pushName: 'Lead Landing',
                message: {
                  conversation: '__INIT__',
                },
              },
            }),
          });

          const result = await response.json();

          if (result.status === 'processed') {
            const leadResponse = await fetch(
              `http://localhost:8000/api/leads/${result.lead_id}`
            );
            const lead = await leadResponse.json();

            const welcomeMessage: Message = {
              role: 'assistant',
              content: lead.ultima_mensagem_ia || 'E aí! 👋 Sou o Smith, da AutomateX.\n\nVou te ajudar a descobrir quanto dinheiro você está perdendo por não usar IA no seu negócio.\n\nPra começar, qual seu nome?',
              timestamp: new Date(),
            };
            setMessages([welcomeMessage]);
            setLeadId(result.lead_id);
          }
        } catch (error) {
          console.error('Erro ao iniciar conversa:', error);
          const welcomeMessage: Message = {
            role: 'assistant',
            content: 'E aí! 👋 Sou o Smith, da AutomateX.\n\nVou te ajudar a descobrir quanto dinheiro você está perdendo por não usar IA no seu negócio.\n\nPra começar, qual seu nome?',
            timestamp: new Date(),
          };
          setMessages([welcomeMessage]);
        }
      }, 800);
    }
  }, [hasStarted]);

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
      let phone = sessionPhone;
      if (!phone) {
        const randomDigits = Math.floor(Math.random() * 900000000) + 100000000;
        phone = `5511${randomDigits}`;
        setSessionPhone(phone);
      }

      const response = await fetch('http://localhost:8000/webhook/whatsapp', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          event: 'messages.upsert',
          source: 'website',
          data: {
            key: {
              remoteJid: `${phone}@s.whatsapp.net`,
              fromMe: false,
              id: `test-${Date.now()}`,
            },
            pushName: 'Lead Landing',
            message: {
              conversation: input,
            },
          },
        }),
      });

      const result = await response.json();

      if (result.status === 'processed') {
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

        // Verificar se deve mostrar calendário
        if (result.show_calendar && result.calendar_url) {
          console.log('📅 Ativando calendário:', result.calendar_url);
          setShowCalendar(true);
          setCalendarUrl(result.calendar_url);
        } else {
          console.log('ℹ️ Calendário não ativado - show_calendar:', result.show_calendar, 'calendar_url:', result.calendar_url);
        }
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4">
      {/* Chat Container - Sempre visível */}
      <div className="w-full max-w-md bg-white rounded-2xl shadow-2xl overflow-hidden flex flex-col" style={{ height: '90vh', maxHeight: '800px' }}>
        {/* Chat Header */}
        <div className="bg-gradient-to-r from-purple-600 to-pink-600 p-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-full bg-white/20 flex items-center justify-center">
              <Bot className="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 className="text-white font-semibold text-lg">Smith</h3>
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span className="text-white/90 text-sm">Online</span>
              </div>
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 bg-gray-50">
          {messages.length === 0 && (
            <div className="text-center py-12">
              <Bot className="w-16 h-16 mx-auto mb-4 text-purple-500 animate-bounce" />
              <p className="text-gray-600">Iniciando conversa...</p>
            </div>
          )}

          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex items-start gap-3 mb-4 ${
                message.role === 'user' ? 'flex-row-reverse' : ''
              }`}
            >
              <div
                className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
                  message.role === 'user'
                    ? 'bg-blue-500'
                    : 'bg-purple-500'
                }`}
              >
                {message.role === 'user' ? (
                  <span className="text-white text-sm font-bold">V</span>
                ) : (
                  <Bot className="w-5 h-5 text-white" />
                )}
              </div>

              <div
                className={`flex-1 max-w-[75%] ${
                  message.role === 'user' ? 'text-right' : ''
                }`}
              >
                <div
                  className={`inline-block px-4 py-3 rounded-2xl ${
                    message.role === 'user'
                      ? 'bg-blue-500 text-white rounded-tr-none'
                      : 'bg-white text-gray-900 shadow-md rounded-tl-none border border-gray-200'
                  }`}
                >
                  <p className="whitespace-pre-wrap text-sm leading-relaxed">
                    {message.content}
                  </p>
                </div>
                <p className="text-xs text-gray-500 mt-1 px-2">
                  {message.timestamp.toLocaleTimeString('pt-BR', {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </p>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex items-start gap-3 mb-4">
              <div className="flex-shrink-0 w-10 h-10 rounded-full bg-purple-500 flex items-center justify-center">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div className="bg-white rounded-2xl rounded-tl-none px-4 py-3 shadow-md border border-gray-200">
                <Loader2 className="w-5 h-5 text-purple-500 animate-spin" />
              </div>
            </div>
          )}

          {/* Calendly Widget */}
          {showCalendar && calendarUrl && (
            <div className="my-6 p-4 bg-white rounded-lg shadow-md">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                📅 Agende sua reunião
              </h3>
              <div
                className="calendly-inline-widget"
                data-url={calendarUrl}
                style={{ minWidth: '320px', height: '630px' }}
              ></div>
            </div>
          )}

          {/* Debug - remover depois */}
          {showCalendar && !calendarUrl && (
            <div className="my-4 p-3 bg-red-100 text-red-700 rounded">
              ⚠️ Debug: showCalendar=true mas calendarUrl está vazio
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="border-t p-4 bg-white">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Digite sua mensagem..."
              disabled={isLoading}
              className="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:bg-gray-100 text-gray-900"
            />
            <button
              onClick={sendMessage}
              disabled={!input.trim() || isLoading}
              className="px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-xl hover:from-purple-700 hover:to-pink-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 font-medium transition-all"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
