# AMPRO License System - Authentication Guide

## Overview

This document provides detailed information about the authentication system in the AMPRO License System. It covers how authentication works, where tokens are generated, how to implement the authentication flow in the frontend, and best practices for token management.

## Authentication Flow

The AMPRO License System uses JWT (JSON Web Token) based authentication. Here's the complete authentication flow:

1. **User Login**:
   - User enters credentials (username/email and password)
   - Frontend sends credentials to the authentication endpoint
   - Backend validates credentials and returns access and refresh tokens
   - Frontend stores tokens and redirects to the dashboard

2. **Token Usage**:
   - Frontend attaches the access token to every API request in the Authorization header
   - Backend validates the token for each protected endpoint
   - If the token is valid, the request is processed

3. **Token Renewal**:
   - When the access token expires, use the refresh token to get a new access token
   - If the refresh token is expired, user must log in again

4. **Logout**:
   - Clear tokens from storage
   - Optionally, invalidate the tokens on the server

## API Endpoints

### Authentication Endpoints

#### Login
```
POST /api/v1/auth/login
```

**Request Body**:
```json
{
  "username": "user@example.com",
  "password": "secure_password"
}
```

**Response (200 OK)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "user@example.com",
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "officer",
    "is_active": true
  }
}
```

#### Get New Access Token
```
POST /api/v1/auth/token
```

**Request Body**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### Get Current User Information
```
GET /api/v1/auth/me
```

**Headers**:
```
Authorization: Bearer {access_token}
```

**Response (200 OK)**:
```json
{
  "id": 1,
  "username": "user@example.com",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "officer",
  "is_active": true
}
```

## Token Generation and Management

### Where Tokens Are Generated

Tokens are generated on the backend server:

1. **Access Token**:
   - Generated when a user successfully logs in
   - Generated when a refresh token is used to request a new access token
   - Contains user identification and permissions (claims)
   - Short expiry (typically 15-60 minutes)

2. **Refresh Token**:
   - Generated only during the login process
   - Longer expiry (typically 7-30 days)
   - Used only to obtain new access tokens

### Token Storage in Frontend

Best practices for token storage:

1. **Access Token**:
   - Store in memory (JavaScript variable) for the most secure approach
   - Alternatively, store in localStorage or sessionStorage for persistence

2. **Refresh Token**:
   - Preferably store in an HttpOnly cookie (if your architecture supports it)
   - Can also be stored in localStorage, but with increased security risk

Example for storage implementation:

```typescript
// auth.service.ts
class AuthService {
  private accessToken: string | null = null;
  private refreshToken: string | null = null;
  
  // Store tokens after login
  storeTokens(accessToken: string, refreshToken: string): void {
    this.accessToken = accessToken;
    this.refreshToken = refreshToken;
    
    // For persistence across page refreshes
    localStorage.setItem('refreshToken', refreshToken);
  }
  
  // Get access token for API requests
  getAccessToken(): string | null {
    return this.accessToken;
  }
  
  // Get refresh token for renewal
  getRefreshToken(): string | null {
    return this.refreshToken || localStorage.getItem('refreshToken');
  }
  
  // Clear tokens on logout
  clearTokens(): void {
    this.accessToken = null;
    this.refreshToken = null;
    localStorage.removeItem('refreshToken');
  }
}
```

## Implementing Authentication in React

### Authentication Context

Create an authentication context to manage the auth state across your application:

```tsx
// src/contexts/AuthContext.tsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../api/api';

interface User {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  
  // Check if user is already logged in on app load
  useEffect(() => {
    const initAuth = async () => {
      try {
        const storedRefreshToken = localStorage.getItem('refreshToken');
        if (storedRefreshToken) {
          await refreshToken();
        }
      } catch (error) {
        console.error('Failed to initialize auth:', error);
      } finally {
        setIsLoading(false);
      }
    };
    
    initAuth();
  }, []);
  
  // Login function
  const login = async (username: string, password: string) => {
    setIsLoading(true);
    try {
      const response = await api.post('/auth/login', { username, password });
      const { access_token, refresh_token, user } = response.data;
      
      // Store tokens
      api.setAuthToken(access_token);
      localStorage.setItem('refreshToken', refresh_token);
      
      // Update state
      setUser(user);
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };
  
  // Logout function
  const logout = () => {
    // Clear tokens
    api.setAuthToken(null);
    localStorage.removeItem('refreshToken');
    
    // Update state
    setUser(null);
  };
  
  // Token refresh function
  const refreshToken = async () => {
    const storedRefreshToken = localStorage.getItem('refreshToken');
    if (!storedRefreshToken) return;
    
    try {
      const response = await api.post('/auth/token', { 
        refresh_token: storedRefreshToken 
      });
      const { access_token } = response.data;
      
      // Update access token
      api.setAuthToken(access_token);
      
      // Get user data
      const userResponse = await api.get('/auth/me');
      setUser(userResponse.data);
    } catch (error) {
      console.error('Token refresh failed:', error);
      logout();
      throw error;
    }
  };
  
  const value = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    refreshToken
  };
  
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
```

### API Service with Token Management

Create a centralized API service to handle authentication headers:

```typescript
// src/api/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL + '/api/v1'
});

