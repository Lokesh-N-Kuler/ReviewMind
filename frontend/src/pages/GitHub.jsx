import React, { useState, useEffect } from 'react';
import {
  Key,
  FolderGit2,
  GitPullRequest,
  Send,
  ExternalLink,
  ChevronRight,
} from 'lucide-react';
import GithubIcon from '../components/GithubIcon';
import { githubService, projectService } from '../services/api';

export default function GitHub() {
  const [status, setStatus] = useState(null);
  const [tokenInput, setTokenInput] = useState('');
  const [connecting, setConnecting] = useState(false);
  const [repos, setRepos] = useState([]);
  const [selectedRepo, setSelectedRepo] = useState(null);
  const [pullRequests, setPullRequests] = useState([]);
  const [selectedPR, setSelectedPR] = useState(null);
  const [prFiles, setPrFiles] = useState([]);
  const [reviewResult, setReviewResult] = useState(null);
  const [reviewing, setReviewing] = useState(false);
  const [projects, setProjects] = useState([]);
  const [selectedProjectId, setSelectedProjectId] = useState('');
  const [publishCommentText, setPublishCommentText] = useState('');
  const [publishing, setPublishing] = useState(false);
  const [publishSuccess, setPublishSuccess] = useState(null);

  const fetchStatusAndData = async () => {
    try {
      const res = await githubService.getStatus();
      setStatus(res.data);
      if (res.data?.connected) {
        const repoRes = await githubService.getRepositories();
        setRepos(repoRes.data || []);
      }
      const projRes = await projectService.list();
      setProjects(projRes.data || []);
      if (projRes.data?.length > 0) {
        setSelectedProjectId(projRes.data[0].id);
      }
    } catch (err) {
      console.error('Failed to load GitHub status:', err);
    }
  };

  useEffect(() => {
    fetchStatusAndData();
  }, []);

  const handleConnectToken = async (e) => {
    e.preventDefault();
    if (!tokenInput.trim()) return;
    setConnecting(true);
    try {
      await githubService.connectToken(tokenInput);
      setTokenInput('');
      await fetchStatusAndData();
    } catch (err) {
      alert('Failed to connect GitHub: ' + (err.response?.data?.detail || err.message));
    } finally {
      setConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    if (!window.confirm('Disconnect GitHub account?')) return;
    try {
      await githubService.disconnect();
      setRepos([]);
      setSelectedRepo(null);
      setSelectedPR(null);
      await fetchStatusAndData();
    } catch {
      alert('Failed to disconnect');
    }
  };

  const handleSelectRepo = async (repo) => {
    setSelectedRepo(repo);
    setSelectedPR(null);
    setPrFiles([]);
    setReviewResult(null);
    try {
      const [owner, name] = repo.full_name.split('/');
      const prRes = await githubService.getPullRequests(owner, name);
      setPullRequests(prRes.data || []);
    } catch (err) {
      console.error('Failed to fetch PRs:', err);
    }
  };

  const handleSelectPR = async (pr) => {
    setSelectedPR(pr);
    setReviewResult(null);
    setPublishSuccess(null);
    try {
      const [owner, repo] = selectedRepo.full_name.split('/');
      const filesRes = await githubService.getPRFiles(owner, repo, pr.number);
      setPrFiles(filesRes.data || []);
    } catch (err) {
      console.error('Failed to load PR files:', err);
    }
  };

  const handleReviewPR = async () => {
    if (!selectedPR || !selectedRepo || !selectedProjectId) {
      alert('Please select a project to associate with this PR review.');
      return;
    }
    setReviewing(true);
    try {
      const res = await githubService.reviewPullRequest({
        project_id: parseInt(selectedProjectId, 10),
        repo_full_name: selectedRepo.full_name,
        pr_number: selectedPR.number,
      });
      setReviewResult(res.data);
    } catch (err) {
      alert('PR Review failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setReviewing(false);
    }
  };

  const handlePublishComment = async (e) => {
    e.preventDefault();
    if (!publishCommentText.trim() || !reviewResult || !selectedRepo || !selectedPR) return;

    setPublishing(true);
    setPublishSuccess(null);
    try {
      await githubService.publishComment(
        reviewResult.id,
        { comment_body: publishCommentText },
        selectedRepo.full_name,
        selectedPR.number
      );
      setPublishSuccess('Review comment successfully published to GitHub PR!');
      setPublishCommentText('');
    } catch (err) {
      alert('Publishing failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setPublishing(false);
    }
  };

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto w-full space-y-6">
      {/* Header */}
      <div className="pb-4 border-b border-slate-200 dark:border-slate-800">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2.5">
          <GithubIcon className="w-6 h-6 text-slate-900 dark:text-white" />
          GitHub Pull Request Integration
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Inspect repositories, analyze Pull Request diffs, and publish developer-approved AI code reviews.
        </p>
      </div>

      {/* Connection State Panel */}
      {!status?.connected ? (
        <div className="p-6 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-xs space-y-4 max-w-xl">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-slate-100 dark:bg-slate-800 rounded-lg text-slate-800 dark:text-white">
              <Key className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900 dark:text-white">Connect GitHub Account</h2>
              <p className="text-xs text-slate-500">
                Provide a Personal Access Token with <code className="text-blue-600">repo</code> scope.
              </p>
            </div>
          </div>

          <form onSubmit={handleConnectToken} className="space-y-3">
            <div>
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                GitHub Token (PAT)
              </label>
              <input
                type="password"
                required
                placeholder="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                value={tokenInput}
                onChange={(e) => setTokenInput(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs text-slate-900 dark:text-white focus:outline-hidden focus:ring-2 focus:ring-blue-500 font-mono"
              />
              <p className="text-[11px] text-slate-400 mt-1">
                Your token is securely encrypted before being stored. Tokens are never exposed to the frontend.
              </p>
            </div>

            <button
              type="submit"
              disabled={connecting}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-xs disabled:bg-blue-400"
            >
              {connecting ? 'Verifying with GitHub...' : 'Connect GitHub'}
            </button>
          </form>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Connected User Bar */}
          <div className="p-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-xs flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-full bg-emerald-50 dark:bg-emerald-950 text-emerald-600 flex items-center justify-center font-bold text-xs">
                GH
              </div>
              <div>
                <p className="text-xs text-slate-500">Connected GitHub User:</p>
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                  @{status.github_username}
                </h3>
              </div>
            </div>

            <button
              onClick={handleDisconnect}
              className="text-xs text-rose-600 hover:text-rose-700 font-medium px-3 py-1.5 rounded-lg border border-rose-200 dark:border-rose-900 hover:bg-rose-50"
            >
              Disconnect
            </button>
          </div>

          {/* Repo & PR Selector */}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
            {/* Repositories List (4 Cols) */}
            <div className="md:col-span-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-xs space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                <FolderGit2 className="w-4 h-4 text-blue-500" />
                Repositories ({repos.length})
              </h3>

              <div className="space-y-1.5 max-h-96 overflow-y-auto">
                {repos.map((r) => {
                  const isSelected = selectedRepo?.id === r.id;
                  return (
                    <button
                      key={r.id}
                      onClick={() => handleSelectRepo(r)}
                      className={`w-full text-left p-2.5 rounded-lg text-xs transition-colors flex items-center justify-between ${
                        isSelected
                          ? 'bg-blue-50 dark:bg-blue-950 text-blue-700 dark:text-blue-300 font-semibold'
                          : 'hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300'
                      }`}
                    >
                      <span className="truncate">{r.full_name}</span>
                      <ChevronRight className="w-3.5 h-3.5 shrink-0 text-slate-400" />
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Pull Requests List (8 Cols) */}
            <div className="md:col-span-8 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-xs space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                  <GitPullRequest className="w-4 h-4 text-purple-500" />
                  Pull Requests {selectedRepo ? `for ${selectedRepo.name}` : ''}
                </h3>
              </div>

              {!selectedRepo ? (
                <div className="p-12 text-center text-slate-400 text-xs">
                  Select a repository from the left panel to inspect its open Pull Requests.
                </div>
              ) : pullRequests.length === 0 ? (
                <div className="p-12 text-center text-slate-400 text-xs">
                  No open pull requests found for {selectedRepo.full_name}.
                </div>
              ) : (
                <div className="space-y-2">
                  {pullRequests.map((pr) => {
                    const isSelected = selectedPR?.id === pr.id;
                    return (
                      <div
                        key={pr.id}
                        onClick={() => handleSelectPR(pr)}
                        className={`p-3.5 rounded-lg border transition-all cursor-pointer flex items-center justify-between ${
                          isSelected
                            ? 'border-purple-500 bg-purple-50/20 dark:bg-purple-950/20'
                            : 'border-slate-200 dark:border-slate-800 hover:border-slate-300'
                        }`}
                      >
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-mono font-bold text-purple-600">#{pr.number}</span>
                            <h4 className="text-sm font-semibold text-slate-900 dark:text-white">{pr.title}</h4>
                          </div>
                          <p className="text-xs text-slate-400">
                            By @{pr.author} &bull; {pr.head_branch} &rarr; {pr.base_branch}
                          </p>
                        </div>

                        <a
                          href={pr.html_url}
                          target="_blank"
                          rel="noreferrer"
                          onClick={(e) => e.stopPropagation()}
                          className="text-slate-400 hover:text-slate-600 p-1"
                        >
                          <ExternalLink className="w-4 h-4" />
                        </a>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>

          {/* Selected PR Review Inspector */}
          {selectedPR && (
            <div className="p-6 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-xs space-y-5">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-3 border-b border-slate-100 dark:border-slate-800">
                <div>
                  <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                    Review PR #{selectedPR.number}: {selectedPR.title}
                  </h3>
                  <p className="text-xs text-slate-500">
                    {prFiles.length} modified file(s) identified in this pull request
                  </p>
                </div>

                <div className="flex items-center gap-3">
                  <select
                    value={selectedProjectId}
                    onChange={(e) => setSelectedProjectId(e.target.value)}
                    className="px-2.5 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs font-medium"
                  >
                    {projects.map((p) => (
                      <option key={p.id} value={p.id}>
                        Target Project: {p.name}
                      </option>
                    ))}
                  </select>

                  <button
                    onClick={handleReviewPR}
                    disabled={reviewing}
                    className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-xs font-semibold shadow-xs disabled:bg-blue-400"
                  >
                    {reviewing ? 'Running ReviewMind Analysis...' : 'Review PR with ReviewMind'}
                  </button>
                </div>
              </div>

              {/* Review Output */}
              {reviewResult && (
                <div className="space-y-4 pt-2">
                  <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-700 dark:text-slate-300">
                        PR Quality Score: {reviewResult.score}/100
                      </span>
                      <span className="text-xs font-semibold text-rose-600">
                        {reviewResult.metrics?.critical || 0} Critical &bull; {reviewResult.metrics?.high || 0} High Issues
                      </span>
                    </div>
                    <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                      {reviewResult.summary}
                    </p>
                  </div>

                  {/* Findings */}
                  <div className="space-y-3">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                      PR Findings ({reviewResult.findings?.length || 0})
                    </h4>
                    {reviewResult.findings?.map((f, idx) => (
                      <div
                        key={idx}
                        className="p-3.5 rounded-lg border border-slate-200 dark:border-slate-800 space-y-1.5 text-xs"
                      >
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-[10px] uppercase px-1.5 py-0.5 rounded-sm bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300">
                            {f.severity}
                          </span>
                          <span className="font-bold text-slate-900 dark:text-white">{f.title}</span>
                          {f.line_start && <span className="font-mono text-slate-400">Line {f.line_start}</span>}
                        </div>
                        <p className="text-slate-600 dark:text-slate-300">{f.explanation}</p>
                        {f.suggested_fix && (
                          <div className="text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/20 p-2 rounded-sm">
                            <span className="font-semibold">Suggested Fix: </span>
                            {f.suggested_fix}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>

                  {/* Developer Approval & Publish Box */}
                  <div className="p-4 rounded-xl border border-blue-200 dark:border-blue-900 bg-blue-50/30 dark:bg-blue-950/20 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-blue-900 dark:text-blue-300 flex items-center gap-1.5">
                        <Send className="w-3.5 h-3.5" />
                        Developer Approval: Publish Review Comment to GitHub
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-500">
                      As mandated by safety requirements, ReviewMind never publishes comments automatically without your explicit approval.
                    </p>

                    <form onSubmit={handlePublishComment} className="space-y-2">
                      <textarea
                        rows={3}
                        required
                        placeholder="Write or customize the final review comment to publish to the GitHub PR thread..."
                        value={publishCommentText}
                        onChange={(e) => setPublishCommentText(e.target.value)}
                        className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs text-slate-900 dark:text-white focus:outline-hidden focus:ring-2 focus:ring-blue-500"
                      />

                      <div className="flex items-center justify-between">
                        <button
                          type="button"
                          onClick={() => {
                            const summaryText = `### ReviewMind AI Code Review Report\n**Score**: ${reviewResult.score}/100\n\n${reviewResult.summary}\n\n**Key Findings**:\n` +
                              reviewResult.findings.map(f => `- **[${f.severity.toUpperCase()}]** ${f.title}: ${f.suggested_fix}`).join('\n');
                            setPublishCommentText(summaryText);
                          }}
                          className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
                        >
                          Auto-populate from review report
                        </button>

                        <button
                          type="submit"
                          disabled={publishing || !publishCommentText.trim()}
                          className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-xs disabled:bg-blue-400"
                        >
                          {publishing ? 'Publishing...' : 'Approve & Publish to GitHub'}
                        </button>
                      </div>
                    </form>

                    {publishSuccess && (
                      <p className="text-xs text-emerald-600 font-semibold pt-1">
                        &bull; {publishSuccess}
                      </p>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
