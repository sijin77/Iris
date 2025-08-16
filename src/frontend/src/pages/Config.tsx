import React, { useState } from 'react';
import { Database, HardDrive, Key, Globe, Save, RefreshCw } from 'lucide-react';

const Config: React.FC = () => {
  const [activeTab, setActiveTab] = useState('database');
  const [config, setConfig] = useState({
    database: {
      type: 'sqlite',
      url: 'sqlite:///./data/memory.sqlite',
      path: './data/memory.sqlite'
    },
    vector: {
      type: 'chroma',
      path: './data/chroma_db',
      apiKey: ''
    },
    embeddings: {
      type: 'openai',
      model: 'text-embedding-ada-002',
      apiKey: ''
    }
  });

  const tabs = [
    { id: 'database', label: 'База данных', icon: <Database className="w-5 h-5" /> },
    { id: 'vector', label: 'Векторное хранилище', icon: <HardDrive className="w-5 h-5" /> },
    { id: 'embeddings', label: 'Эмбеддинги', icon: <Key className="w-5 h-5" /> },
    { id: 'general', label: 'Общие настройки', icon: <Globe className="w-5 h-5" /> }
  ];

  const handleSave = () => {
    // TODO: Сохранение конфигурации
    console.log('Сохранение конфигурации:', config);
  };

  const handleReset = () => {
    // TODO: Сброс к значениям по умолчанию
    console.log('Сброс конфигурации');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-primary-900">Настройки системы</h1>
          <p className="text-primary-600 mt-2">Конфигурируйте параметры Ириски</p>
        </div>
        
        <div className="flex space-x-3">
          <button
            onClick={handleReset}
            className="px-4 py-2 border border-primary-300 text-primary-700 rounded-lg hover:bg-primary-50 transition-colors flex items-center space-x-2"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Сброс</span>
          </button>
          <button
            onClick={handleSave}
            className="px-6 py-2 bg-gradient-to-r from-accent-500 to-accent-600 text-white rounded-lg hover:shadow-medium transition-all duration-200 flex items-center space-x-2"
          >
            <Save className="w-4 h-4" />
            <span>Сохранить</span>
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-primary-200">
        <nav className="flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === tab.id
                  ? 'border-accent-500 text-accent-600'
                  : 'border-transparent text-primary-500 hover:text-primary-700 hover:border-primary-300'
              }`}
            >
              {tab.icon}
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-6 border border-primary-200">
        {activeTab === 'database' && (
          <div className="space-y-6">
            <h3 className="text-xl font-semibold text-primary-800">Настройки базы данных</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-primary-700 mb-2">
                  Тип базы данных
                </label>
                <select
                  value={config.database.type}
                  onChange={(e) => setConfig({...config, database: {...config.database, type: e.target.value}})}
                  className="w-full px-3 py-2 border border-primary-300 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent"
                >
                  <option value="sqlite">SQLite</option>
                  <option value="postgresql">PostgreSQL</option>
                  <option value="mysql">MySQL</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-primary-700 mb-2">
                  URL подключения
                </label>
                <input
                  type="text"
                  value={config.database.url}
                  onChange={(e) => setConfig({...config, database: {...config.database, url: e.target.value}})}
                  className="w-full px-3 py-2 border border-primary-300 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent"
                  placeholder="sqlite:///./data/memory.sqlite"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-primary-700 mb-2">
                  Путь к файлу
                </label>
                <input
                  type="text"
                  value={config.database.path}
                  onChange={(e) => setConfig({...config, database: {...config.database, path: e.target.value}})}
                  className="w-full px-3 py-2 border border-primary-300 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent"
                  placeholder="./data/memory.sqlite"
                />
              </div>
            </div>

            <div className="bg-primary-50 rounded-lg p-4">
              <h4 className="font-medium text-primary-800 mb-2">Текущий статус</h4>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-success-500 rounded-full"></div>
                <span className="text-sm text-primary-600">SQLite подключена и работает</span>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'vector' && (
          <div className="space-y-6">
            <h3 className="text-xl font-semibold text-primary-800">Векторное хранилище</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-primary-700 mb-2">
                  Тип хранилища
                </label>
                <select
                  value={config.vector.type}
                  onChange={(e) => setConfig({...config, vector: {...config.vector, type: e.target.value}})}
                  className="w-full px-3 py-2 border border-primary-300 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent"
                >
                  <option value="chroma">ChromaDB</option>
                  <option value="weaviate">Weaviate</option>
                  <option value="pinecone">Pinecone</option>
                  <option value="qdrant">Qdrant</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-primary-700 mb-2">
                  Путь к хранилищу
                </label>
                <input
                  type="text"
                  value={config.vector.path}
                  onChange={(e) => setConfig({...config, vector: {...config.vector, path: e.target.value}})}
                  className="w-full px-3 py-2 border border-primary-300 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent"
                  placeholder="./data/chroma_db"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-primary-700 mb-2">
                  API ключ
                </label>
                <input
                  type="password"
                  value={config.vector.apiKey}
                  onChange={(e) => setConfig({...config, vector: {...config.vector, apiKey: e.target.value}})}
                  className="w-full px-3 py-2 border border-primary-300 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent"
                  placeholder="Введите API ключ"
                />
              </div>
            </div>

            <div className="bg-warning-50 rounded-lg p-4">
              <h4 className="font-medium text-warning-800 mb-2">Внимание</h4>
              <p className="text-sm text-warning-700">
                ChromaDB требует OpenAI API ключ для работы с эмбеддингами
              </p>
            </div>
          </div>
        )}

        {activeTab === 'embeddings' && (
          <div className="space-y-6">
            <h3 className="text-xl font-semibold text-primary-800">Настройки эмбеддингов</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-primary-700 mb-2">
                  Тип эмбеддингов
                </label>
                <select
                  value={config.embeddings.type}
                  onChange={(e) => setConfig({...config, embeddings: {...config.embeddings, type: e.target.value}})}
                  className="w-full px-3 py-2 border border-primary-300 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent"
                >
                  <option value="openai">OpenAI</option>
                  <option value="sentence-transformers">Sentence Transformers</option>
                  <option value="instructor">Instructor</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-primary-700 mb-2">
                  Модель
                </label>
                <input
                  type="text"
                  value={config.embeddings.model}
                  onChange={(e) => setConfig({...config, embeddings: {...config.embeddings, model: e.target.value}})}
                  className="w-full px-3 py-2 border border-primary-300 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent"
                  placeholder="text-embedding-ada-002"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-primary-700 mb-2">
                  OpenAI API ключ
                </label>
                <input
                  type="password"
                  value={config.embeddings.apiKey}
                  onChange={(e) => setConfig({...config, embeddings: {...config.embeddings, apiKey: e.target.value}})}
                  className="w-full px-3 py-2 border border-primary-300 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent"
                  placeholder="sk-..."
                />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'general' && (
          <div className="space-y-6">
            <h3 className="text-xl font-semibold text-primary-800">Общие настройки</h3>
            
            <div className="text-center py-12">
              <Globe className="w-16 h-16 text-primary-400 mx-auto mb-4" />
              <p className="text-primary-600">Общие настройки будут добавлены позже</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Config;
