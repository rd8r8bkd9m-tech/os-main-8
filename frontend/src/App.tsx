import { useState, useEffect, useRef, useCallback } from 'react';
import { TeachMode } from './TeachMode';
import { Stats } from './Stats';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isError?: boolean;
  metadata?: {
    confidence?: number;
    latency_ms?: number;
    mode?: string;
  };
}

// Иконки как компоненты
const KolibriLogo = () => (
  <svg width="48" height="48" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <linearGradient id="kolibriGrad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#10b981" />
        <stop offset="100%" stopColor="#059669" />
      </linearGradient>
      <linearGradient id="wingGrad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#f59e0b" />
        <stop offset="100%" stopColor="#d97706" />
      </linearGradient>
    </defs>
    {/* Тело колибри */}
    <ellipse cx="50" cy="55" rx="18" ry="25" fill="url(#kolibriGrad)" />
    {/* Голова */}
    <circle cx="50" cy="28" r="14" fill="url(#kolibriGrad)" />
    {/* Клюв */}
    <path d="M50 32 L75 28 L50 24 Z" fill="#374151" />
    {/* Глаз */}
    <circle cx="45" cy="26" r="3" fill="#0f172a" />
    <circle cx="44" cy="25" r="1" fill="white" />
    {/* Крыло */}
    <ellipse cx="35" cy="50" rx="20" ry="8" fill="url(#wingGrad)" transform="rotate(-30, 35, 50)" />
    {/* Хвост */}
    <path d="M42 75 Q50 90 58 75 Q50 82 42 75" fill="url(#kolibriGrad)" />
  </svg>
);

const SendIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="22" y1="2" x2="11" y2="13" />
    <polygon points="22,2 15,22 11,13 2,9" />
  </svg>
);

const LoaderSpinner = () => (
  <div style={{
    width: '20px',
    height: '20px',
    border: '2px solid rgba(255,255,255,0.3)',
    borderTopColor: 'white',
    borderRadius: '50%',
    animation: 'spin 0.8s linear infinite'
  }} />
);

