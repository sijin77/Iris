import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Home from './pages/Home';
import Config from './pages/Config';
import SummarizationConfig from './pages/SummarizationConfig';
import EmotionalMemoryConfig from './pages/EmotionalMemoryConfig';

// Простые тестовые страницы для отладки
const Chat = () => {
  console.log('Chat component rendered');
  return (
    <div className="text-center py-12">
      <h2 className="text-2xl font-bold text-primary-800 mb-4">Чат с Ириской</h2>
      <p className="text-primary-600">Функция чата будет добавлена позже</p>
      <p className="text-sm text-primary-500 mt-4">Компонент Chat загружен успешно</p>
    </div>
  );
};

const Storage = () => {
  console.log('Storage component rendered');
  return (
    <div className="text-center py-12">
      <h2 className="text-2xl font-bold text-primary-800 mb-4">Управление хранилищем</h2>
      <p className="text-primary-600">Функция управления хранилищем будет добавлена позже</p>
      <p className="text-sm text-primary-500 mt-4">Компонент Storage загружен успешно</p>
    </div>
  );
};

// Тестовая страница для проверки роутинга
const TestPage = () => {
  console.log('TestPage component rendered');
  return (
    <div className="text-center py-12">
      <h2 className="text-2xl font-bold text-primary-800 mb-4">Тестовая страница</h2>
      <p className="text-primary-600">Если ты видишь это, значит роутинг работает!</p>
      <p className="text-sm text-primary-500 mt-4">Компонент TestPage загружен успешно</p>
    </div>
  );
};

const App: React.FC = () => {
  console.log('App component rendered');
  
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/config" element={<Config />} />
          <Route path="/summarization" element={<SummarizationConfig />} />
          <Route path="/emotional-memory" element={<EmotionalMemoryConfig />} />
          <Route path="/storage" element={<Storage />} />
          <Route path="/test" element={<TestPage />} />
        </Routes>
      </Layout>
    </Router>
  );
};

export default App;
