import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

console.log('=== main.tsx загружен ===');
console.log('Document ready state:', document.readyState);

const root = document.getElementById('root');
console.log('Root element:', root);

if (!root) {
  console.error('❌ Root element НЕ НАЙДЕН!');
  document.body.innerHTML = '<h1 style="color:red">ERROR: Root not found</h1>';
  throw new Error('Root element not found');
}

console.log('✓ Root найден, рендерим App...');
ReactDOM.createRoot(root).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
console.log('✓ App отрендерен');
