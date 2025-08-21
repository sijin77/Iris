import React, { useState, useEffect } from 'react';
import { 
  Settings, Brain, MessageSquare, Clock, AlertTriangle, 
  Code, Heart, Save, RefreshCw, Download, Upload, 
  ChevronDown, ChevronRight, Plus, Trash2, Edit3, Check 
} from 'lucide-react';

interface AgentSummarizationConfig {
  agent_name: string;
  enabled: boolean;
  chunking_strategy: string;
  max_chunk_size: number;
  min_chunk_size: number;
  overlap_size: number;
  max_context_length: number;
  retrieval_k: number;
  final_k: number;
  thresholds: {
    high_importance: number;
    medium_importance: number;
    min_relevance: number;
    time_gap: number;
  };
  weights: {
    ranking: {
      relevance: number;
      temporal: number;
      importance: number;
    };
    temporal: {
      very_recent: number;
      recent: number;
      medium: number;
      old: number;
    };
    importance: {
      high_keywords: number;
      medium_keywords: number;
      message_length: number;
      question_marks: number;
      exclamation_marks: number;
      caps_ratio: number;
      user_feedback: number;
    };
  };
  patterns: {
    topic_shift: Array<{pattern: string, active: boolean}>;
    questions: Array<{pattern: string, active: boolean}>;
    completion: Array<{pattern: string, active: boolean}>;
    temporal_absolute: Array<{pattern: string, active: boolean}>;
    temporal_relative: Array<{pattern: string, active: boolean}>;
    importance_high: Array<{pattern: string, active: boolean}>;
    importance_medium: Array<{pattern: string, active: boolean}>;
    context_shift: Array<{pattern: string, active: boolean}>;
    technical_context: Array<{pattern: string, active: boolean}>;
    emotional_context: Array<{pattern: string, active: boolean}>;
    dialogue: Record<string, string>;
  };
  user_modes: Record<string, any>;
}

