import { Link, useLocation } from 'react-router-dom';
import { Cpu, Home, Archive, Tag, Search } from 'lucide-react';

export function Header() {
  const location = useLocation();
  
  const navItems = [
    { path: '/', label: 'Home', icon: Home },
    { path: '/categories', label: 'Categories', icon: Tag },
    { path: '/archive', label: 'Archive', icon: Archive },
    { path: '/search', label: 'Search', icon: Search },
  ];

  return (
    <header className="bg-slate-900/80 backdrop-blur-md border-b border-slate-800 sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 group">
            <Cpu className="w-8 h-8 text-indigo-500 group-hover:text-purple-500 transition-colors" />
            <div className="flex flex-col">
              <span className="text-lg font-bold gradient-text">AI Game Tools</span>
              <span className="text-xs text-slate-400">Daily</span>
            </div>
          </Link>

          {/* Navigation */}
          <nav className="hidden md:flex items-center gap-1">
            {navItems.map(({ path, label, icon: Icon }) => (
              <Link
                key={path}
                to={path}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  location.pathname === path
                    ? 'bg-indigo-600/20 text-indigo-400'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                }`}
              >
                <Icon className="w-4 h-4" />
                {label}
              </Link>
            ))}
          </nav>

          {/* Mobile menu button */}
          <button className="md:hidden p-2 text-slate-400 hover:text-slate-200">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
        </div>
      </div>
    </header>
  );
}
