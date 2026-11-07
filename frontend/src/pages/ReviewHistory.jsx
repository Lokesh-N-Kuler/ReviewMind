import React, { useState, useEffect } from 'react';
import {
  History,
  Search,
  Code2,
  Brain,
  ChevronRight,
  Calendar,
  X,
  Copy,
  Check,
} from 'lucide-react';
import { reviewService, projectService } from '../services/api';

export default function ReviewHistory() {
  const [reviews, setReviews] = useState([]);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedProjectFilter, setSelectedProjectFilter] = useState('');
  const [selectedSeverityFilter, setSelectedSeverityFilter] = useState('');
  const [selectedReview, setSelectedReview] = useState(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [revRes, projRes] = await Promise.all([
          reviewService.list({ limit: 100 }),
          projectService.list(),
        ]);
        setReviews(revRes.data || []);
        setProjects(projRes.data || []);
      } catch (err) {
        console.error('Failed to load review history:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const filteredReviews = reviews.filter((r) => {
    const matchesSearch =
      r.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.language?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.summary?.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesProject = !selectedProjectFilter || r.project_id === parseInt(selectedProjectFilter, 10);

    const matchesSeverity =
      !selectedSeverityFilter ||
      (r.metrics && (r.metrics[selectedSeverityFilter.toLowerCase()] || 0) > 0);

    return matchesSearch && matchesProject && matchesSeverity;
  });

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto w-full space-y-6">
      {/* Header */}
      <div className="pb-4 border-b border-slate-200 dark:border-slate-800">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
          <History className="w-6 h-6 text-blue-600" />
          Review History
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Historical record of all AI inspections, quality metrics, and persistent memory associations.
        </p>
      </div>

      {/* Filter and Search Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by title, language, or content..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs text-slate-900 dark:text-white focus:outline-hidden focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <select
          value={selectedProjectFilter}
          onChange={(e) => setSelectedProjectFilter(e.target.value)}
          className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs text-slate-900 dark:text-white focus:outline-hidden focus:ring-2 focus:ring-blue-500 font-medium"
        >
          <option value="">All Projects</option>
          {projects.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>

        <select
          value={selectedSeverityFilter}
          onChange={(e) => setSelectedSeverityFilter(e.target.value)}
          className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs text-slate-900 dark:text-white focus:outline-hidden focus:ring-2 focus:ring-blue-500 font-medium"
        >
          <option value="">All Severities</option>
          <option value="critical">Has Critical Issues</option>
          <option value="high">Has High Issues</option>
          <option value="medium">Has Medium Issues</option>
          <option value="low">Has Low Issues</option>
        </select>
      </div>

      {/* Review List */}
      {loading ? (
        <div className="p-12 text-center text-slate-400">Loading historical reviews...</div>
      ) : filteredReviews.length === 0 ? (
        <div className="p-12 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-center space-y-2">
          <Code2 className="w-10 h-10 text-slate-300 dark:text-slate-700 mx-auto" />
          <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">No matching reviews found</p>
          <p className="text-xs text-slate-500">Try adjusting your filters or submit a new review in the Code Review studio.</p>
        </div>
      ) : (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-xs overflow-hidden divide-y divide-slate-100 dark:divide-slate-800">
          {filteredReviews.map((r) => (
            <div
              key={r.id}
              onClick={() => setSelectedReview(r)}
              className="p-5 hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition-colors cursor-pointer flex flex-col md:flex-row md:items-center justify-between gap-4"
            >
              <div className="space-y-1.5 flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold text-slate-900 dark:text-white truncate">
                    {r.title}
                  </span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 uppercase">
                    {r.language}
                  </span>
                  {r.recalled_memories && r.recalled_memories.length > 0 && (
                    <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-purple-100 dark:bg-purple-950 text-purple-700 dark:text-purple-300 flex items-center gap-1">
                      <Brain className="w-3 h-3" />
                      {r.recalled_memories.length} recalled
                    </span>
                  )}
                </div>

                <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-1">{r.summary}</p>

                <div className="flex items-center gap-3 text-xs text-slate-400 pt-0.5">
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3.5 h-3.5" />
                    {new Date(r.created_at).toLocaleString()}
                  </span>
                  <span>&bull;</span>
                  <span>{r.findings?.length || 0} findings</span>
                </div>
              </div>

              {/* Metrics Pills & Score */}
              <div className="flex items-center gap-4 shrink-0">
                <div className="flex items-center gap-2 text-xs font-semibold">
                  {(r.metrics?.critical || 0) > 0 && (
                    <span className="px-2 py-0.5 rounded-md bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300">
                      {r.metrics.critical} crit
                    </span>
                  )}
                  {(r.metrics?.high || 0) > 0 && (
                    <span className="px-2 py-0.5 rounded-md bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300">
                      {r.metrics.high} high
                    </span>
                  )}
                </div>

                <div
                  className={`text-sm font-black px-3 py-1 rounded-full ${
                    r.score >= 80
                      ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300'
                      : r.score >= 60
                      ? 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300'
                      : 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300'
                  }`}
                >
                  {r.score}/100
                </div>

                <ChevronRight className="w-5 h-5 text-slate-400" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Review Details Modal */}
      {selectedReview && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-slate-900 rounded-2xl max-w-3xl w-full max-h-[85vh] flex flex-col shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden">
            {/* Header */}
            <div className="p-5 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  {selectedReview.title}
                  <span className="text-xs px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 font-mono">
                    {selectedReview.language}
                  </span>
                </h3>
                <p className="text-xs text-slate-500">
                  Reviewed on {new Date(selectedReview.created_at).toLocaleString()}
                </p>
              </div>

              <button
                onClick={() => setSelectedReview(null)}
                className="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-5">
              {/* Score & Summary */}
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700/60 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase">
                    Quality Evaluation
                  </span>
                  <span className="text-sm font-black text-blue-600 dark:text-blue-400">
                    Score: {selectedReview.score}/100
                  </span>
                </div>
                <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                  {selectedReview.summary}
                </p>
              </div>

              {/* Source Code */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Submitted Source Code:
                  </span>
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(selectedReview.source_code);
                      setCopied(true);
                      setTimeout(() => setCopied(false), 2000);
                    }}
                    className="text-xs text-blue-600 dark:text-blue-400 flex items-center gap-1 hover:underline"
                  >
                    {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                    Copy
                  </button>
                </div>
                <pre className="p-3 bg-slate-950 text-slate-200 text-xs font-mono rounded-lg overflow-x-auto max-h-48">
                  <code>{selectedReview.source_code}</code>
                </pre>
              </div>

              {/* Recalled Memories */}
              {selectedReview.recalled_memories && selectedReview.recalled_memories.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-purple-600 dark:text-purple-400 flex items-center gap-1.5">
                    <Brain className="w-3.5 h-3.5" />
                    Recalled Hindsight Memories ({selectedReview.recalled_memories.length})
                  </h4>
                  <div className="space-y-2">
                    {selectedReview.recalled_memories.map((mem, idx) => (
                      <div
                        key={idx}
                        className="p-3 bg-purple-50/50 dark:bg-purple-950/20 rounded-lg border border-purple-100 dark:border-purple-900 text-xs text-purple-900 dark:text-purple-300 font-medium"
                      >
                        {typeof mem === 'string' ? mem : mem.text || mem.content || JSON.stringify(mem)}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Findings */}
              <div className="space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Findings ({selectedReview.findings?.length || 0})
                </h4>

                {selectedReview.findings?.map((f, i) => (
                  <div
                    key={i}
                    className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 space-y-2 text-xs"
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-bold uppercase text-[10px] px-2 py-0.5 rounded-md bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300">
                        {f.severity}
                      </span>
                      <span className="font-bold text-slate-900 dark:text-white">{f.title}</span>
                      {f.line_start && (
                        <span className="text-slate-400 font-mono">Line {f.line_start}</span>
                      )}
                    </div>
                    <p className="text-slate-600 dark:text-slate-300">{f.explanation}</p>
                    {f.suggested_fix && (
                      <div className="text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/30 p-2 rounded-md">
                        <span className="font-semibold">Fix: </span>
                        {f.suggested_fix}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