// Add auth token to requests
api.setAuthToken = (token: string | null) => {
  if (token) {
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    delete api.defaults.headers.common['Authorization'];
  }
};

// Add interceptor for token expiration
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // If error is 401 (Unauthorized) and not already retrying
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        // Get the refresh token from storage
        const refreshToken = localStorage.getItem('refreshToken');
        if (!refreshToken) {
          throw new Error('No refresh token available');
        }
        
        // Get new access token
        const response = await axios.post(
          `${process.env.REACT_APP_API_URL}/api/v1/auth/token`,
          { refresh_token: refreshToken }
        );
        
        const { access_token } = response.data;
        
        // Update access token in API service
        api.setAuthToken(access_token);
        
        // Retry the original request
        return api(originalRequest);
      } catch (refreshError) {
        // If refresh fails, redirect to login
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

export default api;
```

### Login Component

Implement a login form:

```tsx
// src/pages/Login.tsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const Login: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login, isLoading } = useAuth();
  const navigate = useNavigate();
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    try {
      await login(username, password);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed. Please check your credentials.');
    }
  };
  
  return (
    <div className="login-container">
      <h1>AMPRO License System</h1>
      <form onSubmit={handleSubmit}>
        {error && <div className="error-message">{error}</div>}
        
        <div className="form-group">
          <label htmlFor="username">Username</label>
          <input
            type="text"
            id="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="password">Password</label>
          <input
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        
        <button type="submit" disabled={isLoading}>
          {isLoading ? 'Logging in...' : 'Login'}
        </button>
      </form>
    </div>
  );
};

export default Login;
```

### Protected Route Component

Create a component to protect routes that require authentication:

```tsx
// src/components/ProtectedRoute.tsx
import React from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

interface ProtectedRouteProps {
  requiredRole?: string | string[];
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ requiredRole }) => {
  const { user, isAuthenticated, isLoading } = useAuth();
  const location = useLocation();
  
  // Show loading state
  if (isLoading) {
    return <div>Loading...</div>;
  }
  
  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  
  // Check role permissions if required
  if (requiredRole && user) {
    const roles = Array.isArray(requiredRole) ? requiredRole : [requiredRole];
    if (!roles.includes(user.role)) {
      return <Navigate to="/unauthorized" replace />;
    }
  }
  
  // Render the protected content
  return <Outlet />;
};

export default ProtectedRoute;
```

### Using the Protected Routes

Set up your routes with protection:

```tsx
// src/App.tsx
import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';

// Pages
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import CitizensList from './pages/citizens/CitizensList';
import AdminPanel from './pages/admin/AdminPanel';

const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<Login />} />
          
          {/* Protected routes - any authenticated user */}
          <Route element={<ProtectedRoute />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/citizens" element={<CitizensList />} />
          </Route>
          
          {/* Protected routes - admin only */}
          <Route element={<ProtectedRoute requiredRole="admin" />}>
            <Route path="/admin" element={<AdminPanel />} />
          </Route>
          
          {/* Redirect to dashboard if logged in, otherwise to login */}
          <Route path="*" element={<Navigate to="/dashboard" />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
};

export default App;
```

## Security Best Practices

1. **Access Token Security**:
   - Never store sensitive information in JWT payload
   - Use short expiration times (15-60 minutes)
   - Always validate tokens on the server

2. **HTTPS Usage**:
   - Always use HTTPS in production
   - Set the `secure` flag on cookies

3. **XSS Protection**:
   - Sanitize all user inputs
   - Use React's built-in protection against XSS
   - Consider using Content Security Policy

4. **CSRF Protection**:
   - Use anti-CSRF tokens for critical operations
   - Implement proper CORS configuration

5. **Token Invalidation**:
   - Implement token blacklisting for logged-out users
   - Use token rotation strategy for refresh tokens

## Troubleshooting

### Common Authentication Issues

1. **"Invalid token" errors**:
   - The token may have expired
   - The token signature may be invalid
   - Solution: Request a new token or log in again

2. **"Unauthorized" responses (HTTP 401)**:
   - Missing Authorization header
   - Token expired or invalid
   - Solution: Check that the token is being sent correctly

3. **"Forbidden" responses (HTTP 403)**:
   - User doesn't have permission for the requested resource
   - Solution: Check user roles and permissions

4. **Refresh token not working**:
   - Refresh token may have expired
   - Refresh token may have been invalidated
   - Solution: Redirect to login page

## Additional Resources

- [JWT.io](https://jwt.io/) - Decode and verify JWTs
- [React Router Documentation](https://reactrouter.com/en/main)
- [Axios Documentation](https://axios-http.com/docs/intro)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html) 