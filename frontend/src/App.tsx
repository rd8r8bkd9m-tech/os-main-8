import { useState, useEffect } from 'react';
import { TeachMode } from './TeachMode';
import { Stats } from './Stats';

function App() {
  const [showTeachMode, setShowTeachMode] = useState(false);
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);
  const [pendingResponse, setPendingResponse] = useState<string | null>(null);

  // Следим когда pendingResponse меняется - обновляем response
  useEffect(() => {
    if (pendingResponse !== null) {
      console.log('⚡ useEffect: Обновляю response state');
      setResponse(pendingResponse);
      setPendingResponse(null);
    }
  }, [pendingResponse]);

  const handleSend = async () => {
    if (!message.trim()) return;
    setLoading(true);
    setResponse('⏳ Обработка запроса...');
    
    try {
      const result = await fetch('http://localhost:8000/api/v1/ai/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({prompt: message, max_tokens: 1000}),
      });
      
      if (!result.ok) {
        throw new Error(`Ошибка ${result.status}`);
      }
      
      const data = await result.json();
      
      // Используем pendingResponse для гарантированного обновления
      setPendingResponse(data.message);
      
    } catch (error) {
      console.error('❌ Ошибка:', error);
      setResponse('❌ Ошибка подключения к API\n\n' + String(error));
    } finally {
      setLoading(false);
      setMessage('');
    }
  };

  return (
    <div style={{minHeight:'100vh', background:'#0f172a', color:'#e2e8f0'}}>
      <div style={{maxWidth:'900px', margin:'0 auto', padding:'40px 20px'}}>
        <h1 style={{fontSize:'2.5rem', marginBottom:'20px', textAlign:'center'}}>
          🐦 Колибри ИИ — Генеративная Система
        </h1>

        <div style={{display:'flex', gap:'10px', marginBottom:'30px', justifyContent:'center'}}>
          <button
            onClick={() => setShowTeachMode(false)}
            style={{padding:'10px 20px', background:!showTeachMode?'#22c55e':'#334155', color:!showTeachMode?'#000':'#94a3b8', border:'none', borderRadius:'8px', fontSize:'14px', fontWeight:'bold', cursor:'pointer'}}>
            💬 Чат
          </button>
          <button
            onClick={() => setShowTeachMode(true)}
            style={{padding:'10px 20px', background:showTeachMode?'#fbbf24':'#334155', color:showTeachMode?'#000':'#94a3b8', border:'none', borderRadius:'8px', fontSize:'14px', fontWeight:'bold', cursor:'pointer'}}>
            🎓 Обучение
          </button>
        </div>

        {!showTeachMode ? (
          <>
            <div style={{background:'#1e293b', borderRadius:'12px', padding:'30px', marginBottom:'30px', border:'1px solid #334155'}}>
              <h2 style={{marginBottom:'20px', fontSize:'1.3rem'}}>Запросить AI</h2>
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Введите ваш вопрос..."
                style={{width:'100%', padding:'12px', borderRadius:'8px', border:'1px solid #475569', background:'#0f172a', color:'#e2e8f0', fontSize:'14px', minHeight:'100px', fontFamily:'monospace', boxSizing:'border-box'}}
              />
              <button
                onClick={handleSend}
                disabled={loading}
                style={{marginTop:'15px', padding:'12px 24px', background:loading?'#64748b':'#22c55e', color:loading?'#cbd5e1':'#000', border:'none', borderRadius:'8px', fontSize:'16px', fontWeight:'bold', cursor:loading?'not-allowed':'pointer'}}>
                {loading ? 'Обработка...' : 'Отправить'}
              </button>
            </div>

            {response && (
              <div style={{background:'#1e293b', borderRadius:'12px', padding:'30px', marginBottom:'30px', border:'1px solid #334155'}}>
                <h2 style={{marginBottom:'20px', fontSize:'1.3rem'}}>🤖 Ответ AI:</h2>
                {response.includes('❌') ? (
                  <div style={{background:'#0f172a', padding:'20px', borderRadius:'8px', color:'#ef4444', fontSize:'15px', lineHeight:'1.6', whiteSpace:'pre-wrap', wordBreak:'break-word'}}>
                    {response}
                  </div>
                ) : response.includes('⏳') ? (
                  <div style={{background:'#0f172a', padding:'20px', borderRadius:'8px', color:'#f59e0b', fontSize:'15px', lineHeight:'1.6', whiteSpace:'pre-wrap', wordBreak:'break-word'}}>
                    {response}
                  </div>
                ) : (
                  <div style={{background:'#0f172a', padding:'20px', borderRadius:'8px', color:'#4ade80', fontSize:'15px', lineHeight:'1.6', whiteSpace:'pre-wrap', wordBreak:'break-word'}}>
                    {response}
                  </div>
                )}
              </div>
            )}
          </>
        ) : (
          <TeachMode />
        )}

        <Stats />

        <div style={{marginTop:'40px', textAlign:'center', color:'#94a3b8', fontSize:'14px'}}>
          <p>Backend: <code>http://localhost:8000</code></p>
          <p>Режим: <span style={{color:'#4ade80'}}>✓ Generative Decimal AI</span></p>
        </div>
      </div>
    </div>
  );
}

export default App;
