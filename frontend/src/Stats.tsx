import { useState, useEffect } from 'react';

interface AIStats {
  queries_processed: number;
  formula_pool: {
    generation: number;
    examples_count: number;
    best_fitness: number;
    pool_size: number;
  };
}

export function Stats() {
  const [stats, setStats] = useState<AIStats | null>(null);
  const [error, setError] = useState('');

  const fetchStats = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/v1/ai/generative/stats');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setStats(data);
      setError('');
    } catch (err) {
      setError(String(err));
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, []);

  if (error) {
    return (
      <div style={{background:'#dc2626', color:'#fff', padding:'15px', borderRadius:'8px', fontSize:'14px'}}>
        Ошибка загрузки статистики: {error}
      </div>
    );
  }

  if (!stats) {
    return (
      <div style={{background:'#1e293b', padding:'20px', borderRadius:'8px', textAlign:'center', color:'#94a3b8'}}>
        Загрузка статистики...
      </div>
    );
  }

  return (
    <div style={{background:'#1e293b', borderRadius:'12px', padding:'25px', border:'1px solid #334155'}}>
      <h3 style={{marginBottom:'20px', fontSize:'1.2rem', color:'#22c55e'}}>📊 Статистика AI</h3>
      
      <div style={{display:'grid', gridTemplateColumns:'repeat(2, 1fr)', gap:'15px', fontSize:'14px'}}>
        <div style={{background:'#0f172a', padding:'15px', borderRadius:'8px'}}>
          <div style={{color:'#94a3b8', marginBottom:'5px'}}>Поколение</div>
          <div style={{fontSize:'24px', fontWeight:'bold', color:'#4ade80'}}>
            {stats.formula_pool.generation}
          </div>
        </div>

        <div style={{background:'#0f172a', padding:'15px', borderRadius:'8px'}}>
          <div style={{color:'#94a3b8', marginBottom:'5px'}}>Примеров обучения</div>
          <div style={{fontSize:'24px', fontWeight:'bold', color:'#4ade80'}}>
            {stats.formula_pool.examples_count}
          </div>
        </div>

        <div style={{background:'#0f172a', padding:'15px', borderRadius:'8px'}}>
          <div style={{color:'#94a3b8', marginBottom:'5px'}}>Лучший фитнес</div>
          <div style={{fontSize:'24px', fontWeight:'bold', color:'#fbbf24'}}>
            {stats.formula_pool.best_fitness.toFixed(4)}
          </div>
        </div>

        <div style={{background:'#0f172a', padding:'15px', borderRadius:'8px'}}>
          <div style={{color:'#94a3b8', marginBottom:'5px'}}>Размер пула</div>
          <div style={{fontSize:'24px', fontWeight:'bold', color:'#4ade80'}}>
            {stats.formula_pool.pool_size}
          </div>
        </div>
      </div>

      <div style={{marginTop:'15px', padding:'12px', background:'#0f172a', borderRadius:'8px', fontSize:'13px', color:'#cbd5e1'}}>
        Запросов обработано: <span style={{color:'#4ade80', fontWeight:'bold'}}>{stats.queries_processed}</span>
      </div>
    </div>
  );
}
