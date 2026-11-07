import React, { useState, useEffect } from 'react';
import {
  Settings as SettingsIcon,
  User,
  Brain,
  Sparkles,
  Sun,
  Moon,
  Shield,
  CheckCircle,
  Server,
} from 'lucide-react';
import GithubIcon from '../components/GithubIcon';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { healthService, githubService } from '../services/api';

export default function Settings() {
  const { user } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [diagnostics, setDiagnostics] = useState(null);
  const [githubStatus, setGithubStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSettingsData = async () => {
      try {
        setLoading(true);
        const [diagRes, ghRes] = await Promise.all([
          healthService.getDiagnostics(),
          githubService.getStatus().catch(() => ({ data: { connected: false } })),
        ]);
        setDiagnostics(diagRes.data);
        setGithubStatus(ghRes.data);
      } catch (err) {
        console.error('Failed to load settings telemetry:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchSettingsData();
  }, []);

  return (
    <div className="p-6 md:p-8 max-w-4xl mx-auto w-full space-y-8">
      {/* Header */}
      <div className="pb-4 border-b border-slate-200 dark:border-slate-800">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2.5">
          <SettingsIcon className="w-6 h-6 text-slate-700 dark:text-slate-300" />
          Settings & Environment Diagnostics
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          ReviewMind runtime status, authentication profile, and AI memory server configurations.
        </p>
      </div>

      {loading ? (
        <div className="p-12 text-center text-slate-400 text-xs">Loading telemetry & diagnostics...</div>
      ) : (
        <div className="space-y-6">
        {/* User Profile Card */}
        <div className="p-6 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-xs space-y-4">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
            <User className="w-4 h-4 text-blue-500" />
            Developer Profile
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div>
              <span className="text-slate-400 block mb-0.5">Full Name</span>
              <p className="font-semibold text-slate-900 dark:text-white">
                {user?.full_name || 'Lead Developer'}
              </p>
            </div>
            <div>
              <span className="text-slate-400 block mb-0.5">Email Address</span>
              <p className="font-semibold text-slate-900 dark:text-white font-mono">
                {user?.email || 'developer@reviewmind.ai'}
              </p>
            </div>
            <div>
              <span className="text-slate-400 block mb-0.5">Account Status</span>
              <span className="inline-flex items-center gap-1 text-emerald-600 font-semibold">
                <CheckCircle className="w-3.5 h-3.5" /> Active & Verified
              </span>
            </div>
          </div>
        </div>

        {/* Appearance & Theme Card */}
        <div className="p-6 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-xs space-y-4">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
            {theme === 'dark' ? <Moon className="w-4 h-4 text-amber-400" /> : <Sun className="w-4 h-4 text-amber-500" />}
            Interface Theme
          </h2>

          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-900 dark:text-white">
                Current Mode: <span className="capitalize">{theme}</span>
              </p>
              <p className="text-xs text-slate-500 mt-0.5">
                Default is crisp minimal light theme with blue accenting.
              </p>
            </div>

            <button
              onClick={toggleTheme}
              className="px-3.5 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 text-xs font-semibold flex items-center gap-2 transition-colors"
            >
              {theme === 'dark' ? <Sun className="w-3.5 h-3.5 text-amber-400" /> : <Moon className="w-3.5 h-3.5" />}
              Switch to {theme === 'dark' ? 'Light' : 'Dark'}
            </button>
          </div>
        </div>

        {/* AI & Memory Configuration Diagnostics */}
        <div className="p-6 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-xs space-y-4">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
            <Server className="w-4 h-4 text-purple-500" />
            Integrations & Service Health
          </h2>

          <div className="divide-y divide-slate-100 dark:divide-slate-800 text-xs">
            {/* Groq AI Status */}
            <div className="py-3 flex items-center justify-between">
              <div>
                <div className="font-semibold text-slate-900 dark:text-white flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-blue-500" />
                  Groq AI Code Reviewer
                </div>
                <p className="text-slate-500 text-[11px] mt-0.5">
                  Configured Model: <code className="text-slate-700 dark:text-slate-300">{diagnostics?.ai_service?.model}</code>
                </p>
              </div>
              <span
                className={`px-2 py-0.5 rounded-full font-semibold ${
                  diagnostics?.ai_service?.configured
                    ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300'
                    : 'bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300'
                }`}
              >
                {diagnostics?.ai_service?.configured ? 'Active' : 'Missing GROQ_API_KEY'}
              </span>
            </div>

            {/* Hindsight Status */}
            <div className="py-3 flex items-center justify-between">
              <div>
                <div className="font-semibold text-slate-900 dark:text-white flex items-center gap-1.5">
                  <Brain className="w-3.5 h-3.5 text-purple-500" />
                  Hindsight by Vectorize
                </div>
                <p className="text-slate-500 text-[11px] mt-0.5">
                  Server Endpoint: <code className="text-slate-700 dark:text-slate-300">{diagnostics?.memory_service?.base_url}</code>
                </p>
              </div>
              <span
                className={`px-2 py-0.5 rounded-full font-semibold ${
                  diagnostics?.memory_service?.connected
                    ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300'
                    : 'bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300'
                }`}
              >
                {diagnostics?.memory_service?.connected ? 'Online' : 'Self-hosted (Offline)'}
              </span>
            </div>

            {/* GitHub Status */}
            <div className="py-3 flex items-center justify-between">
              <div>
                <div className="font-semibold text-slate-900 dark:text-white flex items-center gap-1.5">
                  <GithubIcon className="w-3.5 h-3.5 text-slate-700 dark:text-slate-300" />
                  GitHub Integration
                </div>
                <p className="text-slate-500 text-[11px] mt-0.5">
                  {githubStatus?.connected ? `Connected as @${githubStatus.github_username}` : 'Not connected'}
                </p>
              </div>
              <span
                className={`px-2 py-0.5 rounded-full font-semibold ${
                  githubStatus?.connected
                    ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300'
                    : 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300'
                }`}
              >
                {githubStatus?.connected ? 'Connected' : 'Disconnected'}
              </span>
            </div>

            {/* Database Engine */}
            <div className="py-3 flex items-center justify-between">
              <div>
                <div className="font-semibold text-slate-900 dark:text-white flex items-center gap-1.5">
                  <Shield className="w-3.5 h-3.5 text-emerald-500" />
                  Database Engine
                </div>
                <p className="text-slate-500 text-[11px] mt-0.5">
                  Dialect: {diagnostics?.database?.url_type?.toUpperCase()} with SQLAlchemy ORM & Alembic migrations
                </p>
              </div>
              <span className="px-2 py-0.5 rounded-full font-semibold bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300">
                Connected
              </span>
            </div>
          </div>
        </div>
      </div>
    )}
  </div>
  );
}
