import React from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { MessageCircle, Settings, Database, Home, User, Brain, Heart } from 'lucide-react';

const Layout: React.FC = () => {
  const location = useLocation();

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-primary-100 flex">
      {/* Боковая навигация для широких экранов */}
      <div className="hidden lg:flex flex-col w-20 bg-white/80 backdrop-blur-md border-r border-primary-200">
        <div className="flex-1 flex flex-col items-center py-6 space-y-8">
          {/* Logo */}
          <div className="w-12 h-12 bg-gradient-to-br from-accent-500 to-accent-600 rounded-xl flex items-center justify-center">
            <span className="text-white font-bold text-xl">И</span>
          </div>

          {/* Вертикальная навигация */}
          <nav className="flex flex-col items-center space-y-6">
            <NavLink to="/" icon={<Home className="w-6 h-6" />} label="Главная" isActive={location.pathname === '/'} />
            <NavLink to="/chat" icon={<MessageCircle className="w-6 h-6" />} label="Чат" isActive={location.pathname === '/chat'} />
            <NavLink to="/config" icon={<Settings className="w-6 h-6" />} label="Настройки" isActive={location.pathname === '/config'} />
            <NavLink to="/summarization" icon={<Brain className="w-6 h-6" />} label="Суммаризация" isActive={location.pathname === '/summarization'} />
            <NavLink to="/emotional-memory" icon={<Heart className="w-6 h-6" />} label="Эмоции" isActive={location.pathname === '/emotional-memory'} />
            <NavLink to="/storage" icon={<Database className="w-6 h-6" />} label="Хранилище" isActive={location.pathname === '/storage'} />
            {/* Тестовая ссылка для отладки */}
            <NavLink to="/test" icon={<span className="w-6 h-6 text-center text-lg font-bold">T</span>} label="Тест" isActive={location.pathname === '/test'} />
          </nav>

          {/* Профиль внизу */}
          <div className="mt-auto">
            <button className="p-3 rounded-xl hover:bg-primary-100 transition-colors">
              <User className="w-6 h-6 text-primary-600" />
            </button>
          </div>
        </div>
      </div>

      {/* Основной контент */}
      <div className="flex-1 flex flex-col">
        {/* Header для мобильных устройств */}
        <header className="lg:hidden bg-white/80 backdrop-blur-md border-b border-primary-200 sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              {/* Logo */}
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-gradient-to-br from-accent-500 to-accent-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-lg">И</span>
                </div>
                <span className="text-xl font-semibold text-primary-800">Ириска</span>
              </div>

              {/* Горизонтальная навигация для мобильных */}
              <nav className="flex items-center space-x-4">
                <MobileNavLink to="/" icon={<Home className="w-5 h-5" />} />
                <MobileNavLink to="/chat" icon={<MessageCircle className="w-5 h-5" />} />
                <MobileNavLink to="/config" icon={<Settings className="w-5 h-5" />} />
                <MobileNavLink to="/summarization" icon={<Brain className="w-5 h-5" />} />
                <MobileNavLink to="/emotional-memory" icon={<Heart className="w-5 h-5" />} />
                <MobileNavLink to="/storage" icon={<Database className="w-5 h-5" />} />
              </nav>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Outlet />
        </main>

        {/* Footer */}
        <footer className="bg-white/80 backdrop-blur-md border-t border-primary-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <div className="text-center text-primary-600">
              <p>&copy; 2024 Ириска - Digital бунтарь и AI агент</p>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
};

// NavLink компонент для боковой панели
const NavLink: React.FC<{ to: string; icon: React.ReactNode; label: string; isActive: boolean }> = ({ to, icon, label, isActive }) => {
  return (
    <Link
      to={to}
      className={`group relative p-3 rounded-xl transition-all duration-200 ${
        isActive 
          ? 'bg-accent-100 text-accent-600 border border-accent-200' 
          : 'text-primary-600 hover:text-primary-800 hover:bg-primary-50'
      }`}
      title={label}
    >
      {icon}
      {/* Tooltip */}
      <div className="absolute left-full ml-2 px-2 py-1 bg-primary-800 text-white text-sm rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap z-50">
        {label}
      </div>
    </Link>
  );
};

// Мобильный NavLink
const MobileNavLink: React.FC<{ to: string; icon: React.ReactNode }> = ({ to, icon }) => {
  return (
    <Link
      to={to}
      className="p-2 rounded-lg text-primary-600 hover:text-primary-800 hover:bg-primary-50 transition-colors"
    >
      {icon}
    </Link>
  );
};

export default Layout;
