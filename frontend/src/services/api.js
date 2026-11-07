import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach JWT token to requests if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('reviewmind_token');
  if (token) {
    if (config.headers && typeof config.headers.set === 'function') {
      config.headers.set('Authorization', `Bearer ${token}`);
    } else {
      config.headers = config.headers || {};
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Intercept responses for auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // If unauthorized and on protected route, clear token and redirect
      const currentPath = window.location.pathname;
      if (currentPath !== '/login' && currentPath !== '/register') {
        localStorage.removeItem('reviewmind_token');
        localStorage.removeItem('reviewmind_user');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const authService = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  getMe: () => api.get('/auth/me'),
};

export const projectService = {
  list: () => api.get('/projects'),
  get: (id) => api.get(`/projects/${id}`),
  create: (data) => api.post('/projects', data),
  update: (id, data) => api.put(`/projects/${id}`, data),
  delete: (id) => api.delete(`/projects/${id}`),
};

export const reviewService = {
  submitReview: (data) => api.post('/reviews', data),
  quickReview: (data) => api.post('/reviews/quick', data),
  list: (params) => api.get('/reviews', { params }),
  get: (id) => api.get(`/reviews/${id}`),
  getFindings: (id) => api.get(`/reviews/${id}/findings`),
  submitFeedback: (reviewId, data) => api.post(`/reviews/${reviewId}/feedback`, data),
};

export const memoryService = {
  getStatus: () => api.get('/memory/status'),
  getProjectMemories: (projectId) => api.get(`/memory/${projectId}`),
  getProjectBankStatus: (projectId) => api.get(`/memory/${projectId}/status`),
  getActivity: (projectId) => api.get(`/memory/${projectId}/activity`),
  retainMemory: (projectId, data) => api.post(`/memory/${projectId}/retain`, data),
  recallMemories: (projectId, data) => api.post(`/memory/${projectId}/recall`, data),
};

export const githubService = {
  getStatus: () => api.get('/github/status'),
  connectToken: (token) => api.post('/github/connect-token', { personal_access_token: token }),
  disconnect: () => api.delete('/github/disconnect'),
  getRepositories: () => api.get('/github/repositories'),
  getPullRequests: (owner, repo) => api.get(`/github/repositories/${owner}/${repo}/pull-requests`),
  getPRFiles: (owner, repo, prNumber) => api.get(`/github/repositories/${owner}/${repo}/pull-requests/${prNumber}/files`),
  reviewPullRequest: (data) => api.post('/github/pull-requests/review', data),
  publishComment: (reviewId, data, repoFullName, prNumber) =>
    api.post(`/github/reviews/${reviewId}/publish`, data, {
      params: { repo_full_name: repoFullName, pr_number: prNumber },
    }),
};

export const healthService = {
  check: () => api.get('/health'),
  getDiagnostics: () => api.get('/health/diagnostics'),
};

export default api;
