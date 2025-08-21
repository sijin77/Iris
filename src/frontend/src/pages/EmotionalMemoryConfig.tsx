import React, { useState, useEffect } from 'react';
import { 
  Brain, Heart, Zap, Settings, Save, RefreshCw, 
  ChevronDown, ChevronRight, Plus, Trash2, Edit3,
  Activity, Target, Clock, Sliders
} from 'lucide-react';

interface EmotionalMemoryConfig {
  agent_name: string;
  emotion_triggers: {
    joy_triggers: Record<string, number>;
    sadness_triggers: Record<string, number>;
    anger_triggers: Record<string, number>;
    fear_triggers: Record<string, number>;
    surprise_triggers: Record<string, number>;
    disgust_triggers: Record<string, number>;
    trust_triggers: Record<string, number>;
    anticipation_triggers: Record<string, number>;
  };
  neuromodulator_settings: {
    base_levels: Record<string, number>;
    activation_thresholds: Record<string, number>;
    half_life_minutes: Record<string, number>;
    modulation_effects: Record<string, Record<string, number>>;
    activation_conditions: Record<string, any>;
  };
  emotion_analysis_config: {
    intensity_modifiers: Record<string, number>;
    negation_words: Record<string, string[]>;
    amplifiers: Record<string, string[]>;
    diminishers: Record<string, string[]>;
    emotion_mapping: Record<string, any>;
    intensity_thresholds: Record<string, number>;
    context_analysis: Record<string, number>;
    history_settings: Record<string, number>;
  };
}

