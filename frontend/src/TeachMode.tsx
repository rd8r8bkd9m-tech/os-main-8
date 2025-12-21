import { useState } from 'react';

interface TeachResult {
  status: string;
  evolution: {
    best_fitness: number;
    avg_fitness: number;
    generation: number;
  };
  message?: string;
}

export function TeachMode() {
  const [inputText, setInputText] = useState('');
  const [expectedOutput, setExpectedOutput] = useState('');
  const [generations, setGenerations] = useState(10);
  const [result, setResult] = useState<TeachResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleTeach = async () => {
    if (!inputText.trim() || !expectedOutput.trim()) {
      setError('Заполните оба поля');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const url = `http://localhost:8000/api/v1/ai/teach?input_text=${encodeURIComponent(inputText)}&expected_output=${encodeURIComponent(expectedOutput)}&evolve_generations=${generations}`;
      const res = await fetch(url, { method: 'POST' });
      
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }
      
      const data = await res.json();
      setResult(data);
      
      // Очищаем форму после успешного обучения
      setInputText('');
      setExpectedOutput('');
      
    } catch (err) {
      setError(`Ошибка обучения: ${err instanceof Error ? err.message : 'Неизвестная ошибка'}`);
    } finally {
      setLoading(false);
    }
  };

  const examples = [
    { input: 'привет', output: 'Привет! Как я могу помочь?' },
    { input: 'как дела', output: 'Отлично! А у вас?' },
    { input: 'погода', output: 'Сегодня солнечно и тепло' },
    { input: 'спасибо', output: 'Всегда рад помочь!' },
  ];

  const applyExample = (example: { input: string; output: string }) => {
    setInputText(example.input);
    setExpectedOutput(example.output);
  };

  return (
    <div className="animate-fade-in">
      <div className="card" style={{
        background: 'rgba(30, 41, 59, 0.6)',
        backdropFilter: 'blur(12px)',
        border: '1px solid rgba(71, 85, 105, 0.5)',
        marginBottom: '24px'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          marginBottom: '24px'
        }}>
          <span style={{ fontSize: '1.75rem' }}>🎓</span>
          <div>
            <h2 style={{
              fontSize: '1.5rem',
              fontWeight: 700,
              background: 'linear-gradient(135deg, #f59e0b, #d97706)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text'
            }}>
              Режим обучения
            </h2>
            <p style={{ color: '#94a3b8', fontSize: '0.9rem' }}>
              Научите ИИ новым паттернам ответов
            </p>
          </div>
        </div>

        {/* Quick Examples */}
        <div style={{ marginBottom: '24px' }}>
          <p style={{ color: '#94a3b8', fontSize: '0.875rem', marginBottom: '10px' }}>
            Быстрые примеры:
          </p>
          <div style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '8px'
          }}>
            {examples.map((ex, idx) => (
              <button
                key={idx}
                onClick={() => applyExample(ex)}
                style={{
                  padding: '6px 12px',
                  background: 'rgba(51, 65, 85, 0.5)',
                  color: '#94a3b8',
                  border: '1px solid #475569',
                  borderRadius: '8px',
                  fontSize: '0.8rem',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
              >
                {ex.input} → ...
              </button>
            ))}
          </div>
        </div>

        {/* Input Fields */}
        <div style={{ display: 'grid', gap: '20px', marginBottom: '24px' }}>
          <div>
            <label style={{
              display: 'block',
              marginBottom: '8px',
              fontSize: '0.9rem',
              fontWeight: 500,
              color: '#e2e8f0'
            }}>
              Входной текст
            </label>
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Например: привет"
              style={{
                width: '100%',
                padding: '14px 16px',
                borderRadius: '12px',
                border: '1px solid #475569',
                background: '#0f172a',
                color: '#f1f5f9',
                fontSize: '1rem',
                fontFamily: 'inherit',
                boxSizing: 'border-box',
                transition: 'all 0.15s ease'
              }}
            />
          </div>

          <div>
            <label style={{
              display: 'block',
              marginBottom: '8px',
              fontSize: '0.9rem',
              fontWeight: 500,
              color: '#e2e8f0'
            }}>
              Ожидаемый ответ
            </label>
            <input
              type="text"
              value={expectedOutput}
              onChange={(e) => setExpectedOutput(e.target.value)}
              placeholder="Например: Привет! Как я могу помочь?"
              style={{
                width: '100%',
                padding: '14px 16px',
                borderRadius: '12px',
                border: '1px solid #475569',
                background: '#0f172a',
                color: '#f1f5f9',
                fontSize: '1rem',
                fontFamily: 'inherit',
                boxSizing: 'border-box',
                transition: 'all 0.15s ease'
              }}
            />
          </div>

          <div>
            <label style={{
              display: 'flex',
              justifyContent: 'space-between',
              marginBottom: '8px',
              fontSize: '0.9rem',
              fontWeight: 500,
              color: '#e2e8f0'
            }}>
              <span>Поколений эволюции</span>
              <span style={{ 
                color: '#f59e0b',
                fontFamily: 'monospace',
                fontWeight: 600
              }}>
                {generations}
              </span>
            </label>
            <input
              type="range"
              min="1"
              max="50"
              value={generations}
              onChange={(e) => setGenerations(parseInt(e.target.value))}
              style={{
                width: '100%',
                height: '8px',
                borderRadius: '4px',
                background: '#334155',
                cursor: 'pointer',
                WebkitAppearance: 'none',
                appearance: 'none'
              }}
            />
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              fontSize: '0.75rem',
              color: '#64748b',
              marginTop: '6px'
            }}>
              <span>1 — быстро</span>
              <span>50 — глубокое обучение</span>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div style={{
            padding: '12px 16px',
            background: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '10px',
            color: '#ef4444',
            fontSize: '0.9rem',
            marginBottom: '20px'
          }}>
            ⚠️ {error}
          </div>
        )}

        {/* Submit Button */}
        <button
          onClick={handleTeach}
          disabled={loading || !inputText.trim() || !expectedOutput.trim()}
          style={{
            width: '100%',
            padding: '16px 24px',
            background: loading 
              ? '#475569'
              : 'linear-gradient(135deg, #f59e0b, #d97706)',
            color: loading ? '#94a3b8' : '#0f172a',
            border: 'none',
            borderRadius: '12px',
            fontSize: '1.1rem',
            fontWeight: 700,
            cursor: loading ? 'not-allowed' : 'pointer',
            transition: 'all 0.25s ease',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '10px',
            boxShadow: loading ? 'none' : '0 4px 15px rgba(245, 158, 11, 0.3)'
          }}
        >
          {loading ? (
            <>
              <div style={{
                width: '20px',
                height: '20px',
                border: '2px solid rgba(0,0,0,0.2)',
                borderTopColor: '#0f172a',
                borderRadius: '50%',
                animation: 'spin 0.8s linear infinite'
              }} />
              Обучение...
            </>
          ) : (
            <>
              🧬 Научить ИИ
            </>
          )}
        </button>

        {/* Result */}
        {result && (
          <div style={{
            marginTop: '24px',
            padding: '20px',
            background: 'rgba(34, 197, 94, 0.1)',
            border: '1px solid rgba(34, 197, 94, 0.3)',
            borderRadius: '12px',
            animation: 'fadeIn 0.3s ease-out'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              marginBottom: '16px'
            }}>
              <span style={{ fontSize: '1.5rem' }}>✅</span>
              <span style={{ color: '#22c55e', fontWeight: 600, fontSize: '1.1rem' }}>
                {result.status}
              </span>
            </div>
            
            {result.message && (
              <p style={{ color: '#94a3b8', fontSize: '0.9rem', marginBottom: '16px' }}>
                {result.message}
              </p>
            )}
            
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: '12px'
            }}>
              <div style={{
                background: '#0f172a',
                padding: '14px',
                borderRadius: '10px',
                textAlign: 'center'
              }}>
                <div style={{ color: '#64748b', fontSize: '0.75rem', marginBottom: '4px' }}>
                  Лучший фитнес
                </div>
                <div style={{ 
                  color: '#f59e0b', 
                  fontSize: '1.25rem', 
                  fontWeight: 700,
                  fontFamily: 'monospace'
                }}>
                  {(result.evolution.best_fitness * 100).toFixed(2)}%
                </div>
              </div>
              <div style={{
                background: '#0f172a',
                padding: '14px',
                borderRadius: '10px',
                textAlign: 'center'
              }}>
                <div style={{ color: '#64748b', fontSize: '0.75rem', marginBottom: '4px' }}>
                  Средний фитнес
                </div>
                <div style={{ 
                  color: '#10b981', 
                  fontSize: '1.25rem', 
                  fontWeight: 700,
                  fontFamily: 'monospace'
                }}>
                  {(result.evolution.avg_fitness * 100).toFixed(2)}%
                </div>
              </div>
              <div style={{
                background: '#0f172a',
                padding: '14px',
                borderRadius: '10px',
                textAlign: 'center'
              }}>
                <div style={{ color: '#64748b', fontSize: '0.75rem', marginBottom: '4px' }}>
                  Поколение
                </div>
                <div style={{ 
                  color: '#3b82f6', 
                  fontSize: '1.25rem', 
                  fontWeight: 700,
                  fontFamily: 'monospace'
                }}>
                  #{result.evolution.generation}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
