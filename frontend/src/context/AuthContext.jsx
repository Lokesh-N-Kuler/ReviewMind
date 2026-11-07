import React, { createContext, useContext, useState, useEffect } from 'react';
import { authService } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('reviewmind_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState(() => localStorage.getItem('reviewmind_token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const verifyUser = async () => {
      const storedToken = localStorage.getItem('reviewmind_token');
      if (storedToken) {
        try {
          const res = await authService.getMe();
          setUser(res.data);
          localStorage.setItem('reviewmind_user', JSON.stringify(res.data));
        } catch {
          logout();
        }
      }
      setLoading(false);
    };
    verifyUser();
  }, []);

  const login = async (email, password) => {
    const res = await authService.login({ email, password });
    const { access_token, user: userData } = res.data;
    localStorage.setItem('reviewmind_token', access_token);
    localStorage.setItem('reviewmind_user', JSON.stringify(userData));
    setToken(access_token);
    setUser(userData);
    return userData;
  };

  const register = async (email, password, fullName) => {
    const res = await authService.register({ email, password, full_name: fullName });
    const { access_token, user: userData } = res.data;
    localStorage.setItem('reviewmind_token', access_token);
    localStorage.setItem('reviewmind_user', JSON.stringify(userData));
    setToken(access_token);
    setUser(userData);
    return userData;
  };

  const logout = () => {
    localStorage.removeItem('reviewmind_token');
    localStorage.removeItem('reviewmind_user');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token,
        loading,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