const SummarizationConfig: React.FC = () => {
  const [activeTab, setActiveTab] = useState('basic');
  const [selectedAgent, setSelectedAgent] = useState('Iriska');
  const [config, setConfig] = useState<AgentSummarizationConfig | null>(null);
  const [loading, setLoading] = useState(false);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    basic: true,
    patterns: false,
    weights: false,
    modes: false
  });

  const tabs = [
    { id: 'basic', label: 'Основные параметры', icon: <Settings className="w-5 h-5" /> },
    { id: 'patterns', label: 'Паттерны диалогов', icon: <MessageSquare className="w-5 h-5" /> },
    { id: 'weights', label: 'Веса и пороги', icon: <Brain className="w-5 h-5" /> },
    { id: 'modes', label: 'Режимы пользователя', icon: <Heart className="w-5 h-5" /> }
  ];

  const patternCategories = [
    { key: 'topic_shift', label: 'Смена темы', icon: <MessageSquare className="w-4 h-4" />, color: 'blue' },
    { key: 'questions', label: 'Вопросы', icon: <Brain className="w-4 h-4" />, color: 'green' },
    { key: 'completion', label: 'Завершение', icon: <Check className="w-4 h-4" />, color: 'purple' },
    { key: 'temporal_absolute', label: 'Абсолютное время', icon: <Clock className="w-4 h-4" />, color: 'orange' },
    { key: 'temporal_relative', label: 'Относительное время', icon: <Clock className="w-4 h-4" />, color: 'yellow' },
    { key: 'importance_high', label: 'Высокая важность', icon: <AlertTriangle className="w-4 h-4" />, color: 'red' },
    { key: 'importance_medium', label: 'Средняя важность', icon: <AlertTriangle className="w-4 h-4" />, color: 'amber' },
    { key: 'context_shift', label: 'Смена контекста', icon: <MessageSquare className="w-4 h-4" />, color: 'indigo' },
    { key: 'technical_context', label: 'Технический контекст', icon: <Code className="w-4 h-4" />, color: 'slate' },
    { key: 'emotional_context', label: 'Эмоциональный контекст', icon: <Heart className="w-4 h-4" />, color: 'pink' }
  ];

  const agents = ['Iriska', 'TechAgent', 'SupportAgent', 'ResearchAgent', 'CreativeAgent'];

  useEffect(() => {
    loadConfig();
  }, [selectedAgent]);

  const loadConfig = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/summarization/agents/${selectedAgent}/config`);
      if (response.ok) {
        const data = await response.json();
        setConfig(data);
      }
    } catch (error) {
      console.error('Ошибка загрузки конфигурации:', error);
    } finally {
      setLoading(false);
    }
  };

  const saveConfig = async () => {
    if (!config) return;
    
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/summarization/agents/${selectedAgent}/config`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      
      if (response.ok) {
        // Показать успешное сохранение
        console.log('Конфигурация сохранена');
      }
    } catch (error) {
      console.error('Ошибка сохранения:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleSection = (section: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const addPattern = (category: string) => {
    if (!config) return;
    
    const newPattern = prompt(`Добавить новый паттерн для категории "${category}":`);
    if (newPattern) {
      setConfig({
        ...config,
        patterns: {
          ...config.patterns,
          [category]: [...(config.patterns[category as keyof typeof config.patterns] as Array<{pattern: string, active: boolean}>), {pattern: newPattern, active: true}]
        }
      });
    }
  };

  const removePattern = (category: string, index: number) => {
    if (!config) return;
    
    setConfig({
      ...config,
      patterns: {
        ...config.patterns,
        [category]: (config.patterns[category as keyof typeof config.patterns] as Array<{pattern: string, active: boolean}>).filter((_, i) => i !== index)
      }
    });
  };

  const updatePattern = (category: string, index: number, newValue: string) => {
    if (!config) return;
    
    const patterns = [...(config.patterns[category as keyof typeof config.patterns] as Array<{pattern: string, active: boolean}>)];
    patterns[index] = {...patterns[index], pattern: newValue};
    
    setConfig({
      ...config,
      patterns: {
        ...config.patterns,
        [category]: patterns
      }
    });
  };

  const togglePattern = (category: string, index: number) => {
    if (!config) return;
    
    const patterns = [...(config.patterns[category as keyof typeof config.patterns] as Array<{pattern: string, active: boolean}>)];
    patterns[index] = {...patterns[index], active: !patterns[index].active};
    
    setConfig({
      ...config,
      patterns: {
        ...config.patterns,
        [category]: patterns
      }
    });
  };

  const toggleAllPatterns = (category: string, active: boolean) => {
    if (!config) return;
    
    const patterns = (config.patterns[category as keyof typeof config.patterns] as Array<{pattern: string, active: boolean}>)
      .map(p => ({...p, active}));
    
    setConfig({
      ...config,
      patterns: {
        ...config.patterns,
        [category]: patterns
      }
    });
  };

  const getActivePatternCount = (category: string): number => {
    if (!config) return 0;
    const patterns = config.patterns[category as keyof typeof config.patterns] as Array<{pattern: string, active: boolean}>;
    return patterns?.filter(p => p.active).length || 0;
  };

  const setSmartDefaults = () => {
    if (!config) return;
    
    // Умные настройки по умолчанию - только самые важные паттерны
    const smartDefaults: Record<string, string[]> = {
      topic_shift: [
        "кстати", "другой вопрос", "а еще", "by the way", "speaking of"
      ],
      questions: [
        "как дела", "что думаешь", "можешь помочь", "how are you", "what do you think", "can you help"
      ],
      completion: [
        "понятно", "спасибо", "отлично", "got it", "thanks", "perfect"
      ],
      temporal_absolute: [
        "вчера", "сегодня", "завтра", "yesterday", "today", "tomorrow"
      ],
      temporal_relative: [
        "недавно", "скоро", "потом", "recently", "soon", "later"
      ],
      importance_high: [
        "важно", "срочно", "проблема", "ошибка", "urgent", "critical", "error", "important"
      ],
      importance_medium: [
        "вопрос", "интересно", "думаю", "question", "interesting", "think"
      ],
      context_shift: [
        "однако", "с другой стороны", "however", "on the other hand"
      ],
      technical_context: [
        "код", "ошибка", "программа", "code", "error", "program"
      ],
      emotional_context: [
        "нравится", "хорошо", "плохо", "like", "good", "bad"
      ]
    };

    const updatedPatterns = { ...config.patterns };
    
    Object.keys(updatedPatterns).forEach(category => {
      const patterns = updatedPatterns[category as keyof typeof updatedPatterns] as Array<{pattern: string, active: boolean}>;
      const defaultPatterns = smartDefaults[category] || [];
      
      // Деактивируем все паттерны
      patterns.forEach(p => p.active = false);
      
      // Активируем только те, что входят в умные настройки по умолчанию
      patterns.forEach(p => {
        if (defaultPatterns.some(def => p.pattern.toLowerCase().includes(def.toLowerCase()))) {
          p.active = true;
        }
      });
    });
    
    setConfig({
      ...config,
      patterns: updatedPatterns
    });
  };

  if (loading || !config) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent-500"></div>
        <span className="ml-3 text-primary-600">Загрузка конфигурации...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-primary-900">Настройки суммаризации</h1>
          <p className="text-primary-600 mt-2">Управление паттернами и параметрами диалогов</p>
        </div>
        
        <div className="flex items-center space-x-3">
          <select
            value={selectedAgent}
            onChange={(e) => setSelectedAgent(e.target.value)}
            className="px-3 py-2 border border-primary-300 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent"
          >
            {agents.map(agent => (
              <option key={agent} value={agent}>{agent}</option>
            ))}
          </select>
          
          <button
            onClick={setSmartDefaults}
            className="px-4 py-2 border border-purple-300 text-purple-700 rounded-lg hover:bg-purple-50 transition-colors flex items-center space-x-2"
            title="Активировать только самые важные паттерны"
          >
            <Brain className="w-4 h-4" />
            <span>Умные настройки</span>
          </button>
          
          <button
            onClick={loadConfig}
            className="px-4 py-2 border border-primary-300 text-primary-700 rounded-lg hover:bg-primary-50 transition-colors flex items-center space-x-2"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Обновить</span>
          </button>
          
          <button
            onClick={saveConfig}
            disabled={loading}
            className="px-6 py-2 bg-gradient-to-r from-accent-500 to-accent-600 text-white rounded-lg hover:shadow-medium transition-all duration-200 flex items-center space-x-2 disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            <span>Сохранить</span>
          </button>
        </div>
      </div>

      {/* Agent Status */}
      <div className="bg-white/60 backdrop-blur-sm rounded-xl p-4 border border-primary-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={`w-3 h-3 rounded-full ${config.enabled ? 'bg-success-500' : 'bg-error-500'}`}></div>
            <span className="font-medium text-primary-800">Агент: {selectedAgent}</span>
            <span className="text-sm text-primary-600">
              Стратегия: {config.chunking_strategy} | Контекст: {config.max_context_length} символов
            </span>
          </div>
          
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.enabled}
              onChange={(e) => setConfig({...config, enabled: e.target.checked})}
              className="rounded border-primary-300 text-accent-600 focus:ring-accent-500"
            />
            <span className="text-sm text-primary-700">Включен</span>
          </label>
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
        
        {/* Basic Parameters */}
        {activeTab === 'basic' && (
          <div className="space-y-8">
            <div>
              <h3 className="text-xl font-semibold text-primary-800 mb-6">Основные параметры</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div>
                  <label className="block text-sm font-medium text-primary-700 mb-2">
                    Стратегия чанкинга
                  </label>
                  <select
                    value={config.chunking_strategy}
                    onChange={(e) => setConfig({...config, chunking_strategy: e.target.value})}
                    className="w-full px-3 py-2 border border-primary-300 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent"
                  >
                    <option value="size_based">По размеру</option>
                    <option value="topic_based">По теме</option>
                    <option value="hybrid">Гибридная</option>
                    <option value="importance_based">По важности</option>
                    <option value="context_based">По контексту</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-primary-700 mb-2">
                    Макс. размер чанка
                  </label>
                  <input
                    type="number"
                    value={config.max_chunk_size}
                    onChange={(e) => setConfig({...config, max_chunk_size: parseInt(e.target.value)})}
                    className="w-full px-3 py-2 border border-primary-300 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent"
                    min="100"
                    max="2000"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-primary-700 mb-2">
                    Мин. размер чанка
                  </label>
                  <input
                    type="number"
                    value={config.min_chunk_size}
                    onChange={(e) => setConfig({...config, min_chunk_size: parseInt(e.target.value)})}
                    className="w-full px-3 py-2 border border-primary-300 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent"
                    min="10"
                    max="500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-primary-700 mb-2">
                    Размер пересечения
                  </label>
                  <input
                    type="number"
                    value={config.overlap_size}
                    onChange={(e) => setConfig({...config, overlap_size: parseInt(e.target.value)})}
                    className="w-full px-3 py-2 border border-primary-300 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent"
                    min="0"
                    max="200"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-primary-700 mb-2">
                    Макс. длина контекста
                  </label>
                  <input
                    type="number"
                    value={config.max_context_length}
                    onChange={(e) => setConfig({...config, max_context_length: parseInt(e.target.value)})}
                    className="w-full px-3 py-2 border border-primary-300 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent"
                    min="500"
                    max="10000"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-primary-700 mb-2">
                    Количество документов (K)
                  </label>
                  <div className="flex space-x-2">
                    <input
                      type="number"
                      value={config.retrieval_k}
                      onChange={(e) => setConfig({...config, retrieval_k: parseInt(e.target.value)})}
                      className="w-1/2 px-3 py-2 border border-primary-300 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent"
                      min="1"
                      max="50"
                      placeholder="Retrieval K"
                    />
                    <input
                      type="number"
                      value={config.final_k}
                      onChange={(e) => setConfig({...config, final_k: parseInt(e.target.value)})}
                      className="w-1/2 px-3 py-2 border border-primary-300 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent"
                      min="1"
                      max="20"
                      placeholder="Final K"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Thresholds */}
            <div>
              <h4 className="text-lg font-semibold text-primary-800 mb-4">Пороговые значения</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div>
                  <label className="block text-sm font-medium text-primary-700 mb-2">
                    Высокая важность
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={config.thresholds.high_importance}
                    onChange={(e) => setConfig({
                      ...config,
                      thresholds: {...config.thresholds, high_importance: parseFloat(e.target.value)}
                    })}
                    className="w-full px-3 py-2 border border-primary-300 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent"
                    min="0"
                    max="1"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-primary-700 mb-2">
                    Средняя важность
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={config.thresholds.medium_importance}
                    onChange={(e) => setConfig({
                      ...config,
                      thresholds: {...config.thresholds, medium_importance: parseFloat(e.target.value)}
                    })}
                    className="w-full px-3 py-2 border border-primary-300 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent"
                    min="0"
                    max="1"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-primary-700 mb-2">
                    Мин. релевантность
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={config.thresholds.min_relevance}
                    onChange={(e) => setConfig({
                      ...config,
                      thresholds: {...config.thresholds, min_relevance: parseFloat(e.target.value)}
                    })}
                    className="w-full px-3 py-2 border border-primary-300 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent"
                    min="0"
                    max="1"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-primary-700 mb-2">
                    Временной разрыв (сек)
                  </label>
                  <input
                    type="number"
                    value={config.thresholds.time_gap}
                    onChange={(e) => setConfig({
                      ...config,
                      thresholds: {...config.thresholds, time_gap: parseInt(e.target.value)}
                    })}
                    className="w-full px-3 py-2 border border-primary-300 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent"
                    min="10"
                    max="3600"
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Patterns */}
        {activeTab === 'patterns' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="text-xl font-semibold text-primary-800">Паттерны диалогов</h3>
              <div className="flex items-center space-x-4 text-sm">
                <div className="text-success-600 font-semibold">
                  Активно: {Object.keys(config.patterns).reduce((total, key) => 
                    total + getActivePatternCount(key), 0
                  )}
                </div>
                <div className="text-primary-600">
                  Всего: {Object.values(config.patterns).flat().length}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {patternCategories.map((category) => {
                const patterns = config.patterns[category.key as keyof typeof config.patterns] as Array<{pattern: string, active: boolean}>;
                const isExpanded = expandedSections[category.key];
                const activeCount = getActivePatternCount(category.key);
                const totalCount = patterns?.length || 0;

                return (
                  <div key={category.key} className="border border-primary-200 rounded-lg">
                    <button
                      onClick={() => toggleSection(category.key)}
                      className="w-full flex items-center justify-between p-4 hover:bg-primary-50 transition-colors"
                    >
                      <div className="flex items-center space-x-3">
                        <div className={`p-1 rounded bg-${category.color}-100 text-${category.color}-600`}>
                          {category.icon}
                        </div>
                        <div className="text-left">
                          <h4 className="font-medium text-primary-800">{category.label}</h4>
                          <p className="text-sm text-primary-600">
                            <span className="font-semibold text-success-600">{activeCount}</span> из {totalCount} активны
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                          activeCount > 0 ? 'bg-success-100 text-success-700' : 'bg-gray-100 text-gray-600'
                        }`}>
                          {activeCount > 0 ? 'Включено' : 'Выключено'}
                        </div>
                        {isExpanded ? <ChevronDown className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
                      </div>
                    </button>

                    {isExpanded && (
                      <div className="border-t border-primary-200 p-4 space-y-3">
                        <div className="flex justify-between items-center">
                          <span className="text-sm font-medium text-primary-700">Управление паттернами:</span>
                          <div className="flex items-center space-x-2">
                            <button
                              onClick={() => toggleAllPatterns(category.key, true)}
                              className="text-xs px-2 py-1 bg-success-100 text-success-700 rounded hover:bg-success-200 transition-colors"
                            >
                              Все
                            </button>
                            <button
                              onClick={() => toggleAllPatterns(category.key, false)}
                              className="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded hover:bg-gray-200 transition-colors"
                            >
                              Никого
                            </button>
                            <button
                              onClick={() => addPattern(category.key)}
                              className="flex items-center space-x-1 text-sm text-accent-600 hover:text-accent-700"
                            >
                              <Plus className="w-4 h-4" />
                              <span>Добавить</span>
                            </button>
                          </div>
                        </div>

                        <div className="max-h-80 overflow-y-auto space-y-2">
                          {patterns?.map((patternObj, index) => (
                            <div key={index} className={`flex items-center space-x-2 p-2 rounded group transition-colors ${
                              patternObj.active ? 'bg-success-50 border border-success-200' : 'bg-gray-50 border border-gray-200'
                            }`}>
                              <input
                                type="checkbox"
                                checked={patternObj.active}
                                onChange={() => togglePattern(category.key, index)}
                                className="rounded border-primary-300 text-accent-600 focus:ring-accent-500 flex-shrink-0"
                              />
                              <input
                                type="text"
                                value={patternObj.pattern}
                                onChange={(e) => updatePattern(category.key, index, e.target.value)}
                                className={`flex-1 px-2 py-1 text-sm border rounded focus:ring-1 focus:ring-accent-500 focus:border-transparent ${
                                  patternObj.active 
                                    ? 'border-success-300 bg-white' 
                                    : 'border-gray-300 bg-gray-100 text-gray-600'
                                }`}
                                disabled={!patternObj.active}
                              />
                              <button
                                onClick={() => removePattern(category.key, index)}
                                className="opacity-0 group-hover:opacity-100 text-error-500 hover:text-error-700 transition-opacity flex-shrink-0"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          ))}
                          
                          {(!patterns || patterns.length === 0) && (
                            <div className="text-center py-8 text-gray-500">
                              <MessageSquare className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                              <p className="text-sm">Паттерны не найдены</p>
                              <button
                                onClick={() => addPattern(category.key)}
                                className="text-accent-600 hover:text-accent-700 text-sm mt-2"
                              >
                                Добавить первый паттерн
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Weights */}
        {activeTab === 'weights' && (
          <div className="space-y-8">
            <h3 className="text-xl font-semibold text-primary-800">Веса и коэффициенты</h3>

            {/* Ranking Weights */}
            <div>
              <h4 className="text-lg font-semibold text-primary-800 mb-4">Веса ранжирования</h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-primary-700 mb-2">
                    Релевантность
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={config.weights.ranking.relevance}
                    onChange={(e) => setConfig({
                      ...config,
                      weights: {
                        ...config.weights,
                        ranking: {...config.weights.ranking, relevance: parseFloat(e.target.value)}
                      }
                    })}
                    className="w-full px-3 py-2 border border-primary-300 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent"
                    min="0"
                    max="1"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-primary-700 mb-2">
                    Временной фактор
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={config.weights.ranking.temporal}
                    onChange={(e) => setConfig({
                      ...config,
                      weights: {
                        ...config.weights,
                        ranking: {...config.weights.ranking, temporal: parseFloat(e.target.value)}
                      }
                    })}
                    className="w-full px-3 py-2 border border-primary-300 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent"
                    min="0"
                    max="1"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-primary-700 mb-2">
                    Важность
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={config.weights.ranking.importance}
                    onChange={(e) => setConfig({
                      ...config,
                      weights: {
                        ...config.weights,
                        ranking: {...config.weights.ranking, importance: parseFloat(e.target.value)}
                      }
                    })}
                    className="w-full px-3 py-2 border border-primary-300 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent"
                    min="0"
                    max="1"
                  />
                </div>
              </div>
            </div>

            {/* Temporal Weights */}
            <div>
              <h4 className="text-lg font-semibold text-primary-800 mb-4">Временные веса</h4>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                  <label className="block text-sm font-medium text-primary-700 mb-2">
                    Очень недавно
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={config.weights.temporal.very_recent}
                    onChange={(e) => setConfig({
                      ...config,
                      weights: {
                        ...config.weights,
                        temporal: {...config.weights.temporal, very_recent: parseFloat(e.target.value)}
                      }
                    })}
                    className="w-full px-3 py-2 border border-primary-300 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent"
                    min="0"
                    max="1"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-primary-700 mb-2">
                    Недавно
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={config.weights.temporal.recent}
                    onChange={(e) => setConfig({
                      ...config,
                      weights: {
                        ...config.weights,
                        temporal: {...config.weights.temporal, recent: parseFloat(e.target.value)}
                      }
                    })}
                    className="w-full px-3 py-2 border border-primary-300 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent"
                    min="0"
                    max="1"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-primary-700 mb-2">
                    Средне
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={config.weights.temporal.medium}
                    onChange={(e) => setConfig({
                      ...config,
                      weights: {
                        ...config.weights,
                        temporal: {...config.weights.temporal, medium: parseFloat(e.target.value)}
                      }
                    })}
                    className="w-full px-3 py-2 border border-primary-300 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent"
                    min="0"
                    max="1"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-primary-700 mb-2">
                    Давно
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={config.weights.temporal.old}
                    onChange={(e) => setConfig({
                      ...config,
                      weights: {
                        ...config.weights,
                        temporal: {...config.weights.temporal, old: parseFloat(e.target.value)}
                      }
                    })}
                    className="w-full px-3 py-2 border border-primary-300 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent"
                    min="0"
                    max="1"
                  />
                </div>
              </div>
            </div>

            {/* Importance Weights */}
            <div>
              <h4 className="text-lg font-semibold text-primary-800 mb-4">Веса важности</h4>
              <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {Object.entries(config.weights.importance).map(([key, value]) => (
                  <div key={key}>
                    <label className="block text-sm font-medium text-primary-700 mb-2">
                      {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={value}
                      onChange={(e) => setConfig({
                        ...config,
                        weights: {
                          ...config.weights,
                          importance: {
                            ...config.weights.importance,
                            [key]: parseFloat(e.target.value)
                          }
                        }
                      })}
                      className="w-full px-3 py-2 border border-primary-300 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent"
                      min="0"
                      max="1"
                    />
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* User Modes */}
        {activeTab === 'modes' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="text-xl font-semibold text-primary-800">Пользовательские режимы</h3>
              <div className="text-sm text-primary-600">
                Доступно режимов: {Object.keys(config.user_modes).length}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {Object.entries(config.user_modes).map(([modeName, modeConfig]) => (
                <div key={modeName} className="border border-primary-200 rounded-lg p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="font-semibold text-primary-800 capitalize">{modeName}</h4>
                    <span className="text-xs bg-primary-100 text-primary-600 px-2 py-1 rounded">
                      {(modeConfig as any).chunking_strategy}
                    </span>
                  </div>
                  
                  <p className="text-sm text-primary-600">
                    {(modeConfig as any).description}
                  </p>
                  
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-primary-500">Chunk:</span>
                      <span className="ml-1 font-medium">{(modeConfig as any).max_chunk_size}</span>
                    </div>
                    <div>
                      <span className="text-primary-500">Context:</span>
                      <span className="ml-1 font-medium">{(modeConfig as any).max_context_length}</span>
                    </div>
                    <div>
                      <span className="text-primary-500">Retrieval K:</span>
                      <span className="ml-1 font-medium">{(modeConfig as any).retrieval_k}</span>
                    </div>
                    <div>
                      <span className="text-primary-500">Final K:</span>
                      <span className="ml-1 font-medium">{(modeConfig as any).final_k}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SummarizationConfig;
