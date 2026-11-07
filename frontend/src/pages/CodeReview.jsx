import React, { useState, useEffect, useRef } from 'react';
import Editor from '@monaco-editor/react';
import {
  Code2,
  Play,
  RotateCcw,
  Sparkles,
  ShieldAlert,
  AlertTriangle,
  Info,
  CheckCircle,
  Brain,
  ThumbsUp,
  ThumbsDown,
  Copy,
  Check,
  ChevronDown,
  FolderGit2,
  FileCode,
  ArrowRight,
  ExternalLink,
} from 'lucide-react';
import { projectService, reviewService } from '../services/api';
import { useTheme } from '../context/ThemeContext';

const SAMPLE_CODES = {
  sql_vulnerability_1: {
    title: 'Demo 1: SQL Injection via Concatenation',
    language: 'python',
    code: `def get_user_profile(user_id):
    # Vulnerable SQL concatenation
    query = "SELECT * FROM users WHERE id = " + user_id
    cursor = db.cursor()
    return cursor.execute(query)
`,
    explanation: 'Initial code review where ReviewMind detects SQL injection and recommends parameterized queries.'
  },
  sql_vulnerability_2: {
    title: 'Demo 2: Recurring SQL Issue (Memory Test)',
    language: 'python',
    code: `def find_orders_by_customer(customer_id):
    # Another query using string concatenation
    sql = "SELECT id, total, created_at FROM orders WHERE customer_id = " + customer_id
    return database.query(sql)
`,
    explanation: 'Second review on the same project: ReviewMind will recall previously established conventions from Hindsight!'
  },
  eval_rce: {
    title: 'Demo 3: Arbitrary Code Execution (eval)',
    language: 'python',
    code: `def calculate_dynamic_expression(user_formula):
    # Dangerous dynamic code evaluation
    result = eval(user_formula)
    return {"calculated": result}
`,
    explanation: 'Detects arbitrary code execution vulnerabilities.'
  },
  js_xss: {
    title: 'Demo 4: DOM XSS via innerHTML',
    language: 'javascript',
    code: `function renderUserProfile(userData) {
    const container = document.getElementById("profile");
    // Cross-site scripting vulnerability
    container.innerHTML = "<h3>" + userData.name + "</h3><p>" + userData.bio + "</p>";
}
`,
    explanation: 'Detects Cross-Site Scripting (XSS) in JavaScript.'
  }
};