const EmotionalMemoryConfig: React.FC = () => {
  const [activeTab, setActiveTab] = useState('triggers');
  const [selectedAgent, setSelectedAgent] = useState('Iriska');
  const [config, setConfig] = useState<EmotionalMemoryConfig | null>(null);
  const [loading, setLoading] = useState(false);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({});

  const tabs = [
    { id: 'triggers', label: 'Эмоциональные триггеры', icon: <Heart className="w-5 h-5" /> },
    { id: 'modulators', label: 'Нейромодуляторы', icon: <Brain className="w-5 h-5" /> },
    { id: 'analysis', label: 'Анализ эмоций', icon: <Activity className="w-5 h-5" /> }
  ];

  const emotionCategories = [
    { key: 'joy_triggers', label: 'Радость', icon: '😊', color: 'yellow' },
    { key: 'sadness_triggers', label: 'Грусть', icon: '😢', color: 'blue' },
    { key: 'anger_triggers', label: 'Гнев', icon: '😠', color: 'red' },
    { key: 'fear_triggers', label: 'Страх', icon: '😨', color: 'purple' },
    { key: 'surprise_triggers', label: 'Удивление', icon: '😲', color: 'orange' },
    { key: 'disgust_triggers', label: 'Отвращение', icon: '🤢', color: 'green' },
    { key: 'trust_triggers', label: 'Доверие', icon: '🤝', color: 'indigo' },
    { key: 'anticipation_triggers', label: 'Предвкушение', icon: '🎯', color: 'pink' }
  ];

  const neuromodulators = [
    { key: 'dopamine', label: 'Дофамин', icon: '🎯', color: 'red', description: 'Вознаграждение, мотивация' },
    { key: 'serotonin', label: 'Серотонин', icon: '😌', color: 'blue', description: 'Настроение, стабильность' },
    { key: 'norepinephrine', label: 'Норэпинефрин', icon: '⚡', color: 'orange', description: 'Внимание, стресс' },
    { key: 'acetylcholine', label: 'Ацетилхолин', icon: '🧠', color: 'green', description: 'Обучение, память' },
    { key: 'gaba', label: 'ГАМК', icon: '😴', color: 'purple', description: 'Торможение, расслабление' }
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

  const addTrigger = (category: string) => {
    if (!config) return;
    
    const trigger = prompt(`Добавить новый триггер для категории "${category}":`);
    const weight = prompt('Вес триггера (0.0-1.0):', '0.5');
    
    if (trigger && weight) {
      const weightNum = parseFloat(weight);
      if (weightNum >= 0 && weightNum <= 1) {
        setConfig({
          ...config,
          emotion_triggers: {
            ...config.emotion_triggers,
            [category]: {
              ...config.emotion_triggers[category as keyof typeof config.emotion_triggers],
              [trigger]: weightNum
            }
          }
        });
      }
    }
  };

  const updateTrigger = (category: string, trigger: string, newWeight: number) => {
    if (!config) return;
    
    setConfig({
      ...config,
      emotion_triggers: {
        ...config.emotion_triggers,
        [category]: {
          ...config.emotion_triggers[category as keyof typeof config.emotion_triggers],
          [trigger]: newWeight
        }
      }
    });
  };

  const removeTrigger = (category: string, trigger: string) => {
    if (!config) return;
    
    const triggers = { ...config.emotion_triggers[category as keyof typeof config.emotion_triggers] };
    delete triggers[trigger];
    
    setConfig({
      ...config,
      emotion_triggers: {
        ...config.emotion_triggers,
        [category]: triggers
      }
    });
  };

  const updateNeuromodulatorLevel = (modulator: string, type: string, value: number) => {
    if (!config) return;
    
    setConfig({
      ...config,
      neuromodulator_settings: {
        ...config.neuromodulator_settings,
        [type]: {
          ...config.neuromodulator_settings[type as keyof typeof config.neuromodulator_settings],
          [modulator]: value
        }
      }
    });
  };

  if (loading || !config) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent-500"></div>
        <span className="ml-3 text-primary-600">Загрузка конфигурации эмоциональной памяти...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-primary-900">Эмоциональная память</h1>
          <p className="text-primary-600 mt-2">Настройка триггеров эмоций и нейромодуляторов</p>
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
        
        {/* Emotion Triggers */}
        {activeTab === 'triggers' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="text-xl font-semibold text-primary-800">Эмоциональные триггеры</h3>
              <div className="text-sm text-primary-600">
                Всего триггеров: {Object.values(config.emotion_triggers).reduce((total, triggers) => 
                  total + Object.keys(triggers).length, 0
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {emotionCategories.map((category) => {
                const triggers = config.emotion_triggers[category.key as keyof typeof config.emotion_triggers] || {};
                const isExpanded = expandedSections[category.key];

                return (
                  <div key={category.key} className="border border-primary-200 rounded-lg">
                    <button
                      onClick={() => toggleSection(category.key)}
                      className="w-full flex items-center justify-between p-4 hover:bg-primary-50 transition-colors"
                    >
                      <div className="flex items-center space-x-3">
                        <span className="text-2xl">{category.icon}</span>
                        <div className="text-left">
                          <h4 className="font-medium text-primary-800">{category.label}</h4>
                          <p className="text-sm text-primary-600">{Object.keys(triggers).length} триггеров</p>
                        </div>
                      </div>
                      {isExpanded ? <ChevronDown className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
                    </button>

                    {isExpanded && (
                      <div className="border-t border-primary-200 p-4 space-y-3">
                        <div className="flex justify-between items-center">
                          <span className="text-sm font-medium text-primary-700">Триггеры с весами:</span>
                          <button
                            onClick={() => addTrigger(category.key)}
                            className="flex items-center space-x-1 text-sm text-accent-600 hover:text-accent-700"
                          >
                            <Plus className="w-4 h-4" />
                            <span>Добавить</span>
                          </button>
                        </div>

                        <div className="max-h-60 overflow-y-auto space-y-2">
                          {Object.entries(triggers).map(([trigger, weight]) => (
                            <div key={trigger} className="flex items-center space-x-3 p-2 bg-gray-50 rounded group">
                              <input
                                type="text"
                                value={trigger}
                                className="flex-1 px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-accent-500 focus:border-transparent bg-white"
                                readOnly
                              />
                              <div className="flex items-center space-x-2">
                                <input
                                  type="range"
                                  min="0"
                                  max="1"
                                  step="0.1"
                                  value={weight}
                                  onChange={(e) => updateTrigger(category.key, trigger, parseFloat(e.target.value))}
                                  className="w-20"
                                />
                                <span className="text-xs font-mono w-8 text-center">{weight.toFixed(1)}</span>
                                <button
                                  onClick={() => removeTrigger(category.key, trigger)}
                                  className="opacity-0 group-hover:opacity-100 text-error-500 hover:text-error-700 transition-opacity"
                                >
                                  <Trash2 className="w-4 h-4" />
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Neuromodulators */}
        {activeTab === 'modulators' && (
          <div className="space-y-8">
            <h3 className="text-xl font-semibold text-primary-800">Настройки нейромодуляторов</h3>

            {neuromodulators.map((modulator) => {
              const isExpanded = expandedSections[modulator.key];
              const baseLevel = config.neuromodulator_settings.base_levels[modulator.key] || 0.5;
              const threshold = config.neuromodulator_settings.activation_thresholds[modulator.key] || 0.5;
              const halfLife = config.neuromodulator_settings.half_life_minutes[modulator.key] || 60;

              return (
                <div key={modulator.key} className="border border-primary-200 rounded-lg">
                  <button
                    onClick={() => toggleSection(modulator.key)}
                    className="w-full flex items-center justify-between p-4 hover:bg-primary-50 transition-colors"
                  >
                    <div className="flex items-center space-x-3">
                      <span className="text-2xl">{modulator.icon}</span>
                      <div className="text-left">
                        <h4 className="font-medium text-primary-800">{modulator.label}</h4>
                        <p className="text-sm text-primary-600">{modulator.description}</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-4">
                      <div className="text-right text-sm">
                        <div>Базовый: {baseLevel.toFixed(2)}</div>
                        <div>Порог: {threshold.toFixed(2)}</div>
                      </div>
                      {isExpanded ? <ChevronDown className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
                    </div>
                  </button>

                  {isExpanded && (
                    <div className="border-t border-primary-200 p-6 space-y-6">
                      {/* Base Settings */}
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-primary-700 mb-2">
                            Базовый уровень
                          </label>
                          <div className="space-y-2">
                            <input
                              type="range"
                              min="0"
                              max="1"
                              step="0.1"
                              value={baseLevel}
                              onChange={(e) => updateNeuromodulatorLevel(modulator.key, 'base_levels', parseFloat(e.target.value))}
                              className="w-full"
                            />
                            <div className="text-center text-sm font-mono">{baseLevel.toFixed(1)}</div>
                          </div>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-primary-700 mb-2">
                            Порог активации
                          </label>
                          <div className="space-y-2">
                            <input
                              type="range"
                              min="0"
                              max="1"
                              step="0.1"
                              value={threshold}
                              onChange={(e) => updateNeuromodulatorLevel(modulator.key, 'activation_thresholds', parseFloat(e.target.value))}
                              className="w-full"
                            />
                            <div className="text-center text-sm font-mono">{threshold.toFixed(1)}</div>
                          </div>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-primary-700 mb-2">
                            Время полураспада (мин)
                          </label>
                          <div className="space-y-2">
                            <input
                              type="range"
                              min="5"
                              max="180"
                              step="5"
                              value={halfLife}
                              onChange={(e) => updateNeuromodulatorLevel(modulator.key, 'half_life_minutes', parseInt(e.target.value))}
                              className="w-full"
                            />
                            <div className="text-center text-sm font-mono">{halfLife} мин</div>
                          </div>
                        </div>
                      </div>

                      {/* Effects */}
                      <div>
                        <h5 className="font-medium text-primary-800 mb-3">Эффекты модуляции</h5>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          {Object.entries(config.neuromodulator_settings.modulation_effects[modulator.key] || {}).map(([effect, value]) => (
                            <div key={effect} className="flex items-center space-x-3">
                              <label className="text-sm text-primary-700 flex-1 capitalize">
                                {effect.replace(/_/g, ' ')}
                              </label>
                              <input
                                type="number"
                                step="0.1"
                                min="0"
                                max="3"
                                value={value}
                                onChange={(e) => {
                                  const newEffects = {
                                    ...config.neuromodulator_settings.modulation_effects,
                                    [modulator.key]: {
                                      ...config.neuromodulator_settings.modulation_effects[modulator.key],
                                      [effect]: parseFloat(e.target.value)
                                    }
                                  };
                                  setConfig({
                                    ...config,
                                    neuromodulator_settings: {
                                      ...config.neuromodulator_settings,
                                      modulation_effects: newEffects
                                    }
                                  });
                                }}
                                className="w-20 px-2 py-1 text-sm border border-primary-300 rounded focus:ring-1 focus:ring-accent-500"
                              />
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Analysis Config */}
        {activeTab === 'analysis' && (
          <div className="space-y-8">
            <h3 className="text-xl font-semibold text-primary-800">Конфигурация анализа эмоций</h3>

            {/* Intensity Thresholds */}
            <div className="border border-primary-200 rounded-lg p-6">
              <h4 className="font-medium text-primary-800 mb-4">Пороги интенсивности</h4>
              <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                {Object.entries(config.emotion_analysis_config.intensity_thresholds).map(([level, value]) => (
                  <div key={level}>
                    <label className="block text-sm font-medium text-primary-700 mb-2 capitalize">
                      {level.replace(/_/g, ' ')}
                    </label>
                    <div className="space-y-2">
                      <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.1"
                        value={value}
                        onChange={(e) => {
                          setConfig({
                            ...config,
                            emotion_analysis_config: {
                              ...config.emotion_analysis_config,
                              intensity_thresholds: {
                                ...config.emotion_analysis_config.intensity_thresholds,
                                [level]: parseFloat(e.target.value)
                              }
                            }
                          });
                        }}
                        className="w-full"
                      />
                      <div className="text-center text-sm font-mono">{value.toFixed(1)}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Context Analysis */}
            <div className="border border-primary-200 rounded-lg p-6">
              <h4 className="font-medium text-primary-800 mb-4">Настройки контекстного анализа</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {Object.entries(config.emotion_analysis_config.context_analysis).map(([param, value]) => (
                  <div key={param}>
                    <label className="block text-sm font-medium text-primary-700 mb-2 capitalize">
                      {param.replace(/_/g, ' ')}
                    </label>
                    <input
                      type="number"
                      step={param.includes('window') ? "1" : "0.1"}
                      min="0"
                      max={param.includes('window') ? "10" : "2"}
                      value={value}
                      onChange={(e) => {
                        setConfig({
                          ...config,
                          emotion_analysis_config: {
                            ...config.emotion_analysis_config,
                            context_analysis: {
                              ...config.emotion_analysis_config.context_analysis,
                              [param]: parseFloat(e.target.value)
                            }
                          }
                        });
                      }}
                      className="w-full px-3 py-2 border border-primary-300 rounded focus:ring-1 focus:ring-accent-500"
                    />
                  </div>
                ))}
              </div>
            </div>

            {/* History Settings */}
            <div className="border border-primary-200 rounded-lg p-6">
              <h4 className="font-medium text-primary-800 mb-4">Настройки истории эмоций</h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {Object.entries(config.emotion_analysis_config.history_settings).map(([param, value]) => (
                  <div key={param}>
                    <label className="block text-sm font-medium text-primary-700 mb-2 capitalize">
                      {param.replace(/_/g, ' ')}
                    </label>
                    <input
                      type="number"
                      step={param === 'decay_factor' ? "0.01" : "1"}
                      min={param === 'decay_factor' ? "0.5" : "1"}
                      max={param === 'max_history_size' ? "200" : param === 'trend_analysis_hours' ? "168" : "1"}
                      value={value}
                      onChange={(e) => {
                        setConfig({
                          ...config,
                          emotion_analysis_config: {
                            ...config.emotion_analysis_config,
                            history_settings: {
                              ...config.emotion_analysis_config.history_settings,
                              [param]: parseFloat(e.target.value)
                            }
                          }
                        });
                      }}
                      className="w-full px-3 py-2 border border-primary-300 rounded focus:ring-1 focus:ring-accent-500"
                    />
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default EmotionalMemoryConfig;