function App() {
  const [showTeachMode, setShowTeachMode] = useState(false);
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + 'px';
    }
  }, [message]);

  const generateId = () => Math.random().toString(36).substring(2, 9);

  const handleSend = async () => {
    if (!message.trim() || loading) return;
    
    const userMessage: Message = {
      id: generateId(),
      role: 'user',
      content: message.trim(),
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    const currentMessage = message.trim();
    setMessage('');
    setLoading(true);
    
    try {
      const result = await fetch('http://localhost:8000/api/v1/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: currentMessage, max_tokens: 1000 }),
      });
      
      if (!result.ok) {
        throw new Error(`Ошибка сервера: ${result.status}`);
      }
      
      const data = await result.json();
      
      const assistantMessage: Message = {
        id: generateId(),
        role: 'assistant',
        content: data.response || data.message || 'Ответ получен',
        timestamp: new Date(),
        metadata: {
          confidence: data.confidence,
          latency_ms: data.latency_ms,
          mode: data.mode
        }
      };
      
      setMessages(prev => [...prev, assistantMessage]);
      
    } catch (error) {
      const errorMessage: Message = {
        id: generateId(),
        role: 'assistant',
        content: `Не удалось получить ответ: ${error instanceof Error ? error.message : 'Неизвестная ошибка'}`,
        timestamp: new Date(),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      handleSend();
    }
  };

  const clearHistory = () => {
    setMessages([]);
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)',
      color: '#f1f5f9'
    }}>
      {/* Background decoration */}
      <div style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'radial-gradient(circle at 20% 20%, rgba(16, 185, 129, 0.1) 0%, transparent 50%), radial-gradient(circle at 80% 80%, rgba(245, 158, 11, 0.08) 0%, transparent 50%)',
        pointerEvents: 'none',
        zIndex: 0
      }} />

      <div className="container" style={{ position: 'relative', zIndex: 1 }}>
        {/* Header */}
        <header style={{
          textAlign: 'center',
          marginBottom: '32px',
          animation: 'fadeIn 0.5s ease-out'
        }}>
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center', 
            gap: '16px',
            marginBottom: '12px'
          }}>
            <div className="animate-float">
              <KolibriLogo />
            </div>
            <h1 style={{ 
              fontSize: '2.5rem', 
              fontWeight: 700,
              background: 'linear-gradient(135deg, #10b981, #f59e0b)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text'
            }}>
              Колибри ИИ
            </h1>
          </div>
          <p style={{ color: '#94a3b8', fontSize: '1.1rem' }}>
            Генеративная система искусственного интеллекта
          </p>
        </header>

        {/* Tab Navigation */}
        <nav style={{
          display: 'flex',
          gap: '12px',
          justifyContent: 'center',
          marginBottom: '32px'
        }}>
          <button
            onClick={() => setShowTeachMode(false)}
            style={{
              padding: '12px 24px',
              background: !showTeachMode 
                ? 'linear-gradient(135deg, #10b981, #059669)' 
                : 'rgba(51, 65, 85, 0.5)',
              color: !showTeachMode ? '#0f172a' : '#94a3b8',
              border: 'none',
              borderRadius: '12px',
              fontSize: '1rem',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.25s ease',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              boxShadow: !showTeachMode ? '0 4px 15px rgba(16, 185, 129, 0.3)' : 'none'
            }}
          >
            💬 Чат
          </button>
          <button
            onClick={() => setShowTeachMode(true)}
            style={{
              padding: '12px 24px',
              background: showTeachMode 
                ? 'linear-gradient(135deg, #f59e0b, #d97706)' 
                : 'rgba(51, 65, 85, 0.5)',
              color: showTeachMode ? '#0f172a' : '#94a3b8',
              border: 'none',
              borderRadius: '12px',
              fontSize: '1rem',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.25s ease',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              boxShadow: showTeachMode ? '0 4px 15px rgba(245, 158, 11, 0.3)' : 'none'
            }}
          >
            🎓 Обучение
          </button>
        </nav>

        {!showTeachMode ? (
          <div className="animate-fade-in">
            {/* Chat Container */}
            <div className="card" style={{
              marginBottom: '24px',
              background: 'rgba(30, 41, 59, 0.6)',
              backdropFilter: 'blur(12px)',
              border: '1px solid rgba(71, 85, 105, 0.5)'
            }}>
              {/* Messages Area */}
              <div style={{
                minHeight: '300px',
                maxHeight: '500px',
                overflowY: 'auto',
                marginBottom: '20px',
                padding: '8px'
              }}>
                {messages.length === 0 ? (
                  <div style={{
                    textAlign: 'center',
                    padding: '60px 20px',
                    color: '#64748b'
                  }}>
                    <div style={{ fontSize: '3rem', marginBottom: '16px' }}>🐦</div>
                    <p style={{ fontSize: '1.1rem', marginBottom: '8px' }}>
                      Начните диалог с Колибри ИИ
                    </p>
                    <p style={{ fontSize: '0.9rem' }}>
                      Введите вопрос и нажмите <kbd style={{
                        background: '#334155',
                        padding: '2px 8px',
                        borderRadius: '4px',
                        fontSize: '0.85rem'
                      }}>Ctrl+Enter</kbd> для отправки
                    </p>
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    {messages.map((msg) => (
                      <div
                        key={msg.id}
                        style={{
                          display: 'flex',
                          justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                          animation: 'fadeIn 0.3s ease-out'
                        }}
                      >
                        <div style={{
                          maxWidth: '80%',
                          padding: '14px 18px',
                          borderRadius: msg.role === 'user' 
                            ? '16px 16px 4px 16px' 
                            : '16px 16px 16px 4px',
                          background: msg.role === 'user'
                            ? 'linear-gradient(135deg, #10b981, #059669)'
                            : msg.isError 
                              ? 'rgba(239, 68, 68, 0.15)'
                              : 'rgba(51, 65, 85, 0.8)',
                          color: msg.role === 'user' ? '#0f172a' : msg.isError ? '#ef4444' : '#f1f5f9',
                          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.2)'
                        }}>
                          <p style={{ 
                            whiteSpace: 'pre-wrap', 
                            wordBreak: 'break-word',
                            lineHeight: 1.6
                          }}>
                            {msg.content}
                          </p>
                          {msg.metadata && (
                            <div style={{
                              marginTop: '10px',
                              paddingTop: '10px',
                              borderTop: '1px solid rgba(255, 255, 255, 0.1)',
                              display: 'flex',
                              gap: '12px',
                              fontSize: '0.75rem',
                              color: '#94a3b8'
                            }}>
                              {msg.metadata.confidence !== undefined && (
                                <span>
                                  Уверенность: {(msg.metadata.confidence * 100).toFixed(1)}%
                                </span>
                              )}
                              {msg.metadata.latency_ms !== undefined && (
                                <span>{msg.metadata.latency_ms.toFixed(0)}ms</span>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                    {loading && (
                      <div style={{
                        display: 'flex',
                        justifyContent: 'flex-start',
                        animation: 'fadeIn 0.3s ease-out'
                      }}>
                        <div style={{
                          padding: '14px 18px',
                          borderRadius: '16px 16px 16px 4px',
                          background: 'rgba(51, 65, 85, 0.8)',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '10px'
                        }}>
                          <LoaderSpinner />
                          <span style={{ color: '#94a3b8' }}>Колибри думает...</span>
                        </div>
                      </div>
                    )}
                    <div ref={messagesEndRef} />
                  </div>
                )}
              </div>

              {/* Input Area */}
              <div style={{
                display: 'flex',
                gap: '12px',
                alignItems: 'flex-end'
              }}>
                <textarea
                  ref={textareaRef}
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Введите ваш вопрос..."
                  rows={1}
                  style={{
                    flex: 1,
                    padding: '14px 16px',
                    borderRadius: '12px',
                    border: '1px solid #475569',
                    background: '#0f172a',
                    color: '#f1f5f9',
                    fontSize: '1rem',
                    fontFamily: 'inherit',
                    resize: 'none',
                    minHeight: '52px',
                    maxHeight: '200px',
                    transition: 'all 0.15s ease'
                  }}
                />
                <button
                  onClick={handleSend}
                  disabled={loading || !message.trim()}
                  style={{
                    padding: '14px 20px',
                    background: loading || !message.trim()
                      ? '#475569'
                      : 'linear-gradient(135deg, #10b981, #059669)',
                    color: loading || !message.trim() ? '#94a3b8' : '#0f172a',
                    border: 'none',
                    borderRadius: '12px',
                    fontSize: '1rem',
                    fontWeight: 600,
                    cursor: loading || !message.trim() ? 'not-allowed' : 'pointer',
                    transition: 'all 0.25s ease',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    boxShadow: loading || !message.trim() 
                      ? 'none' 
                      : '0 4px 15px rgba(16, 185, 129, 0.3)'
                  }}
                >
                  {loading ? <LoaderSpinner /> : <SendIcon />}
                  <span style={{ display: 'none' }}>Отправить</span>
                </button>
              </div>

              {/* Actions */}
              {messages.length > 0 && (
                <div style={{
                  marginTop: '16px',
                  display: 'flex',
                  justifyContent: 'flex-end'
                }}>
                  <button
                    onClick={clearHistory}
                    style={{
                      padding: '8px 16px',
                      background: 'transparent',
                      color: '#64748b',
                      border: '1px solid #334155',
                      borderRadius: '8px',
                      fontSize: '0.875rem',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    Очистить историю
                  </button>
                </div>
              )}
            </div>
          </div>
        ) : (
          <TeachMode />
        )}

        {/* Stats */}
        <Stats />

        {/* Footer */}
        <footer style={{
          marginTop: '40px',
          textAlign: 'center',
          color: '#64748b',
          fontSize: '0.875rem',
          padding: '20px 0',
          borderTop: '1px solid rgba(51, 65, 85, 0.5)'
        }}>
          <div style={{ marginBottom: '8px' }}>
            <span style={{ color: '#10b981' }}>●</span> Backend: <code>localhost:8000</code>
          </div>
          <p>
            Колибри ИИ © 2025 — Кочуров Владислав Евгеньевич
          </p>
        </footer>
      </div>
    </div>
  );
}

export default App;
