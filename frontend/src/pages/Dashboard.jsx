import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Code2,
  FolderGit2,
  AlertTriangle,
  ShieldAlert,
  Brain,
  ArrowRight,
  Sparkles,
  ChevronRight,
} from 'lucide-react';
import { projectService, reviewService, healthService } from '../services/api';

export default function Dashboard() {
  const [stats, setStats] = useState({
    totalProjects: 0,
    totalReviews: 0,
    criticalIssues: 0,
    highIssues: 0,
    resolvedIssues: 0,
  });
  const [recentReviews, setRecentReviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [diagnostics, setDiagnostics] = useState(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        const [projRes, revRes, diagRes] = await Promise.all([
          projectService.list(),
          reviewService.list({ limit: 10 }),
          healthService.getDiagnostics(),
        ]);

        const projects = projRes.data || [];
        const reviews = revRes.data || [];
        setDiagnostics(diagRes.data);

        let critical = 0;
        let high = 0;
        let medium = 0;
        let low = 0;
        for (const r of reviews) {
          if (r.metrics) {
            critical += r.metrics.critical || 0;
            high += r.metrics.high || 0;
            medium += r.metrics.medium || 0;
            low += r.metrics.low || 0;
          }
        }

        setStats({
          totalProjects: projects.length,
          totalReviews: reviews.length,
          criticalIssues: critical,
          highIssues: high,
          mediumIssues: medium,
          lowIssues: low,
        });
        setRecentReviews(reviews);
      } catch (err) {
        console.error('Failed to load dashboard data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  const statCards = [
    {
      title: 'Total Projects',
      value: stats.totalProjects,
      icon: FolderGit2,
      color: 'text-blue-600 bg-blue-50 dark:bg-blue-950/40 dark:text-blue-400',
      change: 'Active workspaces',
    },
    {
      title: 'Code Reviews',
      value: stats.totalReviews,
      icon: Code2,
      color: 'text-indigo-600 bg-indigo-50 dark:bg-indigo-950/40 dark:text-indigo-400',
      change: 'Inspections completed',
    },
    {
      title: 'Critical Vulnerabilities',
      value: stats.criticalIssues,
      icon: ShieldAlert,
      color: 'text-rose-600 bg-rose-50 dark:bg-rose-950/40 dark:text-rose-400',
      change: 'Immediate action needed',
    },
    {
      title: 'High Severity Issues',
      value: stats.highIssues,
      icon: AlertTriangle,
      color: 'text-amber-600 bg-amber-50 dark:bg-amber-950/40 dark:text-amber-400',
      change: 'Quality & security alerts',
    },
  ];

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto w-full space-y-8">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-slate-200 dark:border-slate-800">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Engineering Dashboard
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Real-time code health overview and persistent agent memory telemetry.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            to="/review"
            className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium shadow-xs transition-colors"
          >
            <Code2 className="w-4 h-4" />
            New Code Review
          </Link>
        </div>
      </div>

      {/* System Engine Status Callout */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Hindsight Status */}
        <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs flex items-start gap-3">
          <div className="p-2.5 rounded-lg bg-purple-50 dark:bg-purple-950/50 text-purple-600 dark:text-purple-400">
            <Brain className="w-5 h-5" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-slate-900 dark:text-white">Hindsight Agent Memory</h2>
              <span
                className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                  diagnostics?.memory_service?.connected
                    ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300'
                    : 'bg-amber-50 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300'
                }`}
              >
                {diagnostics?.memory_service?.connected ? 'Connected' : 'Offline / Self-hosted'}
              </span>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Target endpoint: <code className="text-slate-700 dark:text-slate-300">{diagnostics?.memory_service?.base_url || 'https://api.hindsight.vectorize.io'}</code>
            </p>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Multi-strategy semantic retrieval, temporal memory, and project bank isolation active.
            </p>
          </div>
        </div>

        {/* AI Model Status */}
        <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs flex items-start gap-3">
          <div className="p-2.5 rounded-lg bg-blue-50 dark:bg-blue-950/50 text-blue-600 dark:text-blue-400">
            <Sparkles className="w-5 h-5" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-slate-900 dark:text-white">Groq AI Inference Engine</h2>
              <span
                className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                  diagnostics?.ai_service?.configured
                    ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300'
                    : 'bg-amber-50 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300'
                }`}
              >
                {diagnostics?.ai_service?.configured ? 'Active' : 'Static AST Mode'}
              </span>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Model: <code className="text-slate-700 dark:text-slate-300">{diagnostics?.ai_service?.model || 'openai/gpt-oss-20b'}</code>
            </p>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Structured JSON validation with Pydantic guardrails & anti-prompt injection shielding.
            </p>
          </div>
        </div>
      </div>

      {/* Zero Projects Alert */}
      {!loading && stats.totalProjects === 0 && (
        <div className="p-4 rounded-xl bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <FolderGit2 className="w-5 h-5 text-blue-600 dark:text-blue-400 shrink-0" />
            <div>
              <p className="text-sm font-semibold text-blue-900 dark:text-blue-200">
                No projects found
              </p>
              <p className="text-xs text-blue-700 dark:text-blue-300">
                Create your first project workspace to isolate agent memory banks and track long-term code health.
              </p>
            </div>
          </div>
          <Link
            to="/projects"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium shrink-0 transition-colors"
          >
            Create Project <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      )}

      {/* Metrics Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((stat) => {
          const Icon = stat.icon;
          return (
            <div
              key={stat.title}
              className="p-5 bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 rounded-xl shadow-xs space-y-3"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  {stat.title}
                </span>
                <div className={`p-2 rounded-lg ${stat.color}`}>
                  <Icon className="w-4 h-4" />
                </div>
              </div>
              <div>
                <div className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
                  {loading ? '...' : stat.value}
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{stat.change}</p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Recent Reviews Table */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 rounded-xl shadow-xs overflow-hidden">
        <div className="p-5 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-slate-900 dark:text-white">Recent Code Reviews</h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Audit log of completed reviews with quality scores and recalled memories.
            </p>
          </div>
          <Link
            to="/history"
            className="text-xs font-medium text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
          >
            View All <ChevronRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {recentReviews.length === 0 ? (
          <div className="p-12 text-center space-y-3">
            <div className="w-12 h-12 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-400 flex items-center justify-center mx-auto">
              <Code2 className="w-6 h-6" />
            </div>
            <p className="text-sm font-medium text-slate-700 dark:text-slate-300">No code reviews yet</p>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              Open the built-in Monaco Code Editor and submit your first snippet to test persistent AI memory.
            </p>
            <Link
              to="/review"
              className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-xs font-medium mt-2"
            >
              Start Review
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 dark:bg-slate-800/50 text-slate-500 dark:text-slate-400 text-xs font-semibold uppercase tracking-wider border-b border-slate-100 dark:border-slate-800">
                <tr>
                  <th className="px-5 py-3">Review Title</th>
                  <th className="px-5 py-3">Language</th>
                  <th className="px-5 py-3">Score</th>
                  <th className="px-5 py-3">Findings</th>
                  <th className="px-5 py-3">Recalled Memories</th>
                  <th className="px-5 py-3">Date</th>
                  <th className="px-5 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {recentReviews.map((rev) => (
                  <tr key={rev.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition-colors">
                    <td className="px-5 py-3.5 font-medium text-slate-900 dark:text-slate-100">
                      {rev.title}
                    </td>
                    <td className="px-5 py-3.5">
                      <span className="text-xs px-2 py-0.5 rounded-md font-mono bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                        {rev.language}
                      </span>
                    </td>
                    <td className="px-5 py-3.5">
                      <span
                        className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                          rev.score >= 80
                            ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300'
                            : rev.score >= 60
                            ? 'bg-amber-50 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300'
                            : 'bg-rose-50 text-rose-700 dark:bg-rose-950/50 dark:text-rose-300'
                        }`}
                      >
                        {rev.score}/100
                      </span>
                    </td>
                    <td className="px-5 py-3.5 text-xs text-slate-600 dark:text-slate-300">
                      <span className="font-semibold text-rose-600">{rev.metrics?.critical || 0} crit</span>,{' '}
                      <span className="text-amber-600">{rev.metrics?.high || 0} high</span>
                    </td>
                    <td className="px-5 py-3.5 text-xs text-purple-600 dark:text-purple-400 font-medium">
                      {rev.recalled_memories?.length > 0 ? (
                        <span className="flex items-center gap-1">
                          <Brain className="w-3.5 h-3.5" />
                          {rev.recalled_memories.length} recalled
                        </span>
                      ) : (
                        <span className="text-slate-400">None</span>
                      )}
                    </td>
                    <td className="px-5 py-3.5 text-xs text-slate-500">
                      {new Date(rev.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <Link
                        to={`/history`}
                        className="text-xs text-blue-600 dark:text-blue-400 font-medium hover:underline"
                      >
                        Details
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
