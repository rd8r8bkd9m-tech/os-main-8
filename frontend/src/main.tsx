import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

const root = document.getElementById('root');

if (!root) {
  document.body.innerHTML = '<div style="padding:40px;text-align:center;color:#ef4444;font-family:system-ui"><h1>Ошибка загрузки</h1><p>Элемент root не найден</p></div>';
  throw new Error('Root element not found');
}

ReactDOM.createRoot(root).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
