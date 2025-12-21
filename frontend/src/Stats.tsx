import { useState, useEffect } from 'react';

interface AIStats {
  total_queries?: number;
  queries_processed?: number;
  formula_pool: {
    generation: number;
    examples_count: number;
    best_fitness: number;
    pool_size: number;
    avg_fitness?: number;
  };
  mode?: string;
  auto_learn_enabled?: boolean;
  pending_learning_queue?: number;
}

export function Stats() {
  const [stats, setStats] = useState<AIStats | null>(null);
  const [error, setError] = useState('');
  const [isCollapsed, setIsCollapsed] = useState(false);

  const fetchStats = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/v1/ai/generative/stats');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setStats(data);
      setError('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка загрузки');
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, []);

  if (error) {
    return (
      <div className="card" style={{
        background: 'rgba(239, 68, 68, 0.1)',
        border: '1px solid rgba(239, 68, 68, 0.3)'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          color: '#ef4444'
        }}>
          <span>⚠️</span>
          <span>Статистика недоступна: {error}</span>
          <button
            onClick={fetchStats}
            style={{
              marginLeft: 'auto',
              padding: '6px 12px',
              background: 'transparent',
              border: '1px solid #ef4444',
              borderRadius: '6px',
              color: '#ef4444',
              cursor: 'pointer',
              fontSize: '0.8rem'
            }}
          >
            Повторить
          </button>
        </div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="card" style={{
        background: 'rgba(30, 41, 59, 0.6)',
        backdropFilter: 'blur(12px)',
        border: '1px solid rgba(71, 85, 105, 0.5)'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '10px',
          padding: '20px',
          color: '#94a3b8'
        }}>
          <div style={{
            width: '20px',
            height: '20px',
            border: '2px solid #475569',
            borderTopColor: '#10b981',
            borderRadius: '50%',
            animation: 'spin 0.8s linear infinite'
          }} />
          <span>Загрузка статистики...</span>
        </div>
      </div>
    );
  }

  const statItems = [
    {
      label: 'Поколение',
      value: stats.formula_pool.generation,
      color: '#10b981',
      icon: '🧬'
    },
    {
      label: 'Примеров',
      value: stats.formula_pool.examples_count,
      color: '#3b82f6',
      icon: '📚'
    },
    {
      label: 'Лучший фитнес',
      value: `${(stats.formula_pool.best_fitness * 100).toFixed(1)}%`,
      color: '#f59e0b',
      icon: '🏆'
    },
    {
      label: 'Размер пула',
      value: stats.formula_pool.pool_size,
      color: '#8b5cf6',
      icon: '🔬'
    }
  ];

  return (
    <div className="card" style={{
      background: 'rgba(30, 41, 59, 0.6)',
      backdropFilter: 'blur(12px)',
      border: '1px solid rgba(71, 85, 105, 0.5)',
      transition: 'all 0.25s ease'
    }}>
      {/* Header */}
      <button
        onClick={() => setIsCollapsed(!isCollapsed)}
        style={{
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'transparent',
          border: 'none',
          cursor: 'pointer',
          padding: 0
        }}
      >
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px'
        }}>
          <span style={{ fontSize: '1.5rem' }}>📊</span>
          <h3 style={{
            fontSize: '1.25rem',
            fontWeight: 600,
            color: '#10b981'
          }}>
            Статистика ИИ
          </h3>
          {stats.auto_learn_enabled && (
            <span style={{
              padding: '3px 8px',
              background: 'rgba(34, 197, 94, 0.2)',
              color: '#22c55e',
              borderRadius: '6px',
              fontSize: '0.7rem',
              fontWeight: 600,
              textTransform: 'uppercase'
            }}>
              Авто-обучение
            </span>
          )}
        </div>
        <span style={{
          color: '#64748b',
          fontSize: '1.5rem',
          transform: isCollapsed ? 'rotate(-90deg)' : 'rotate(0)',
          transition: 'transform 0.2s ease'
        }}>
          ▼
        </span>
      </button>

      {/* Content */}
      {!isCollapsed && (
        <div style={{
          marginTop: '20px',
          animation: 'fadeIn 0.2s ease-out'
        }}>
          {/* Stats Grid */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
            gap: '12px',
            marginBottom: '16px'
          }}>
            {statItems.map((item, idx) => (
              <div
                key={idx}
                style={{
                  background: 'rgba(15, 23, 42, 0.8)',
                  padding: '16px',
                  borderRadius: '12px',
                  textAlign: 'center',
                  border: '1px solid rgba(71, 85, 105, 0.3)',
                  transition: 'all 0.2s ease'
                }}
              >
                <div style={{ fontSize: '1.5rem', marginBottom: '8px' }}>
                  {item.icon}
                </div>
                <div style={{
                  fontSize: '1.5rem',
                  fontWeight: 700,
                  color: item.color,
                  fontFamily: 'monospace',
                  marginBottom: '4px'
                }}>
                  {item.value}
                </div>
                <div style={{
                  fontSize: '0.75rem',
                  color: '#64748b',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em'
                }}>
                  {item.label}
                </div>
              </div>
            ))}
          </div>

          {/* Additional Info */}
          <div style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '16px',
            padding: '14px',
            background: 'rgba(15, 23, 42, 0.5)',
            borderRadius: '10px',
            fontSize: '0.85rem'
          }}>
            {stats.total_queries !== undefined && (
              <div>
                <span style={{ color: '#64748b' }}>Запросов:</span>{' '}
                <span style={{ color: '#10b981', fontWeight: 600 }}>
                  {stats.total_queries}
                </span>
              </div>
            )}
            {stats.formula_pool.avg_fitness !== undefined && (
              <div>
                <span style={{ color: '#64748b' }}>Средний фитнес:</span>{' '}
                <span style={{ color: '#f59e0b', fontWeight: 600 }}>
                  {(stats.formula_pool.avg_fitness * 100).toFixed(1)}%
                </span>
              </div>
            )}
            {stats.pending_learning_queue !== undefined && stats.pending_learning_queue > 0 && (
              <div>
                <span style={{ color: '#64748b' }}>В очереди обучения:</span>{' '}
                <span style={{ color: '#3b82f6', fontWeight: 600 }}>
                  {stats.pending_learning_queue}
                </span>
              </div>
            )}
            <div style={{ marginLeft: 'auto' }}>
              <span style={{ color: '#64748b' }}>Режим:</span>{' '}
              <span style={{ color: '#8b5cf6', fontWeight: 600 }}>
                {stats.mode || 'generative_decimal'}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
