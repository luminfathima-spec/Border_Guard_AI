import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import type { User } from '../types';
import { authApi } from '../services/sentinelApi';

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (token: string, user: User) => void;
  logout: () => void;
  isAdmin: boolean;
  isAnalyst: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('sentinel_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem('sentinel_token');
  });
  const [loading, setLoading] = useState<boolean>(true);

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('sentinel_token');
    localStorage.removeItem('sentinel_user');
  };

  useEffect(() => {
    if (token) {
      authApi.getMe()
        .then((userData) => {
          setUser(userData);
          localStorage.setItem('sentinel_user', JSON.stringify(userData));
        })
        .catch(() => {
          logout();
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [token]);

  const login = (newToken: string, newUser: User) => {
    setToken(newToken);
    setUser(newUser);
    localStorage.setItem('sentinel_token', newToken);
    localStorage.setItem('sentinel_user', JSON.stringify(newUser));
  };

  const isAdmin = user?.role === 'ADMIN';
  const isAnalyst = user?.role === 'ADMIN' || user?.role === 'SECURITY_ANALYST';

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout, isAdmin, isAnalyst }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
