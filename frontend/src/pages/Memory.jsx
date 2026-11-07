import React, { useState, useEffect } from 'react';
import {
  Brain,
  Plus,
  Search,
  FolderGit2,
  Tag,
  Clock,
  Layers,
  RefreshCw,
  X,
} from 'lucide-react';
import { projectService, memoryService } from '../services/api';

export default function Memory() {
  const [projects, setProjects] = useState([]);
  const [selectedProjectId, setSelectedProjectId] = useState('');
  const [bankStatus, setBankStatus] = useState(null);
  const [memories, setMemories] = useState([]);
  const [activity, setActivity] = useState([]);
  const [loading, setLoading] = useState(false);
  const [connStatus, setConnStatus] = useState(null);

  // Modal for manual retain
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [retainForm, setRetainForm] = useState({
    content: '',
    category: 'coding_standards',
    tags: 'security, sql',
  });
  const [retaining, setRetaining] = useState(false);

  // Recall Test
  const [recallQuery, setRecallQuery] = useState('database queries SQL injection');
  const [recallResults, setRecallResults] = useState(null);
  const [recalling, setRecalling] = useState(false);

  useEffect(() => {
    const init = async () => {
      try {
        const [projRes, statusRes] = await Promise.all([
          projectService.list(),
          memoryService.getStatus(),
        ]);
        setProjects(projRes.data || []);
        setConnStatus(statusRes.data);
        if (projRes.data && projRes.data.length > 0) {
          setSelectedProjectId(projRes.data[0].id);
        }
      } catch (err) {
        console.error('Failed to load memory overview:', err);
      }
    };
    init();
  }, []);

  const loadProjectMemory = async (pId) => {
    if (!pId) return;
    setLoading(true);
    try {
      const [statusRes, memRes, actRes] = await Promise.all([
        memoryService.getProjectBankStatus(pId),
        memoryService.getProjectMemories(pId).catch(() => ({ data: [] })),
        memoryService.getActivity(pId).catch(() => ({ data: [] })),
      ]);

      setBankStatus(statusRes.data);
      setMemories(memRes.data || []);
      setActivity(actRes.data || []);
    } catch (err) {
      console.error('Failed to load project memory:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedProjectId) {
      loadProjectMemory(selectedProjectId);
    }
  }, [selectedProjectId]);

  const handleRetain = async (e) => {
    e.preventDefault();
    if (!retainForm.content.trim() || !selectedProjectId) return;

    setRetaining(true);
    try {
      const tagList = retainForm.tags
        .split(',')
        .map((t) => t.trim())
        .filter(Boolean);

      await memoryService.retainMemory(selectedProjectId, {
        content: retainForm.content,
        category: retainForm.category,
        tags: tagList,
      });

      setIsModalOpen(false);
      setRetainForm({ content: '', category: 'coding_standards', tags: 'security, sql' });
      await loadProjectMemory(selectedProjectId);
    } catch (err) {
      alert('Retention failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setRetaining(false);
    }
  };

  const handleTestRecall = async () => {
    if (!recallQuery.trim() || !selectedProjectId) return;
    setRecalling(true);
    try {
      const res = await memoryService.recallMemories(selectedProjectId, {
        query: recallQuery,
        limit: 4,
      });
      setRecallResults(res.data || []);
    } catch (err) {
      alert('Recall test failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setRecalling(false);
    }
  };

  const selectedProject = projects.find((p) => p.id === parseInt(selectedProjectId, 10));

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto w-full space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-slate-200 dark:border-slate-800">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2.5">
            <Brain className="w-6 h-6 text-purple-600 dark:text-purple-400" />
            Hindsight Persistent Agent Memory
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Biomimetic long-term memory banks, semantic recall, and validated project lessons.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsModalOpen(true)}
            disabled={!selectedProjectId}
            className="inline-flex items-center gap-2 bg-purple-600 hover:bg-purple-700 disabled:bg-purple-400 text-white px-4 py-2 rounded-lg text-sm font-semibold shadow-xs transition-colors"
          >
            <Plus className="w-4 h-4" />
            Teach Rule to Agent
          </button>
        </div>
      </div>

      {/* Memory Bank Info & Status Banner */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Project Selector Card */}
        <div className="p-5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-xs space-y-3">
          <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
            Select Project Memory Bank
          </label>
          <div className="flex items-center gap-2">
            <FolderGit2 className="w-5 h-5 text-purple-600 dark:text-purple-400" />
            <select
              value={selectedProjectId}
              onChange={(e) => setSelectedProjectId(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-xs font-semibold focus:outline-hidden focus:ring-2 focus:ring-purple-500"
            >
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>
          {selectedProject && (
            <p className="text-[11px] text-slate-400 font-mono">
              Bank ID: {selectedProject.hindsight_bank_id}
            </p>
          )}
        </div>

        {/* Server Connection Status */}
        <div className="p-5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-xs space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Hindsight Server Health
            </span>
            <span
              className={`w-2.5 h-2.5 rounded-full ${
                connStatus?.connected ? 'bg-emerald-500 animate-pulse' : 'bg-amber-400'
              }`}
            />
          </div>
          <div className="text-base font-bold text-slate-900 dark:text-white">
            {connStatus?.connected ? 'Online & Ready' : 'Self-hosted (Offline)'}
          </div>
          <p className="text-xs text-slate-500 truncate">
            {connStatus?.connected
              ? `Connected at ${connStatus.base_url}`
              : 'Vectorize Hindsight Cloud (api.hindsight.vectorize.io)'}
          </p>
        </div>

        {/* Memory Stats */}
        <div className="p-5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-xs space-y-2">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Total Retained Knowledge
          </span>
          <div className="text-2xl font-black text-purple-600 dark:text-purple-400">
            {loading ? '...' : memories.length}
          </div>
          <p className="text-xs text-slate-500 truncate">
            {bankStatus?.hindsight_bank_id ? `Active Bank: ${bankStatus.hindsight_bank_id}` : 'Learned standards, resolved bugs, and developer preferences'}
          </p>
        </div>
      </div>

      {/* Interactive Semantic Recall Playground */}
      <div className="p-5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <div>
            <h2 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <Search className="w-4 h-4 text-purple-600 dark:text-purple-400" />
              Live Hindsight Semantic Recall Tester
            </h2>
            <p className="text-xs text-slate-500">
              Query the current project's memory bank using Hindsight's vector & graph search.
            </p>
          </div>
        </div>

        <div className="flex gap-2">
          <input
            type="text"
            value={recallQuery}
            onChange={(e) => setRecallQuery(e.target.value)}
            placeholder="Search query (e.g., SQL queries, security rules, preferences)..."
            className="flex-1 px-3.5 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs text-slate-900 dark:text-white focus:outline-hidden focus:ring-2 focus:ring-purple-500"
          />
          <button
            onClick={handleTestRecall}
            disabled={recalling || !selectedProjectId}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-xs"
          >
            {recalling ? 'Searching...' : 'Recall'}
          </button>
        </div>

        {recallResults && (
          <div className="p-3 bg-purple-50/50 dark:bg-purple-950/20 rounded-lg border border-purple-100 dark:border-purple-800/60 space-y-2">
            <h3 className="text-xs font-bold text-purple-900 dark:text-purple-300">
              Recalled Matches ({recallResults.length})
            </h3>
            {recallResults.length === 0 ? (
              <p className="text-xs text-slate-500">No relevant memories found for this query in this project bank.</p>
            ) : (
              <div className="space-y-2">
                {recallResults.map((r, i) => (
                  <div
                    key={i}
                    className="p-3 bg-white dark:bg-slate-800 rounded-md border border-purple-100 dark:border-purple-900 text-xs space-y-1"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-slate-900 dark:text-white">&ldquo;{r.text}&rdquo;</span>
                      {r.score && (
                        <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-sm bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300">
                          Score: {(r.score * 100).toFixed(0)}%
                        </span>
                      )}
                    </div>
                    {r.tags && r.tags.length > 0 && (
                      <div className="flex gap-1 pt-1">
                        {r.tags.map((t, tidx) => (
                          <span key={tidx} className="text-[10px] bg-slate-100 dark:bg-slate-700 px-1.5 rounded-sm">
                            #{t}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Retained Knowledge List */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-xs overflow-hidden">
        <div className="p-5 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-slate-900 dark:text-white">
              Retained Memories in Project Bank
            </h2>
            <p className="text-xs text-slate-500">
              Rules and lessons retained from developer-approved reviews and manual teachings.
            </p>
          </div>
          <button
            onClick={() => loadProjectMemory(selectedProjectId)}
            className="p-1.5 rounded-md hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500"
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>

        {memories.length === 0 ? (
          <div className="p-12 text-center text-slate-400 space-y-2">
            <Brain className="w-10 h-10 text-slate-300 dark:text-slate-700 mx-auto" />
            <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">No memories retained yet</p>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              When developers accept review findings or click "Teach Rule", confirmed lessons are stored into this project's memory bank.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100 dark:divide-slate-800">
            {memories.map((m, idx) => (
              <div key={idx} className="p-4 hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition-colors space-y-1.5">
                <div className="flex items-start justify-between gap-3">
                  <p className="text-xs font-medium text-slate-900 dark:text-slate-100 leading-relaxed">
                    {m.text}
                  </p>
                  <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-md bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-300 shrink-0">
                    {m.category || 'standards'}
                  </span>
                </div>

                <div className="flex items-center gap-3 text-[11px] text-slate-400">
                  {m.tags && m.tags.length > 0 && (
                    <div className="flex items-center gap-1">
                      <Tag className="w-3 h-3" />
                      <span>{m.tags.join(', ')}</span>
                    </div>
                  )}
                  {m.created_at && (
                    <div className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      <span>{new Date(m.created_at).toLocaleDateString()}</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Activity Log */}
      {activity.length > 0 && (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-xs overflow-hidden">
          <div className="p-5 border-b border-slate-100 dark:border-slate-800">
            <h2 className="text-base font-semibold text-slate-900 dark:text-white flex items-center gap-2">
              <Layers className="w-4 h-4 text-purple-600 dark:text-purple-400" />
              Memory Bank Activity History
            </h2>
            <p className="text-xs text-slate-500">
              Audit log of all memory retention and recall operations executed by the agent.
            </p>
          </div>
          <div className="divide-y divide-slate-100 dark:divide-slate-800">
            {activity.map((act) => (
              <div key={act.id} className="p-4 flex items-center justify-between text-xs">
                <div className="flex items-center gap-3">
                  <span className={`px-2 py-0.5 rounded-md font-mono text-[10px] font-bold uppercase ${
                    act.action === 'retain'
                      ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300'
                      : 'bg-purple-50 text-purple-700 dark:bg-purple-950 dark:text-purple-300'
                  }`}>
                    {act.action}
                  </span>
                  <span className="text-slate-800 dark:text-slate-200 font-medium">
                    {typeof act.details === 'object'
                      ? (act.details?.query || act.details?.summary || act.details?.content || JSON.stringify(act.details))
                      : String(act.details)}
                  </span>
                </div>
                <span className="text-slate-400 text-[11px]">
                  {new Date(act.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Retain Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-slate-900 rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200 dark:border-slate-800 space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-800">
              <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Brain className="w-5 h-5 text-purple-600" /> Teach Rule to Agent
              </h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleRetain} className="space-y-4">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Rule or Standard to Remember *
                </label>
                <textarea
                  rows={3}
                  required
                  placeholder="e.g. Always use parameterized queries for SQL. Enforce strict JWT token expiry."
                  value={retainForm.content}
                  onChange={(e) => setRetainForm({ ...retainForm, content: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-xs focus:ring-2 focus:ring-purple-500 focus:outline-hidden"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Category
                </label>
                <select
                  value={retainForm.category}
                  onChange={(e) => setRetainForm({ ...retainForm, category: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-xs focus:ring-2 focus:ring-purple-500 focus:outline-hidden"
                >
                  <option value="coding_standards">Coding Standards</option>
                  <option value="recurring_bugs">Recurring Bugs & Fixes</option>
                  <option value="vulnerabilities">Resolved Vulnerabilities</option>
                  <option value="developer_preferences">Developer Preferences</option>
                  <option value="architecture">Architectural Decisions</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Tags (comma separated)
                </label>
                <input
                  type="text"
                  placeholder="security, database, auth"
                  value={retainForm.tags}
                  onChange={(e) => setRetainForm({ ...retainForm, tags: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-xs focus:ring-2 focus:ring-purple-500 focus:outline-hidden"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-3.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 text-xs font-medium hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={retaining}
                  className="px-4 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-700 text-white text-xs font-semibold shadow-xs disabled:bg-purple-400"
                >
                  {retaining ? 'Retaining...' : 'Retain in Hindsight'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
