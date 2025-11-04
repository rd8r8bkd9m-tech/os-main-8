import { useState } from 'react';

interface TeachResult {
  status: string;
  evolution: {
    best_fitness: number;
    avg_fitness: number;
    generation: number;
  };
}

export function TeachMode() {
  const [inputText, setInputText] = useState('');
  const [expectedOutput, setExpectedOutput] = useState('');
  const [generations, setGenerations] = useState(10);
  const [result, setResult] = useState<TeachResult | null>(null);
  const [loading, setLoading] = useState(false);

  const handleTeach = async () => {
    if (!inputText.trim() || !expectedOutput.trim()) return;
    
    setLoading(true);
    try {
      const url = `http://localhost:8000/api/v1/ai/teach?input_text=${encodeURIComponent(inputText)}&expected_output=${encodeURIComponent(expectedOutput)}&evolve_generations=${generations}`;
      const res = await fetch(url, { method: 'POST' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setResult(data);
    } catch (error) {
      alert('Ошибка обучения: ' + String(error));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{background:'#1e293b', borderRadius:'12px', padding:'30px', border:'1px solid #334155'}}>
      <h2 style={{marginBottom:'20px', fontSize:'1.3rem', color:'#fbbf24'}}>🎓 Режим обучения</h2>
      
      <div style={{marginBottom:'20px'}}>
        <label style={{display:'block', marginBottom:'8px', fontSize:'14px', color:'#cbd5e1'}}>
          Входной текст:
        </label>
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Например: hello"
          style={{width:'100%', padding:'10px', borderRadius:'8px', border:'1px solid #475569', background:'#0f172a', color:'#e2e8f0', fontSize:'14px', fontFamily:'monospace', boxSizing:'border-box'}}
        />
      </div>

      <div style={{marginBottom:'20px'}}>
        <label style={{display:'block', marginBottom:'8px', fontSize:'14px', color:'#cbd5e1'}}>
          Ожидаемый результат:
        </label>
        <input
          type="text"
          value={expectedOutput}
          onChange={(e) => setExpectedOutput(e.target.value)}
          placeholder="Например: hi"
          style={{width:'100%', padding:'10px', borderRadius:'8px', border:'1px solid #475569', background:'#0f172a', color:'#e2e8f0', fontSize:'14px', fontFamily:'monospace', boxSizing:'border-box'}}
        />
      </div>

      <div style={{marginBottom:'20px'}}>
        <label style={{display:'block', marginBottom:'8px', fontSize:'14px', color:'#cbd5e1'}}>
          Поколений эволюции: {generations}
        </label>
        <input
          type="range"
          min="1"
          max="50"
          value={generations}
          onChange={(e) => setGenerations(parseInt(e.target.value))}
          style={{width:'100%'}}
        />
        <div style={{display:'flex', justifyContent:'space-between', fontSize:'12px', color:'#94a3b8', marginTop:'5px'}}>
          <span>1 (быстро)</span>
          <span>50 (глубокое обучение)</span>
        </div>
      </div>

      <button
        onClick={handleTeach}
        disabled={loading}
        style={{padding:'12px 24px', background:loading?'#64748b':'#fbbf24', color:'#000', border:'none', borderRadius:'8px', fontSize:'16px', fontWeight:'bold', cursor:loading?'not-allowed':'pointer'}}>
        {loading ? 'Обучение...' : 'Научить AI'}
      </button>

      {result && (
        <div style={{marginTop:'20px', padding:'15px', background:'#0f172a', borderRadius:'8px', border:'1px solid #475569'}}>
          <div style={{color:'#4ade80', marginBottom:'10px'}}>✓ {result.status}</div>
          <div style={{fontSize:'14px', color:'#cbd5e1'}}>
            <div>Лучший фитнес: <span style={{color:'#fbbf24'}}>{result.evolution.best_fitness.toFixed(4)}</span></div>
            <div>Средний фитнес: <span style={{color:'#fbbf24'}}>{result.evolution.avg_fitness.toFixed(4)}</span></div>
            <div>Поколение: <span style={{color:'#fbbf24'}}>{result.evolution.generation}</span></div>
          </div>
        </div>
      )}
    </div>
  );
}
