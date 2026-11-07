import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import MainLayout from './layouts/MainLayout';
import Dashboard from './pages/Dashboard';
import CodeReview from './pages/CodeReview';
import Projects from './pages/Projects';
import GitHub from './pages/GitHub';
import ReviewHistory from './pages/ReviewHistory';
import Memory from './pages/Memory';
import Settings from './pages/Settings';
import Login from './pages/Login';
import Register from './pages/Register';

// Route Guard enforcing authentication on protected application routes
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950 text-slate-600 dark:text-slate-300 font-sans">
        Loading ReviewMind...
      </div>
    );
  }
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />

            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <MainLayout />
                </ProtectedRoute>
              }
            >
              <Route index element={<Dashboard />} />
              <Route path="review" element={<CodeReview />} />
              <Route path="projects" element={<Projects />} />
              <Route path="github" element={<GitHub />} />
              <Route path="history" element={<ReviewHistory />} />
              <Route path="memory" element={<Memory />} />
              <Route path="settings" element={<Settings />} />
            </Route>

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}
