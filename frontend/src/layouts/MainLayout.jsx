import React, { useState, useEffect } from 'react';
import { NavLink, Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Code2,
  FolderGit2,
  History,
  Brain,
  Settings as SettingsIcon,
  LogOut,
  Moon,
  Sun,
  ShieldCheck,
  Cpu,
  ChevronRight,
  Menu,
  X,
  Sparkles,
} from 'lucide-react';
import GithubIcon from '../components/GithubIcon';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { memoryService, healthService } from '../services/api';

export default function MainLayout() {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [hindsightStatus, setHindsightStatus] = useState({ connected: false, checking: true });
  const [aiStatus, setAiStatus] = useState({ available: false, model: 'llama-3.3-70b-versatile' });

  useEffect(() => {
    const checkDiagnostics = async () => {
      try {
        const res = await healthService.getDiagnostics();
        const data = res.data;
        setHindsightStatus({
          connected: data.memory_service?.connected || false,
          checking: false,
          message: data.memory_service?.message || data.memory_service?.error,
        });
        setAiStatus({
          available: data.ai_service?.available || false,
          model: data.ai_service?.model || 'llama-3.3-70b-versatile',
        });
      } catch {
        setHindsightStatus({ connected: false, checking: false });
      }
    };
    checkDiagnostics();
  }, [location.pathname]);

  const navItems = [
    { name: 'Overview', path: '/', icon: LayoutDashboard },
    { name: 'Code Review', path: '/review', icon: Code2 },
    { name: 'Projects', path: '/projects', icon: FolderGit2 },
    { name: 'GitHub', path: '/github', icon: GithubIcon },
    { name: 'Review History', path: '/history', icon: History },
    { name: 'AI Memory', path: '/memory', icon: Brain },
    { name: 'Settings', path: '/settings', icon: SettingsIcon },
  ];

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-800 dark:text-slate-100 flex flex-col md:flex-row font-sans">
      {/* Desktop Sidebar */}
      <aside className="w-64 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 hidden md:flex flex-col justify-between p-4 shadow-xs">
        <div>
          {/* Logo & Brand */}
          <div className="flex items-center gap-3 px-2 py-4 mb-4 border-b border-slate-100 dark:border-slate-800">
            <div className="w-10 h-10 rounded-xl bg-blue-600 text-white flex items-center justify-center shadow-sm shadow-blue-500/20">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <div className="font-bold text-lg tracking-tight text-slate-900 dark:text-white flex items-center gap-1.5">
                ReviewMind
                <span className="text-[10px] font-semibold bg-blue-50 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300 px-1.5 py-0.5 rounded-sm">AI</span>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400">Persistent Memory Agent</p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  end={item.path === '/'}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 font-semibold'
                        : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800/60'
                    }`
                  }
                >
                  <Icon className="w-4 h-4" />
                  {item.name}
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* Bottom Panel: System Indicators & User */}
        <div className="pt-4 border-t border-slate-100 dark:border-slate-800 space-y-3">
          {/* Hindsight Status Pill */}
          <div className="px-3 py-2 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200/60 dark:border-slate-700/60 text-xs">
            <div className="flex items-center justify-between font-medium">
              <span className="flex items-center gap-1.5 text-slate-600 dark:text-slate-300">
                <Brain className="w-3.5 h-3.5 text-purple-500" />
                Hindsight Memory
              </span>
              <span
                className={`w-2 h-2 rounded-full ${
                  hindsightStatus.connected ? 'bg-emerald-500 animate-pulse' : 'bg-amber-400'
                }`}
              />
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 truncate">
              {hindsightStatus.connected ? 'Bank Context Active' : 'Self-hosted (Offline)'}
            </p>
          </div>

          {/* User Profile & Logout */}
          <div className="flex items-center justify-between px-2 pt-1">
            <div className="flex items-center gap-2 overflow-hidden">
              <div className="w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200 flex items-center justify-center font-semibold text-xs">
                {user?.full_name ? user.full_name[0].toUpperCase() : 'U'}
              </div>
              <div className="overflow-hidden">
                <p className="text-xs font-medium text-slate-900 dark:text-slate-100 truncate">
                  {user?.full_name || 'Developer'}
                </p>
                <p className="text-[10px] text-slate-500 truncate">{user?.email || 'Guest'}</p>
              </div>
            </div>

            <div className="flex items-center gap-1">
              <button
                onClick={toggleTheme}
                title="Toggle Theme"
                className="p-1.5 rounded-md hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500 hover:text-slate-700 dark:text-slate-400"
              >
                {theme === 'dark' ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4" />}
              </button>
              <button
                onClick={handleLogout}
                title="Logout"
                className="p-1.5 rounded-md hover:bg-rose-50 dark:hover:bg-rose-950/40 text-slate-500 hover:text-rose-600 dark:text-slate-400"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </aside>

      {/* Mobile Header */}
      <div className="md:hidden flex items-center justify-between p-4 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-blue-600 text-white flex items-center justify-center">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <span className="font-bold text-slate-900 dark:text-white">ReviewMind</span>
        </div>
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="p-2 rounded-lg text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
        >
          {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {/* Mobile Dropdown Nav */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 px-4 py-3 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={() => setMobileMenuOpen(false)}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium ${
                    isActive ? 'bg-blue-50 text-blue-600 font-semibold' : 'text-slate-600'
                  }`
                }
              >
                <Icon className="w-4 h-4" />
                {item.name}
              </NavLink>
            );
          })}
        </div>
      )}

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
