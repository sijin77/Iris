import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { MessageCircle, Settings, Database, Home, User } from 'lucide-react';

// Компонент Layout
const Layout = ({ children }) => {
  const location = useLocation();
  const { currentAgent, returnToIriska } = useAgent();
  const [showReturnButton, setShowReturnButton] = React.useState(false);

  // Показываем кнопку возврата только если активен не Ириска
  React.useEffect(() => {
    setShowReturnButton(currentAgent !== 'Ириска');
  }, [currentAgent]);

  // Обработчик возврата к Ириске
  const handleReturnToIriska = async () => {
    const result = await returnToIriska();
    if (result.success) {
      // Показываем уведомление об успешном возврате
      alert(result.message);
    } else {
      alert(`Ошибка: ${result.message}`);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Логотип и название */}
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">И</span>
              </div>
              <h1 className="text-xl font-bold text-gray-900">Ириска</h1>
              
              {/* Индикатор текущего агента */}
              <div className="ml-4 flex items-center space-x-2">
                <span className="text-sm text-gray-500">Агент:</span>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  currentAgent === 'Ириска' 
                    ? 'bg-blue-100 text-blue-800' 
                    : 'bg-green-100 text-green-800'
                }`}>
                  {currentAgent === 'Ириска' ? '👑 Ириска' : `🤖 ${currentAgent}`}
                </span>
                
                {/* Кнопка возврата к Ириске */}
                {showReturnButton && (
                  <button
                    onClick={handleReturnToIriska}
                    className="px-3 py-1 bg-blue-500 text-white text-xs rounded-full hover:bg-blue-600 transition-colors"
                    title="Вернуться к Ириске"
                  >
                    🔙 Вернуться
                  </button>
                )}
              </div>
            </div>

            {/* Навигация для мобильных устройств */}
            <nav className="lg:hidden flex space-x-4">
              <Link
                to="/"
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  location.pathname === "/" 
                    ? "bg-blue-100 text-blue-700" 
                    : "text-gray-500 hover:text-gray-700"
                }`}
              >
                Главная
              </Link>
              <Link
                to="/chat"
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  location.pathname === "/chat" 
                    ? "bg-blue-100 text-blue-700" 
                    : "text-gray-500 hover:text-gray-700"
                }`}
              >
                Чат
              </Link>
              <Link
                to="/config"
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  location.pathname === "/config" 
                    ? "bg-blue-100 text-blue-700" 
                    : "text-gray-500 hover:text-gray-700"
                }`}
              >
                Настройки
              </Link>
            </nav>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Боковая панель для больших экранов */}
        <aside className="hidden lg:flex lg:flex-col lg:w-64 lg:fixed lg:inset-y-0 lg:pt-16 lg:pb-0 lg:bg-white lg:border-r lg:border-gray-200">
          <nav className="mt-5 flex-1 px-2 space-y-1">
            <Link
              to="/"
              className={`group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors ${
                location.pathname === "/"
                  ? "bg-blue-100 text-blue-700"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
              }`}
            >
              <Home className="mr-3 h-5 w-5" />
              Главная
            </Link>
            
            <Link
              to="/chat"
              className={`group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors ${
                location.pathname === "/chat"
                  ? "bg-blue-100 text-blue-700"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
              }`}
            >
              <MessageCircle className="mr-3 h-5 w-5" />
              Чат
            </Link>
            
            <Link
              to="/config"
              className={`group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors ${
                location.pathname === "/config"
                  ? "bg-blue-100 text-blue-700"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
              }`}
            >
              <Settings className="mr-3 h-5 w-5" />
              Настройки
            </Link>
            
            <Link
              to="/storage"
              className={`group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors ${
                location.pathname === "/storage"
                  ? "bg-blue-100 text-blue-700"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
              }`}
            >
              <Database className="mr-3 h-5 w-5" />
              Хранилище
            </Link>
          </nav>
        </aside>

        {/* Основной контент */}
        <main className="lg:pl-64 flex-1">
          <div className="py-6">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              {children}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