export default function CodeReview() {
  const { theme } = useTheme();
  const [projects, setProjects] = useState([]);
  const [selectedProjectId, setSelectedProjectId] = useState('');
  const [language, setLanguage] = useState('python');
  const [sourceCode, setSourceCode] = useState(SAMPLE_CODES.sql_vulnerability_1.code);
  const [title, setTitle] = useState('Data Access Security Review');
  const [loading, setLoading] = useState(false);
  const [reviewResult, setReviewResult] = useState(null);
  const [error, setError] = useState(null);
  const [selectedFinding, setSelectedFinding] = useState(null);
  const [copiedId, setCopiedId] = useState(null);
  const [feedbackSuccess, setFeedbackSuccess] = useState({});

  const editorRef = useRef(null);

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const res = await projectService.list();
        setProjects(res.data || []);
        if (res.data && res.data.length > 0) {
          setSelectedProjectId(res.data[0].id);
        }
      } catch (err) {
        console.error('Failed to load projects:', err);
      }
    };
    fetchProjects();
  }, []);

  const handleEditorDidMount = (editor) => {
    editorRef.current = editor;
  };

  const handleSelectSample = (sampleKey) => {
    const sample = SAMPLE_CODES[sampleKey];
    if (sample) {
      setLanguage(sample.language);
      setSourceCode(sample.code);
      setTitle(sample.title);
      setReviewResult(null);
      setError(null);
    }
  };

  const handleLineJump = (lineNumber) => {
    if (editorRef.current && lineNumber) {
      editorRef.current.revealLineInCenter(lineNumber);
      editorRef.current.setPosition({ lineNumber, column: 1 });
      editorRef.current.focus();
    }
  };

  const handleSubmitReview = async () => {
    if (!sourceCode.trim()) {
      setError('Please provide source code to review.');
      return;
    }

    setLoading(true);
    setError(null);
    setSelectedFinding(null);

    try {
      let res;
      if (selectedProjectId) {
        res = await reviewService.submitReview({
          project_id: parseInt(selectedProjectId, 10),
          language,
          source_code: sourceCode,
          title: title || `${language.toUpperCase()} Review`,
          file_path: 'main'
        });
      } else {
        res = await reviewService.quickReview({
          language,
          source_code: sourceCode,
          file_path: 'main'
        });
      }

      setReviewResult(res.data);
      if (res.data.findings && res.data.findings.length > 0) {
        setSelectedFinding(res.data.findings[0]);
      }
    } catch (err) {
      console.error('Review failed:', err);
      setError(err.response?.data?.detail || 'Code review request failed. Please check backend status.');
    } finally {
      setLoading(false);
    }
  };

  const handleFeedback = async (findingId, feedbackType, comment = '') => {
    if (!reviewResult) return;
    try {
      await reviewService.submitFeedback(reviewResult.id, {
        finding_id: findingId,
        feedback_type: feedbackType,
        comment,
        retain_in_hindsight: true,
      });

      setFeedbackSuccess((prev) => ({
        ...prev,
        [findingId]: feedbackType === 'accepted' ? 'Accepted & retained into Hindsight' : 'Feedback recorded',
      }));
    } catch (err) {
      console.error('Failed to submit feedback:', err);
    }
  };

  const handleCopyFix = (snippet, id) => {
    navigator.clipboard.writeText(snippet);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] md:h-screen overflow-hidden">
      {/* Top Action Bar */}
      <div className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 px-6 py-3 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-blue-50 dark:bg-blue-950 text-blue-600 dark:text-blue-400">
            <Code2 className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-base font-semibold text-slate-900 dark:text-white">AI Code Review Studio</h1>
            <p className="text-xs text-slate-500">Persistent memory recall & AST static security inspection</p>
          </div>
        </div>

        {/* Project & Language Selectors */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Project Selector */}
          <div className="flex items-center gap-1.5 text-xs">
            <FolderGit2 className="w-4 h-4 text-slate-400" />
            <select
              value={selectedProjectId}
              onChange={(e) => setSelectedProjectId(e.target.value)}
              className="px-2.5 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-xs font-medium focus:outline-hidden focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Default Sandbox / Playground</option>
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  Project: {p.name}
                </option>
              ))}
            </select>
          </div>

          {/* Language Selector */}
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="px-2.5 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-xs font-medium focus:outline-hidden focus:ring-2 focus:ring-blue-500"
          >
            <option value="python">Python</option>
            <option value="javascript">JavaScript</option>
            <option value="typescript">TypeScript</option>
            <option value="sql">SQL</option>
            <option value="java">Java</option>
            <option value="cpp">C++</option>
          </select>

          {/* Sample Code Dropdown */}
          <div className="relative group">
            <button className="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 text-xs font-medium flex items-center gap-1">
              <Sparkles className="w-3.5 h-3.5 text-blue-500" />
              Load Sample Code
              <ChevronDown className="w-3.5 h-3.5" />
            </button>
            <div className="absolute right-0 top-full mt-1 w-64 bg-white dark:bg-slate-800 rounded-lg shadow-lg border border-slate-200 dark:border-slate-700 py-1 hidden group-hover:block z-50">
              {Object.entries(SAMPLE_CODES).map(([key, sample]) => (
                <button
                  key={key}
                  onClick={() => handleSelectSample(key)}
                  className="w-full text-left px-3 py-2 text-xs hover:bg-blue-50 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 block"
                >
                  <p className="font-semibold text-slate-900 dark:text-white">{sample.title}</p>
                  <p className="text-[10px] text-slate-500 truncate">{sample.explanation}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Review Button */}
          <button
            onClick={handleSubmitReview}
            disabled={loading}
            className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-4 py-1.5 rounded-lg text-xs font-semibold shadow-xs transition-colors"
          >
            {loading ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Analyzing with AI...
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                Review Code
              </>
            )}
          </button>
        </div>
      </div>

      {/* Two-Panel Layout */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 min-h-0 bg-slate-100 dark:bg-slate-950">
        {/* Left Panel: Monaco Editor (7 Cols on desktop) */}
        <div className="lg:col-span-7 flex flex-col border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 min-h-[350px]">
          <div className="px-4 py-2 bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between text-xs text-slate-500">
            <span className="flex items-center gap-1.5 font-medium text-slate-700 dark:text-slate-300">
              <FileCode className="w-4 h-4 text-blue-500" />
              Source Input Editor ({language})
            </span>
            <button
              onClick={() => {
                setSourceCode('');
                setReviewResult(null);
              }}
              className="hover:text-slate-700 dark:hover:text-slate-200 flex items-center gap-1"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              Clear
            </button>
          </div>

          <div className="flex-1 min-h-0">
            <Editor
              height="100%"
              language={language === 'c++' ? 'cpp' : language}
              value={sourceCode}
              onChange={(val) => setSourceCode(val || '')}
              theme={theme === 'dark' ? 'vs-dark' : 'light'}
              onMount={handleEditorDidMount}
              options={{
                minimap: { enabled: false },
                fontSize: 13,
                fontFamily: 'JetBrains Mono, Menlo, Monaco, Consolas, monospace',
                lineNumbers: 'on',
                scrollBeyondLastLine: false,
                wordWrap: 'on',
                automaticLayout: true,
                padding: { top: 12, bottom: 12 },
              }}
            />
          </div>
        </div>

        {/* Right Panel: Review Findings & Recalled Memory (5 Cols on desktop) */}
        <div className="lg:col-span-5 flex flex-col bg-white dark:bg-slate-900 overflow-y-auto min-h-0">
          {error && (
            <div className="p-4 m-4 rounded-xl bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-900 text-rose-800 dark:text-rose-200 text-xs">
              <div className="flex items-center gap-2 font-semibold">
                <ShieldAlert className="w-4 h-4 text-rose-600" />
                Review Alert
              </div>
              <p className="mt-1">{error}</p>
            </div>
          )}

          {!reviewResult && !loading && !error && (
            <div className="flex-1 flex flex-col items-center justify-center p-8 text-center text-slate-400 space-y-4">
              <div className="w-16 h-16 rounded-2xl bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 flex items-center justify-center shadow-xs">
                <Code2 className="w-8 h-8" />
              </div>
              <div className="max-w-xs">
                <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200">Ready for Code Review</h3>
                <p className="text-xs text-slate-500 mt-1">
                  Click "Review Code" above to trigger static AST parsing, recall project lessons from Hindsight, and receive AI explanations.
                </p>
              </div>
            </div>
          )}

          {loading && (
            <div className="flex-1 flex flex-col items-center justify-center p-8 text-center space-y-4">
              <div className="w-12 h-12 rounded-full border-4 border-blue-200 border-t-blue-600 animate-spin" />
              <div className="space-y-1">
                <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">Orchestrating Review Pipeline</p>
                <p className="text-xs text-slate-500">1. AST parsing &bull; 2. Recalling Hindsight memory &bull; 3. AI analysis</p>
              </div>
            </div>
          )}

          {reviewResult && (
            <div className="p-5 space-y-5">
              {/* Score & Summary Card */}
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700/80 space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-sm font-bold text-slate-900 dark:text-white">Review Summary</h2>
                    <p className="text-xs text-slate-500">Completed at {new Date(reviewResult.created_at).toLocaleTimeString()}</p>
                  </div>
                  <div
                    className={`text-base font-black px-3 py-1 rounded-full ${
                      reviewResult.score >= 80
                        ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300'
                        : reviewResult.score >= 60
                        ? 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300'
                        : 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300'
                    }`}
                  >
                    {reviewResult.score} / 100
                  </div>
                </div>

                <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed">{reviewResult.summary}</p>

                {/* Severity Breakdown Badges */}
                <div className="flex flex-wrap gap-2 pt-1 border-t border-slate-200/60 dark:border-slate-700/60 text-xs font-semibold">
                  <span className="px-2 py-0.5 rounded-md bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300">
                    {reviewResult.metrics?.critical || 0} Critical
                  </span>
                  <span className="px-2 py-0.5 rounded-md bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300">
                    {reviewResult.metrics?.high || 0} High
                  </span>
                  <span className="px-2 py-0.5 rounded-md bg-yellow-100 text-yellow-800 dark:bg-yellow-950/60 dark:text-yellow-300">
                    {reviewResult.metrics?.medium || 0} Medium
                  </span>
                  <span className="px-2 py-0.5 rounded-md bg-slate-200 text-slate-800 dark:bg-slate-700 dark:text-slate-200">
                    {reviewResult.metrics?.low || 0} Low
                  </span>
                </div>
              </div>

              {/* Recalled Memories Callout (From Hindsight) */}
              {reviewResult.recalled_memories && reviewResult.recalled_memories.length > 0 && (
                <div className="p-4 rounded-xl bg-purple-50/80 dark:bg-purple-950/40 border border-purple-200 dark:border-purple-800 space-y-2">
                  <div className="flex items-center gap-2 text-xs font-bold text-purple-900 dark:text-purple-300">
                    <Brain className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                    Persistent Knowledge Recalled by Hindsight ({reviewResult.recalled_memories.length})
                  </div>
                  <p className="text-[11px] text-purple-800 dark:text-purple-300">
                    The AI reviewed this code using lessons and conventions learned from previous reviews of this project:
                  </p>
                  <ul className="space-y-1.5 pt-1">
                    {reviewResult.recalled_memories.map((m, idx) => (
                      <li
                        key={idx}
                        className="text-xs text-purple-950 dark:text-purple-200 bg-white/70 dark:bg-purple-900/30 p-2 rounded-lg border border-purple-100 dark:border-purple-800/50"
                      >
                        <p className="font-medium">&ldquo;{m.text}&rdquo;</p>
                        {m.tags && m.tags.length > 0 && (
                          <div className="flex gap-1 mt-1">
                            {m.tags.map((t, tidx) => (
                              <span key={tidx} className="text-[10px] bg-purple-100 dark:bg-purple-800 px-1.5 rounded-sm">
                                #{t}
                              </span>
                            ))}
                          </div>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Retained Memories Callout (From Hindsight) */}
              {reviewResult.retained_memories && reviewResult.retained_memories.length > 0 && (
                <div className="p-4 rounded-xl bg-emerald-50/80 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 space-y-2">
                  <div className="flex items-center gap-2 text-xs font-bold text-emerald-900 dark:text-emerald-300">
                    <CheckCircle className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                    Validated Findings Retained into Hindsight ({reviewResult.retained_memories.length})
                  </div>
                  <p className="text-[11px] text-emerald-800 dark:text-emerald-300">
                    The following validated lessons were stored into this project's persistent memory bank:
                  </p>
                  <ul className="space-y-1 pt-1">
                    {reviewResult.retained_memories.map((ret, idx) => (
                      <li
                        key={idx}
                        className="text-xs text-emerald-950 dark:text-emerald-200 bg-white/70 dark:bg-emerald-900/30 p-2 rounded-lg border border-emerald-100 dark:border-emerald-800/50 font-medium"
                      >
                        {ret}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Findings List */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                    Detected Findings ({reviewResult.findings?.length || 0})
                  </h3>
                  <span className="text-[11px] text-slate-400">Click a finding to jump to code</span>
                </div>

                {reviewResult.findings?.map((f) => {
                  const isSelected = selectedFinding?.finding_id === f.finding_id;
                  const isCrit = f.severity === 'critical';
                  const isHigh = f.severity === 'high';

                  return (
                    <div
                      key={f.finding_id}
                      onClick={() => {
                        setSelectedFinding(f);
                        if (f.line_start) handleLineJump(f.line_start);
                      }}
                      className={`p-4 rounded-xl border transition-all cursor-pointer space-y-3 ${
                        isSelected
                          ? 'border-blue-500 bg-blue-50/20 dark:bg-blue-950/20 shadow-xs'
                          : 'border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 bg-white dark:bg-slate-900'
                      }`}
                    >
                      {/* Finding Header */}
                      <div className="flex items-start justify-between gap-2">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span
                              className={`text-[10px] font-bold px-2 py-0.5 rounded-md uppercase tracking-wider ${
                                isCrit
                                  ? 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300'
                                  : isHigh
                                  ? 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300'
                                  : 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300'
                              }`}
                            >
                              {f.severity}
                            </span>
                            <span className="text-xs font-mono text-slate-500">[{f.category}]</span>
                            {f.line_start && (
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleLineJump(f.line_start);
                                }}
                                className="text-xs font-mono text-blue-600 dark:text-blue-400 hover:underline"
                              >
                                Line {f.line_start}
                              </button>
                            )}
                          </div>
                          <h4 className="text-sm font-semibold text-slate-900 dark:text-white leading-snug">
                            {f.title}
                          </h4>
                        </div>
                      </div>

                      {/* Explanation */}
                      <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">{f.explanation}</p>

                      {/* Why it Matters */}
                      {f.why_it_matters && (
                        <div className="text-xs text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-800/50 p-2.5 rounded-lg border border-slate-100 dark:border-slate-800">
                          <span className="font-semibold text-slate-700 dark:text-slate-300">Why it matters: </span>
                          {f.why_it_matters}
                        </div>
                      )}

                      {/* Suggested Fix */}
                      {f.suggested_fix && (
                        <div className="text-xs text-slate-700 dark:text-slate-200 space-y-1">
                          <span className="font-semibold text-emerald-600 dark:text-emerald-400">Suggested Fix:</span>
                          <p>{f.suggested_fix}</p>
                        </div>
                      )}

                      {/* Corrected Code Snippet */}
                      {f.corrected_code && (
                        <div className="space-y-1">
                          <div className="flex items-center justify-between text-[11px] text-slate-500">
                            <span>Recommended Implementation:</span>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleCopyFix(f.corrected_code, f.finding_id);
                              }}
                              className="text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
                            >
                              {copiedId === f.finding_id ? (
                                <>
                                  <Check className="w-3 h-3" /> Copied!
                                </>
                              ) : (
                                <>
                                  <Copy className="w-3 h-3" /> Copy Snippet
                                </>
                              )}
                            </button>
                          </div>
                          <pre className="p-3 rounded-lg bg-slate-950 text-emerald-400 text-xs font-mono overflow-x-auto">
                            <code>{f.corrected_code}</code>
                          </pre>
                        </div>
                      )}

                      {/* Memory References */}
                      {f.memory_references && f.memory_references.length > 0 && (
                        <div className="text-[11px] text-purple-700 dark:text-purple-300 flex items-center gap-1.5 font-medium">
                          <Brain className="w-3.5 h-3.5" />
                          Grounded on memory: {f.memory_references.join(', ')}
                        </div>
                      )}

                      {/* Feedback & Retention Bar */}
                      <div className="pt-2 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
                        <span className="text-[11px] text-slate-400">Rate suggestion:</span>
                        <div className="flex items-center gap-2">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleFeedback(f.finding_id, 'accepted');
                            }}
                            className="px-2.5 py-1 rounded-md text-xs font-medium bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 hover:bg-emerald-100 flex items-center gap-1"
                          >
                            <ThumbsUp className="w-3 h-3" />
                            Accept & Remember
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleFeedback(f.finding_id, 'rejected');
                            }}
                            className="px-2.5 py-1 rounded-md text-xs font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 flex items-center gap-1"
                          >
                            <ThumbsDown className="w-3 h-3" />
                            Dismiss
                          </button>
                        </div>
                      </div>

                      {feedbackSuccess[f.finding_id] && (
                        <p className="text-[11px] text-emerald-600 dark:text-emerald-400 font-semibold text-right">
                          &bull; {feedbackSuccess[f.finding_id]}
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
