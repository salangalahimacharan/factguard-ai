import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ShieldCheck, Search, History, BarChart3, Layers, BookOpen, ExternalLink } from 'lucide-react';

export const Navbar: React.FC = () => {
  const location = useLocation();

  const navItems = [
    { label: 'Check Claim', path: '/verify', icon: <Search className="w-4 h-4" /> },
    { label: 'Demo Mode', path: '/demo', icon: <Layers className="w-4 h-4 text-cyan-400" /> },
    { label: 'History', path: '/history', icon: <History className="w-4 h-4" /> },
    { label: 'Analytics', path: '/analytics', icon: <BarChart3 className="w-4 h-4" /> },
  ];

  return (
    <nav className="sticky top-0 z-50 glass-panel border-b border-slate-800/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-3 group">
            <div className="p-2 bg-gradient-to-tr from-cyan-500 to-indigo-600 rounded-xl shadow-lg shadow-cyan-500/20 group-hover:scale-105 transition-transform">
              <ShieldCheck className="w-6 h-6 text-white" />
            </div>
            <div>
              <span className="font-black text-xl tracking-tight text-white">FactGuard <span className="gradient-text">AI</span></span>
              <span className="hidden sm:inline-block ml-2 text-[10px] uppercase font-bold tracking-widest bg-cyan-950 text-cyan-400 border border-cyan-800 px-1.5 py-0.5 rounded">B.Tech Project</span>
            </div>
          </Link>

          {/* Nav Links */}
          <div className="flex items-center space-x-1 sm:space-x-2">
            {navItems.map((item) => {
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center space-x-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-cyan-950/80 text-cyan-300 border border-cyan-500/30 shadow-sm'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                  }`}
                >
                  {item.icon}
                  <span>{item.label}</span>
                </Link>
              );
            })}

            <Link
              to="/verify"
              className="ml-2 bg-gradient-to-r from-cyan-500 to-sky-600 hover:from-cyan-400 hover:to-sky-500 text-white font-semibold text-sm px-4 py-2 rounded-xl shadow-lg shadow-cyan-500/25 transition-all transform hover:-translate-y-0.5"
            >
              Verify Claim
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
};