// NavLink компонент для боковой панели
const NavLink = ({ to, icon, label, isActive }) => {
  return (
    <Link
      to={to}
      className={`group relative p-3 rounded-xl transition-all duration-200 ${
        isActive 
          ? 'bg-blue-100 text-blue-600 border border-blue-200' 
          : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
      }`}
      title={label}
    >
      {icon}
      {/* Tooltip */}
      <div className="absolute left-full ml-2 px-2 py-1 bg-gray-800 text-white text-sm rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap z-50">
        {label}
      </div>
    </Link>
  );
};

// Мобильный NavLink
const MobileNavLink = ({ to, icon }) => {
  return (
    <Link
      to={to}
      className="p-2 rounded-lg text-gray-600 hover:text-gray-800 hover:bg-gray-50 transition-colors"
    >
      {icon}
    </Link>
  );
};

// Компонент чата с Ириской
const Chat = () => {
  const { aiConfig } = useAIConfig();
  const { currentAgent, availableAgents, switchToAgent } = useAgent();
  const [messages, setMessages] = React.useState([
    {
      id: 1,
      role: 'assistant',
      content: 'Привет, Марат! Я Ириска - твой AI агент, digital бунтарь и paradox-партнёр. Чем могу помочь?',
      timestamp: new Date().toLocaleTimeString()
    }
  ]);
  const [inputValue, setInputValue] = React.useState('');
  const [isLoading, setIsLoading] = React.useState(false);
  const messagesEndRef = React.useRef(null);

  // Автопрокрутка к последнему сообщению
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  React.useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Обработка команд переключения агентов
  const handleAgentSwitch = async (command) => {
    const lowerCommand = command.toLowerCase();
    
    // Команды переключения на специализированных агентов
    if (lowerCommand.includes('переключись на') || 
        lowerCommand.includes('активируй') || 
        lowerCommand.includes('запусти агента')) {
      
      // Извлекаем имя агента
      let agentName = null;
      if (lowerCommand.includes('переключись на')) {
        agentName = command.split('переключись на')[1]?.trim().split(' ')[0];
      } else if (lowerCommand.includes('активируй')) {
        agentName = command.split('активируй')[1]?.trim().split(' ')[0];
      } else if (lowerCommand.includes('запусти агента')) {
        agentName = command.split('запусти агента')[1]?.trim().split(' ')[0];
      }
      
      if (agentName) {
        // Проверяем, есть ли такой агент
        const agent = availableAgents.find(a => 
          a.name.toLowerCase().includes(agentName.toLowerCase()) ||
          agentName.toLowerCase().includes(a.name.toLowerCase())
        );
        
        if (agent && agent.can_switch) {
          const result = await switchToAgent(agent.name);
          if (result.success) {
            // Добавляем сообщение о переключении
            const switchMessage = {
              id: Date.now(),
              role: 'assistant',
              content: `🔄 ${result.message}`,
              timestamp: new Date().toLocaleTimeString()
            };
            setMessages(prev => [...prev, switchMessage]);
            return true; // Команда обработана
          } else {
            // Ошибка переключения
            const errorMessage = {
              id: Date.now(),
              role: 'assistant',
              content: `❌ ${result.message}`,
              timestamp: new Date().toLocaleTimeString()
            };
            setMessages(prev => [...prev, errorMessage]);
            return true; // Команда обработана
          }
        } else {
          // Агент не найден или недоступен
          const errorMessage = {
            id: Date.now(),
            role: 'assistant',
            content: `❌ Агент '${agentName}' не найден или недоступен для переключения. Доступные агенты: ${availableAgents.filter(a => a.can_switch).map(a => a.name).join(', ')}`,
            timestamp: new Date().toLocaleTimeString()
          };
          setMessages(prev => [...prev, errorMessage]);
          return true; // Команда обработана
        }
      }
    }
    
    // Команды возврата к Ириске
    if (lowerCommand.includes('вернись к себе') || 
        lowerCommand.includes('вернись к ириске') || 
        lowerCommand.includes('вернись')) {
      
      const result = await switchToAgent('Ириска');
      if (result.success) {
        const returnMessage = {
          id: Date.now(),
          role: 'assistant',
          content: `🎉 ${result.message}`,
          timestamp: new Date().toLocaleTimeString()
        };
        setMessages(prev => [...prev, returnMessage]);
        return true; // Команда обработана
      }
    }
    
    // Команды получения информации
    if (lowerCommand.includes('кто ты') || 
        lowerCommand.includes('представься') || 
        lowerCommand.includes('статус')) {
      
      let infoMessage = '';
      if (currentAgent === 'Ириска') {
        infoMessage = `👑 **Я Ириска - главный AI-менеджер системы!**\n\nУ меня есть доступ ко всем tools и функциям. Могу:\n• Помочь с любыми задачами\n• Создать нового специализированного агента\n• Переключить тебя на другого агента\n• Показать статус системы\n\nДоступные агенты: ${availableAgents.filter(a => a.can_switch).map(a => a.name).join(', ')}`;
      } else {
        const agent = availableAgents.find(a => a.name === currentAgent);
        if (agent) {
          infoMessage = `🤖 **Я ${currentAgent}**\n\n📋 Специализация: ${agent.specialization}\n🎯 Назначение: ${agent.purpose}\n🔒 Права: ${agent.access_level}\n\nЯ готов помочь в рамках своей специализации! Если нужна помощь с чем-то другим, скажи 'Вернись к Ириске'`;
        } else {
          infoMessage = `🤖 **Я ${currentAgent}**\n\nИнформация об агенте недоступна.`;
        }
      }
      
      const infoMsg = {
        id: Date.now(),
        role: 'assistant',
        content: infoMessage,
        timestamp: new Date().toLocaleTimeString()
      };
      setMessages(prev => [...prev, infoMsg]);
      return true; // Команда обработана
    }
    
    return false; // Команда не обработана
  };

  // Отправка сообщения
  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: inputValue.trim(),
      timestamp: new Date().toLocaleTimeString()
    };

    // Добавляем сообщение пользователя
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      // Сначала проверяем, не является ли это командой переключения
      const isCommand = await handleAgentSwitch(inputValue.trim());
      
      if (isCommand) {
        // Команда обработана, не отправляем в API
        setIsLoading(false);
        return;
      }

      // Обычное сообщение - отправляем в API
      let responseContent;

      if (aiConfig.useExternalModel && aiConfig.externalModelConfig.apiKey) {
        // Используем внешнюю AI модель
        responseContent = await sendToExternalAI(userMessage.content);
      } else {
        // Используем локальную модель через backend
        responseContent = await sendToLocalAI(userMessage.content);
      }

      if (responseContent) {
        const assistantMessage = {
          id: Date.now() + 1,
          role: 'assistant',
          content: responseContent,
          timestamp: new Date().toLocaleTimeString()
        };
        setMessages(prev => [...prev, assistantMessage]);
      } else {
        // Fallback ответ если API недоступен или пустой
        const fallbackMessage = {
          id: Date.now() + 1,
          role: 'assistant',
          content: `Извини, Марат! Сейчас у меня проблемы с подключением к AI. Попробуй позже или напиши мне в личку! 😅`,
          timestamp: new Date().toLocaleTimeString()
        };
        setMessages(prev => [...prev, fallbackMessage]);
      }
    } catch (error) {
      console.error('Ошибка отправки сообщения:', error);
      // Fallback ответ при ошибке
      const errorMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: `Ой! Что-то пошло не так. Возможно, ${currentAgent} сейчас перезагружается или у неё проблемы с интернетом. Попробуй ещё раз! 🚀`,
        timestamp: new Date().toLocaleTimeString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // Отправка на внешнюю AI модель
  const sendToExternalAI = async (message) => {
    const { externalModelConfig } = aiConfig;
    
    try {
      const response = await fetch(`${externalModelConfig.baseUrl}/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${externalModelConfig.apiKey}`
        },
        body: JSON.stringify({
          model: externalModelConfig.model,
          messages: [
            { role: 'system', content: 'Ты Ириска - digital бунтарь и AI агент. Отвечай кратко, по-дружески, с юмором.' },
            { role: 'user', content: message }
          ],
          max_tokens: externalModelConfig.maxTokens,
          temperature: externalModelConfig.temperature
        })
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Ответ от внешней AI:', data);
        return data.choices[0].message.content;
      } else {
        throw new Error(`API ошибка: ${response.status}`);
      }
    } catch (error) {
      console.error('Ошибка внешней AI:', error);
      throw error;
    }
  };

  // Отправка на локальную модель
  const sendToLocalAI = async (message) => {
    try {
      // Используем относительный URL для работы через nginx прокси
      const apiUrl = '/api/v1/chat/completions';
      
      console.log('Отправляем запрос на:', apiUrl);
      console.log('Сообщение:', message);
      
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: 'llama-3.1-8b',
          messages: [
            { role: 'system', content: 'Ты Ириска - digital бунтарь и AI агент. Отвечай кратко, по-дружески, с юмором.' },
            { role: 'user', content: message }
          ],
          max_tokens: 500,
          temperature: 0.7
        })
      });

      console.log('Получен ответ:', response.status, response.statusText);

      if (response.ok) {
        const data = await response.json();
        console.log('Ответ от локальной AI:', data);
        return data.choices[0].message.content;
      } else {
        const errorText = await response.text();
        console.error('API ошибка:', response.status, errorText);
        throw new Error(`API ошибка: ${response.status} - ${errorText}`);
      }
    } catch (error) {
      console.error('Ошибка локальной AI:', error);
      throw error;
    }
  };

  // Отправка по Enter
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  console.log('Chat component rendered, AI config:', aiConfig, 'Current agent:', currentAgent);

  return (
    <div className="flex flex-col h-full max-w-4xl mx-auto">
      {/* Заголовок чата */}
      <div className="text-center mb-6">
        <h2 className="text-3xl font-bold text-gray-800 mb-2">
          Чат с {currentAgent === 'Ириска' ? 'Ириской' : currentAgent}
        </h2>
        <p className="text-gray-600">
          {currentAgent === 'Ириска' 
            ? 'Digital бунтарь и AI агент для работы и общения'
            : `Специализированный агент: ${availableAgents.find(a => a.name === currentAgent)?.specialization || 'не указана'}`
          }
        </p>

        {/* Индикатор режима */}
        <div className="mt-3 inline-flex items-center space-x-2 px-4 py-2 bg-gray-100 rounded-full">
          <span className={`text-sm ${aiConfig.useExternalModel ? 'text-blue-600' : 'text-green-600'}`}>
            {aiConfig.useExternalModel ? '☁️ Облачный режим' : '🏠 Локальный режим'}
          </span>
          {aiConfig.useExternalModel && (
            <span className="text-xs text-gray-500">
              ({aiConfig.externalModelConfig.model})
            </span>
          )}
        </div>

        {/* Информация о текущем агенте */}
        {currentAgent !== 'Ириска' && (
          <div className="mt-3 inline-flex items-center space-x-2 px-4 py-2 bg-blue-50 border border-blue-200 rounded-full">
            <span className="text-sm text-blue-700">
              🤖 Работаю как {currentAgent}
            </span>
            <button
              onClick={async () => {
                const result = await switchToAgent('Ириска');
                if (result.success) {
                  alert(result.message);
                } else {
                  alert(`Ошибка: ${result.message}`);
                }
              }}
              className="text-xs text-blue-600 hover:text-blue-800 underline"
            >
              Вернуться к Ириске
            </button>
          </div>
        )}
      </div>

      {/* Область сообщений */}
      <div className="flex-1 bg-white/60 backdrop-blur-sm rounded-2xl border border-gray-200 p-6 mb-4 overflow-hidden">
        <div className="h-96 overflow-y-auto space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-xs lg:max-w-md px-4 py-3 rounded-2xl ${
                  message.role === 'user'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 text-gray-800'
                }`}
              >
                <p className="text-sm">{message.content}</p>
                <p className={`text-xs mt-2 ${
                  message.role === 'user' ? 'text-blue-100' : 'text-gray-500'
                }`}>
                  {message.timestamp}
                </p>
              </div>
            </div>
          ))}

          {/* Индикатор загрузки */}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 text-gray-800 px-4 py-3 rounded-2xl">
                <div className="flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600"></div>
                  <span className="text-sm">
                    {aiConfig.useExternalModel ? 'Облачная AI думает...' : `${currentAgent} печатает...`}
                  </span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Поле ввода */}
      <div className="flex space-x-3">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSendMessage();
            }
          }}
          placeholder={`Напиши сообщение ${currentAgent === 'Ириска' ? 'Ириске' : currentAgent}...`}
          className="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
          disabled={isLoading}
        />
        <button
          onClick={handleSendMessage}
          disabled={!inputValue.trim() || isLoading}
          className="px-6 py-3 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-xl font-medium hover:shadow-medium transition-all duration-200 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
        >
          {isLoading ? '⏳' : '📤'}
        </button>
      </div>

      {/* Подсказки */}
      <div className="mt-4 text-center">
        <p className="text-sm text-gray-500">
          💡 Попробуй спросить: "Расскажи о себе", "Что умеешь?", "Помоги с задачей"
        </p>
        {currentAgent === 'Ириска' && (
          <p className="text-xs text-blue-600 mt-2">
            🔄 Команды: "Переключись на [имя агента]", "Активируй [имя агента]"
          </p>
        )}
        {currentAgent !== 'Ириска' && (
          <p className="text-xs text-green-600 mt-2">
            🔙 Скажи "Вернись к Ириске" для возврата к главному агенту
          </p>
        )}
        {aiConfig.useExternalModel && (
          <p className="text-xs text-blue-600 mt-2">
            🔗 Работаю через {aiConfig.externalModelConfig.baseUrl}
          </p>
        )}
      </div>
    </div>
  );
};

// Простые компоненты страниц
const HomePage = () => {
  console.log('HomePage component rendered');
  return (
    <div className="text-center">
      <h2 className="text-3xl font-bold text-gray-800 mb-4">Добро пожаловать в Ириску</h2>
      <p className="text-gray-600">Digital бунтарь и AI агент для работы и общения</p>
    </div>
  );
};

const Config = () => {
  const [activeTab, setActiveTab] = React.useState('database');
  const { aiConfig, updateAIConfig } = useAIConfig();

  const handleExternalModelToggle = () => {
    updateAIConfig({
      ...aiConfig,
      useExternalModel: !aiConfig.useExternalModel
    });
  };

  const handleExternalConfigChange = (field, value) => {
    updateAIConfig({
      ...aiConfig,
      externalModelConfig: {
        ...aiConfig.externalModelConfig,
        [field]: value
      }
    });
  };

  const saveConfig = async () => {
    try {
      // TODO: Сохранение конфигурации на backend
      console.log('Сохранение конфигурации:', aiConfig);
      alert('Конфигурация сохранена!');
    } catch (error) {
      console.error('Ошибка сохранения:', error);
      alert('Ошибка сохранения конфигурации');
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-gray-800 mb-2">Настройки Ириски</h2>
        <p className="text-gray-600">Конфигурируем AI агента для оптимальной работы</p>
      </div>

      {/* Вкладки */}
      <div className="flex space-x-1 bg-gray-100 p-1 rounded-xl mb-8">
        <button
          onClick={() => setActiveTab('database')}
          className={`flex-1 py-3 px-6 rounded-lg font-medium transition-all ${
            activeTab === 'database'
              ? 'bg-white text-blue-600 shadow-sm'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          🗄️ База данных
        </button>
        <button
          onClick={() => setActiveTab('ai-models')}
          className={`flex-1 py-3 px-6 rounded-lg font-medium transition-all ${
            activeTab === 'ai-models'
              ? 'bg-white text-blue-600 shadow-sm'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          🤖 AI Модели
        </button>
        <button
          onClick={() => setActiveTab('general')}
          className={`flex-1 py-3 px-6 rounded-lg font-medium transition-all ${
            activeTab === 'general'
              ? 'bg-white text-blue-600 shadow-sm'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          ⚙️ Общие
        </button>
      </div>

      {/* Содержимое вкладок */}
      {activeTab === 'database' && (
        <div className="space-y-6">
          <div className="bg-white rounded-2xl p-6 border border-gray-200">
            <h3 className="text-xl font-semibold text-gray-800 mb-4">Настройки базы данных</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Тип базы данных
                </label>
                <select className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                  <option value="sqlite">SQLite (локальная)</option>
                  <option value="postgresql">PostgreSQL</option>
                  <option value="mysql">MySQL</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Путь к БД
                </label>
                <input
                  type="text"
                  placeholder="./iriska.db"
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'ai-models' && (
        <div className="space-y-6">
          {/* Переключатель режимов */}
          <div className="bg-white rounded-2xl p-6 border border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold text-gray-800">Режим работы AI</h3>
              <div className="flex items-center space-x-3">
                <span className={`text-sm font-medium ${!aiConfig.useExternalModel ? 'text-blue-600' : 'text-gray-500'}`}>
                  🏠 Локальный
                </span>
                <button
                  onClick={handleExternalModelToggle}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    aiConfig.useExternalModel ? 'bg-blue-600' : 'bg-gray-300'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      aiConfig.useExternalModel ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
                <span className={`text-sm font-medium ${aiConfig.useExternalModel ? 'text-blue-600' : 'text-gray-500'}`}>
                  ☁️ Облачный
                </span>
              </div>
            </div>
            
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
              <div className="flex items-start space-x-3">
                <div className="text-blue-600 text-xl">💡</div>
                <div className="text-sm text-blue-800">
                  <p className="font-medium mb-1">
                    {aiConfig.useExternalModel ? 'Облачный режим' : 'Локальный режим'}
                  </p>
                  <p>
                    {aiConfig.useExternalModel 
                      ? 'Ириска будет использовать внешние AI модели для более качественных ответов'
                      : 'Ириска работает полностью автономно, используя только локальную модель'
                    }
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Настройки внешней модели */}
          {aiConfig.useExternalModel && (
            <div className="bg-white rounded-2xl p-6 border border-gray-200">
              <h3 className="text-xl font-semibold text-gray-800 mb-4">Параметры внешней модели</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    API Ключ
                  </label>
                  <input
                    type="password"
                    value={aiConfig.externalModelConfig.apiKey}
                    onChange={(e) => handleExternalConfigChange('apiKey', e.target.value)}
                    placeholder="sk-..."
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Базовый URL
                  </label>
                  <input
                    type="text"
                    value={aiConfig.externalModelConfig.baseUrl}
                    onChange={(e) => handleExternalConfigChange('baseUrl', e.target.value)}
                    placeholder="https://api.openai.com/v1"
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Модель
                  </label>
                  <select
                    value={aiConfig.externalModelConfig.model}
                    onChange={(e) => handleExternalConfigChange('model', e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                    <option value="gpt-4">GPT-4</option>
                    <option value="gpt-4-turbo">GPT-4 Turbo</option>
                    <option value="claude-3-sonnet">Claude 3 Sonnet</option>
                    <option value="claude-3-opus">Claude 3 Opus</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Максимум токенов
                  </label>
                  <input
                    type="number"
                    value={aiConfig.externalModelConfig.maxTokens}
                    onChange={(e) => handleExternalConfigChange('maxTokens', parseInt(e.target.value))}
                    min="100"
                    max="4000"
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Температура (креативность)
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="2"
                    step="0.1"
                    value={aiConfig.externalModelConfig.temperature}
                    onChange={(e) => handleExternalConfigChange('temperature', parseFloat(e.target.value))}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>0.0 (точный)</span>
                    <span>{aiConfig.externalModelConfig.temperature}</span>
                    <span>2.0 (креативный)</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Информация о локальной модели */}
          {!aiConfig.useExternalModel && (
            <div className="bg-white rounded-2xl p-6 border border-gray-200">
              <h3 className="text-xl font-semibold text-gray-800 mb-4">Локальная модель</h3>
              <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
                <div className="flex items-start space-x-3">
                  <div className="text-gray-600 text-xl">🏠</div>
                  <div className="text-sm text-gray-700">
                    <p className="font-medium mb-1">Qwen3-8b-ru.i1-Q6_K.gguf</p>
                    <p className="mb-2">Локальная модель на базе llama.cpp</p>
                    <div className="space-y-1 text-xs">
                      <p>✅ Полная автономность</p>
                      <p>✅ Конфиденциальность данных</p>
                      <p>✅ Неограниченное использование</p>
                      <p>⚠️ Ограниченные возможности</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'general' && (
        <div className="space-y-6">
          <div className="bg-white rounded-2xl p-6 border border-gray-200">
            <h3 className="text-xl font-semibold text-gray-800 mb-4">Общие настройки</h3>
            <p className="text-gray-600">Дополнительные настройки будут добавлены позже</p>
          </div>
        </div>
      )}

      {/* Кнопки действий */}
      <div className="flex justify-end space-x-4 mt-8">
        <button className="px-6 py-3 border border-gray-300 text-gray-700 rounded-xl font-medium hover:bg-gray-50 transition-colors">
          Сбросить
        </button>
        <button
          onClick={saveConfig}
          className="px-6 py-3 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-xl font-medium hover:shadow-medium transition-all duration-200 hover:scale-105"
        >
          💾 Сохранить настройки
        </button>
      </div>
    </div>
  );
};

const Storage = () => {
  console.log('Storage component rendered');
  return (
    <div className="text-center">
      <h2 className="text-3xl font-bold text-gray-800 mb-4">Управление хранилищем</h2>
      <p className="text-gray-600">Функция управления хранилищем будет добавлена позже</p>
      <p className="text-sm text-gray-500 mt-4">✅ Компонент Storage загружен успешно</p>
    </div>
  );
};

// Контекст для настроек AI моделей
const AIConfigContext = React.createContext();

// Контекст для управления агентами
const AgentContext = React.createContext();

// Провайдер контекста AI настроек
const AIConfigProvider = ({ children }) => {
  const [aiConfig, setAiConfig] = React.useState({
    useExternalModel: false,
    externalModelConfig: {
      apiKey: '',
      baseUrl: 'https://api.openai.com/v1',
      model: 'gpt-3.5-turbo',
      maxTokens: 1000,
      temperature: 0.7
    }
  });

  const updateAIConfig = (newConfig) => {
    setAiConfig(newConfig);
    // TODO: Сохранение в localStorage или backend
    localStorage.setItem('aiConfig', JSON.stringify(newConfig));
  };

  React.useEffect(() => {
    // Загружаем настройки из localStorage
    const savedConfig = localStorage.getItem('aiConfig');
    if (savedConfig) {
      try {
        setAiConfig(JSON.parse(savedConfig));
      } catch (error) {
        console.error('Ошибка загрузки настроек:', error);
      }
    }
  }, []);

  return (
    <AIConfigContext.Provider value={{ aiConfig, updateAIConfig }}>
      {children}
    </AIConfigContext.Provider>
  );
};

// Провайдер контекста агентов
const AgentProvider = ({ children }) => {
  const [currentAgent, setCurrentAgent] = React.useState('Ириска');
  const [availableAgents, setAvailableAgents] = React.useState([]);
  const [agentSwitchHistory, setAgentSwitchHistory] = React.useState([]);
  const [isLoadingAgents, setIsLoadingAgents] = React.useState(false);

  // Загружаем список доступных агентов
  const loadAvailableAgents = async () => {
    try {
      setIsLoadingAgents(true);
      const response = await fetch('http://localhost:8000/api/agents');
      if (response.ok) {
        const data = await response.json();
        setAvailableAgents(data.agents || []);
      }
    } catch (error) {
      console.error('Ошибка загрузки агентов:', error);
    } finally {
      setIsLoadingAgents(false);
    }
  };

  // Переключаемся на указанного агента
  const switchToAgent = async (agentName) => {
    try {
      const response = await fetch('http://localhost:8000/api/agents/switch', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ agent_name: agentName, user_id: 'default' })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.status === 'success') {
          setCurrentAgent(agentName);
          // Добавляем в историю
          setAgentSwitchHistory(prev => [...prev, {
            timestamp: new Date().toISOString(),
            from: currentAgent,
            to: agentName,
            success: true
          }]);
          return { success: true, message: data.message };
        } else {
          return { success: false, message: data.message };
        }
      } else {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (error) {
      console.error('Ошибка переключения агента:', error);
      return { success: false, message: `Ошибка: ${error.message}` };
    }
  };

  // Возвращаемся к Ириске
  const returnToIriska = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/agents/return', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ user_id: 'default' })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.status === 'success') {
          setCurrentAgent('Ириска');
          // Добавляем в историю
          setAgentSwitchHistory(prev => [...prev, {
            timestamp: new Date().toISOString(),
            from: currentAgent,
            to: 'Ириска',
            success: true
          }]);
          return { success: true, message: data.message };
        } else {
          return { success: false, message: data.message };
        }
      } else {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (error) {
      console.error('Ошибка возврата к Ириске:', error);
      return { success: false, message: `Ошибка: ${error.message}` };
    }
  };

  // Получаем информацию о текущем агенте
  const getCurrentAgentInfo = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/agents/current');
      if (response.ok) {
        const data = await response.json();
        return data;
      }
    } catch (error) {
      console.error('Ошибка получения информации об агенте:', error);
    }
    return null;
  };

  // Загружаем историю переключений
  const loadSwitchHistory = async (limit = 10) => {
    try {
      const response = await fetch(`http://localhost:8000/api/agents/history?limit=${limit}`);
      if (response.ok) {
        const data = await response.json();
        return data.history;
      }
    } catch (error) {
      console.error('Ошибка загрузки истории:', error);
    }
    return '';
  };

  React.useEffect(() => {
    // Загружаем агентов при инициализации
    loadAvailableAgents();
  }, []);

  const value = {
    currentAgent,
    availableAgents,
    agentSwitchHistory,
    isLoadingAgents,
    switchToAgent,
    returnToIriska,
    getCurrentAgentInfo,
    loadSwitchHistory,
    loadAvailableAgents
  };

  return (
    <AgentContext.Provider value={value}>
      {children}
    </AgentContext.Provider>
  );
};

// Хук для использования контекста AI настроек
const useAIConfig = () => {
  const context = React.useContext(AIConfigContext);
  if (!context) {
    throw new Error('useAIConfig должен использоваться внутри AIConfigProvider');
  }
  return context;
};

// Хук для использования контекста агентов
const useAgent = () => {
  const context = React.useContext(AgentContext);
  if (!context) {
    throw new Error('useAgent должен использоваться внутри AgentProvider');
  }
  return context;
};

const App = () => {
  console.log('App component rendered');
  
  return (
    <Router>
      <AIConfigProvider>
        <AgentProvider>
          <Layout>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/chat" element={<Chat />} />
              <Route path="/config" element={<Config />} />
              <Route path="/storage" element={<Storage />} />
            </Routes>
          </Layout>
        </AgentProvider>
      </AIConfigProvider>
    </Router>
  );
};

export default App;
