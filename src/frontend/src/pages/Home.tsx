import React from 'react';
import { Link } from 'react-router-dom';
import { MessageCircle, Settings, Database, Brain, Zap, Shield } from 'lucide-react';

const Home: React.FC = () => {
  const features = [
    {
      icon: <MessageCircle className="w-8 h-8" />,
      title: "Умный Чат",
      description: "Общайтесь с Ириской - digital бунтарем и paradox-партнёром",
      color: "from-accent-500 to-accent-600",
      link: "/chat"
    },
    {
      icon: <Settings className="w-8 h-8" />,
      title: "Настройки",
      description: "Персонализируйте поведение и настройки агента",
      color: "from-primary-500 to-primary-600",
      link: "/config"
    },
    {
      icon: <Database className="w-8 h-8" />,
      title: "Хранилище",
      description: "Управляйте базами данных и векторными хранилищами",
      color: "from-success-500 to-success-600",
      link: "/storage"
    },
    {
      icon: <Brain className="w-8 h-8" />,
      title: "ИИ Модели",
      description: "Настройте LLM и эмбеддинги для лучших результатов",
      color: "from-warning-500 to-warning-600",
      link: "/models"
    },
    {
      icon: <Zap className="w-8 h-8" />,
      title: "Автоматизация",
      description: "Создавайте триггеры и автоматические действия",
      color: "from-error-500 to-error-600",
      link: "/automation"
    },
    {
      icon: <Shield className="w-8 h-8" />,
      title: "Безопасность",
      description: "Настройте правила безопасности и ограничения",
      color: "from-neutral-500 to-neutral-600",
      link: "/security"
    }
  ];

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="text-center space-y-6">
        <div className="flex justify-center">
          <div className="w-20 h-20 bg-gradient-to-br from-accent-500 to-accent-600 rounded-2xl flex items-center justify-center shadow-strong">
            <span className="text-white font-bold text-3xl">И</span>
          </div>
        </div>
        
        <h1 className="text-4xl md:text-5xl font-bold text-primary-900">
          Добро пожаловать в <span className="text-accent-600">Ириску</span>
        </h1>
        
        <p className="text-xl text-primary-600 max-w-3xl mx-auto">
          Digital бунтарь и AI агент для работы и общения
        </p>

        {/* Auth Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <button className="px-8 py-3 bg-gradient-to-r from-accent-500 to-accent-600 text-white rounded-xl font-semibold hover:shadow-medium transition-all duration-200 hover:scale-105">
            Войти через Google
          </button>
          <button className="px-8 py-3 bg-gradient-to-r from-primary-500 to-primary-600 text-white rounded-xl font-semibold hover:shadow-medium transition-all duration-200 hover:scale-105">
            Войти через GitHub
          </button>
        </div>
      </div>

      {/* Features Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {features.map((feature, index) => (
          <Link
            key={index}
            to={feature.link}
            className="group bg-white/60 backdrop-blur-sm rounded-2xl p-6 border border-primary-200 hover:border-primary-300 hover:shadow-medium transition-all duration-300 hover:scale-105 cursor-pointer block"
          >
            <div className={`w-16 h-16 bg-gradient-to-br ${feature.color} rounded-xl flex items-center justify-center text-white mb-4 group-hover:scale-110 transition-transform duration-200`}>
              {feature.icon}
            </div>
            
            <h3 className="text-xl font-semibold text-primary-800 mb-2">
              {feature.title}
            </h3>
            
            <p className="text-primary-600 leading-relaxed">
              {feature.description}
            </p>
          </Link>
        ))}
      </div>

      {/* Quick Stats */}
      <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-6 border border-primary-200">
        <h3 className="text-xl font-semibold text-primary-800 mb-4">Статистика системы</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-accent-600">100%</div>
            <div className="text-sm text-primary-600">Доступность</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-success-600">SQLite</div>
            <div className="text-sm text-primary-600">База данных</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-warning-600">ChromaDB</div>
            <div className="text-sm text-primary-600">Векторное хранилище</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-error-600">Qwen3</div>
            <div className="text-sm text-primary-600">LLM модель</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Home;
