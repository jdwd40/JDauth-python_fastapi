# JDauth FastAPI Frontend Integration Guide

This document provides comprehensive instructions for LLMs building frontend applications that integrate with the JDauth FastAPI authentication service.

## 🎯 **Overview for Frontend Developers**

JDauth FastAPI is a secure authentication service with JWT tokens. This guide provides everything needed to build a frontend that integrates seamlessly with the API.

**Key Integration Points**:
- User registration and login
- JWT token management  
- Protected route access
- Profile management
- Error handling
- Security considerations

## 🔧 **API Configuration**

### **Base URLs**
```javascript
const API_CONFIG = {
    BASE_URL: 'http://localhost:8000',
    API_BASE: 'http://localhost:8000/api',
    ENDPOINTS: {
        HEALTH: '/health',
        REGISTER: '/api/auth/register',
        LOGIN: '/api/auth/login', 
        REFRESH: '/api/auth/refresh',
        PROFILE: '/api/user/profile',
        PROTECTED: '/api/user/protected',
        USERS_LIST: '/api/users'
    }
};
```

### **Authentication Headers**
```javascript
const AUTH_HEADER = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
};
```

## 🔐 **Authentication Flow Implementation**

### **1. User Registration**

**Endpoint**: `POST /api/auth/register`

**Request**:
```javascript
const registerUser = async (username, password) => {
    const response = await fetch(`${API_CONFIG.API_BASE}/auth/register`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            username: username,
            password: password
        })
    });
    
    const data = await response.json();
    
    if (response.ok) {
        // Success - user registered
        return {
            success: true,
            userId: data.user_id,
            message: data.message
        };
    } else {
        // Error - registration failed
        return {
            success: false,
            error: data.message,
            statusCode: data.status_code
        };
    }
};
```

**Success Response (201)**:
```json
{
    "message": "User created successfully",
    "user_id": 123
}
```

**Error Response (400)**:
```json
{
    "error": true,
    "message": "Username already exists",
    "status_code": 400,
    "timestamp": "2025-09-12T21:00:00Z"
}
```

**Validation Rules**:
- Username: 3-50 characters, alphanumeric + underscore
- Password: 8+ characters, any printable characters

### **2. User Login**

**Endpoint**: `POST /api/auth/login`

**Request**:
```javascript
const loginUser = async (username, password) => {
    const response = await fetch(`${API_CONFIG.API_BASE}/auth/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            username: username,
            password: password
        })
    });
    
    const data = await response.json();
    
    if (response.ok) {
        // Success - store token
        localStorage.setItem('auth_token', data.access_token);
        localStorage.setItem('token_expires', Date.now() + (data.expires_in * 1000));
        
        return {
            success: true,
            token: data.access_token,
            expiresIn: data.expires_in
        };
    } else {
        // Error - login failed
        return {
            success: false,
            error: data.message,
            statusCode: data.status_code
        };
    }
};
```

**Success Response (200)**:
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 1800
}
```

**Error Response (401)**:
```json
{
    "error": true,
    "message": "Invalid credentials",
    "status_code": 401,
    "timestamp": "2025-09-12T21:00:00Z"
}
```

### **3. Token Management**

**Token Storage**:
```javascript
// Store token securely
const storeToken = (tokenData) => {
    localStorage.setItem('auth_token', tokenData.access_token);
    localStorage.setItem('token_expires', Date.now() + (tokenData.expires_in * 1000));
    localStorage.setItem('token_type', tokenData.token_type);
};

// Get stored token
const getToken = () => {
    return localStorage.getItem('auth_token');
};

// Check if token is expired
const isTokenExpired = () => {
    const expires = localStorage.getItem('token_expires');
    if (!expires) return true;
    return Date.now() >= parseInt(expires);
};

// Clear token (logout)
const clearToken = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('token_expires');
    localStorage.removeItem('token_type');
};
```

**Token Refresh**:
```javascript
const refreshToken = async () => {
    const currentToken = getToken();
    if (!currentToken) return { success: false, error: 'No token to refresh' };
    
    const response = await fetch(`${API_CONFIG.API_BASE}/auth/refresh`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${currentToken}`
        }
    });
    
    const data = await response.json();
    
    if (response.ok) {
        storeToken(data);
        return { success: true, token: data.access_token };
    } else {
        clearToken(); // Clear invalid token
        return { success: false, error: data.message };
    }
};
```

## 👤 **User Profile Management**

### **Get User Profile**

**Endpoint**: `GET /api/user/profile`

**Request**:
```javascript
const getUserProfile = async () => {
    const token = getToken();
    if (!token) return { success: false, error: 'Not authenticated' };
    
    const response = await fetch(`${API_CONFIG.API_BASE}/user/profile`, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
    
    const data = await response.json();
    
    if (response.ok) {
        return {
            success: true,
            user: {
                id: data.id,
                username: data.username,
                createdAt: data.created_at
            }
        };
    } else {
        if (response.status === 401) {
            clearToken(); // Token invalid
        }
        return { success: false, error: data.message };
    }
};
```

**Success Response (200)**:
```json
{
    "id": 123,
    "username": "myuser",
    "created_at": "2025-09-12T20:00:00Z"
}
```

### **Update User Profile**

**Endpoint**: `PUT /api/user/profile`

**Request**:
```javascript
const updateUserProfile = async (updates) => {
    const token = getToken();
    if (!token) return { success: false, error: 'Not authenticated' };
    
    const response = await fetch(`${API_CONFIG.API_BASE}/user/profile`, {
        method: 'PUT',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(updates)
    });
    
    const data = await response.json();
    
    if (response.ok) {
        return {
            success: true,
            user: {
                id: data.id,
                username: data.username,
                createdAt: data.created_at
            }
        };
    } else {
        if (response.status === 401) {
            clearToken(); // Token invalid
        }
        return { success: false, error: data.message };
    }
};

// Usage examples:
// updateUserProfile({ username: "new_username" })
// updateUserProfile({ password: "new_password123" })
// updateUserProfile({ username: "new_user", password: "new_pass123" })
```

## 🛡️ **Protected Routes Access**

### **Generic Protected Request Function**

```javascript
const makeProtectedRequest = async (endpoint, options = {}) => {
    const token = getToken();
    
    // Check if token exists and is not expired
    if (!token || isTokenExpired()) {
        // Try to refresh token
        const refreshResult = await refreshToken();
        if (!refreshResult.success) {
            return { success: false, error: 'Authentication required', needsLogin: true };
        }
    }
    
    const response = await fetch(`${API_CONFIG.API_BASE}${endpoint}`, {
        ...options,
        headers: {
            'Authorization': `Bearer ${getToken()}`,
            'Content-Type': 'application/json',
            ...options.headers
        }
    });
    
    const data = await response.json();
    
    if (response.ok) {
        return { success: true, data: data };
    } else {
        if (response.status === 401) {
            clearToken();
            return { success: false, error: data.message, needsLogin: true };
        }
        return { success: false, error: data.message, statusCode: data.status_code };
    }
};
```

### **Example Protected Endpoint Usage**

```javascript
// Access protected endpoint
const accessProtectedEndpoint = async () => {
    return await makeProtectedRequest('/user/protected');
};

// Get users list (admin only)
const getUsersList = async (skip = 0, limit = 10) => {
    return await makeProtectedRequest(`/users?skip=${skip}&limit=${limit}`);
};
```

## 🔄 **Complete Authentication Service Class**

```javascript
class JDAuthService {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
        this.apiBase = `${baseUrl}/api`;
    }
    
    // Registration
    async register(username, password) {
        try {
            const response = await fetch(`${this.apiBase}/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            
            const data = await response.json();
            return { success: response.ok, data, status: response.status };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
    
    // Login
    async login(username, password) {
        try {
            const response = await fetch(`${this.apiBase}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.storeToken(data);
            }
            
            return { success: response.ok, data, status: response.status };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
    
    // Token management
    storeToken(tokenData) {
        localStorage.setItem('auth_token', tokenData.access_token);
        localStorage.setItem('token_expires', Date.now() + (tokenData.expires_in * 1000));
    }
    
    getToken() {
        return localStorage.getItem('auth_token');
    }
    
    isAuthenticated() {
        const token = this.getToken();
        const expires = localStorage.getItem('token_expires');
        return token && expires && Date.now() < parseInt(expires);
    }
    
    logout() {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('token_expires');
    }
    
    // Protected requests
    async makeAuthenticatedRequest(endpoint, options = {}) {
        const token = this.getToken();
        
        if (!token || !this.isAuthenticated()) {
            return { success: false, error: 'Authentication required', needsLogin: true };
        }
        
        try {
            const response = await fetch(`${this.apiBase}${endpoint}`, {
                ...options,
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });
            
            const data = await response.json();
            
            if (response.status === 401) {
                this.logout();
                return { success: false, error: data.message, needsLogin: true };
            }
            
            return { success: response.ok, data, status: response.status };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
    
    // Profile operations
    async getProfile() {
        return await this.makeAuthenticatedRequest('/user/profile');
    }
    
    async updateProfile(updates) {
        return await this.makeAuthenticatedRequest('/user/profile', {
            method: 'PUT',
            body: JSON.stringify(updates)
        });
    }
    
    // Refresh token
    async refreshToken() {
        return await this.makeAuthenticatedRequest('/auth/refresh', {
            method: 'POST'
        });
    }
}
```

## 🎨 **Frontend Implementation Examples**

### **React Hooks Example**

```javascript
// useAuth.js
import { useState, useEffect, createContext, useContext } from 'react';

const AuthContext = createContext();

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within AuthProvider');
    }
    return context;
};

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(null);
    const [loading, setLoading] = useState(true);
    const authService = new JDAuthService();
    
    useEffect(() => {
        // Check for existing token on app start
        const savedToken = authService.getToken();
        if (savedToken && authService.isAuthenticated()) {
            setToken(savedToken);
            loadUserProfile();
        } else {
            setLoading(false);
        }
    }, []);
    
    const loadUserProfile = async () => {
        const result = await authService.getProfile();
        if (result.success) {
            setUser(result.data);
        } else if (result.needsLogin) {
            logout();
        }
        setLoading(false);
    };
    
    const login = async (username, password) => {
        setLoading(true);
        const result = await authService.login(username, password);
        
        if (result.success) {
            setToken(result.data.access_token);
            await loadUserProfile();
            return { success: true };
        } else {
            setLoading(false);
            return { success: false, error: result.data.message };
        }
    };
    
    const register = async (username, password) => {
        setLoading(true);
        const result = await authService.register(username, password);
        setLoading(false);
        
        if (result.success) {
            return { success: true, message: result.data.message };
        } else {
            return { success: false, error: result.data.message };
        }
    };
    
    const logout = () => {
        authService.logout();
        setToken(null);
        setUser(null);
    };
    
    const updateProfile = async (updates) => {
        const result = await authService.updateProfile(updates);
        
        if (result.success) {
            setUser(result.data);
            return { success: true };
        } else {
            if (result.needsLogin) {
                logout();
            }
            return { success: false, error: result.data.message };
        }
    };
    
    return (
        <AuthContext.Provider value={{
            user,
            token,
            loading,
            login,
            register,
            logout,
            updateProfile,
            isAuthenticated: !!token && !!user
        }}>
            {children}
        </AuthContext.Provider>
    );
};
```

### **Vue.js Composable Example**

```javascript
// useAuth.js
import { ref, computed, onMounted } from 'vue';

const user = ref(null);
const token = ref(null);
const loading = ref(false);
const authService = new JDAuthService();

export const useAuth = () => {
    const isAuthenticated = computed(() => {
        return !!token.value && !!user.value && authService.isAuthenticated();
    });
    
    const login = async (username, password) => {
        loading.value = true;
        const result = await authService.login(username, password);
        
        if (result.success) {
            token.value = result.data.access_token;
            await loadUserProfile();
            return { success: true };
        } else {
            loading.value = false;
            return { success: false, error: result.data.message };
        }
    };
    
    const register = async (username, password) => {
        loading.value = true;
        const result = await authService.register(username, password);
        loading.value = false;
        
        return result.success 
            ? { success: true, message: result.data.message }
            : { success: false, error: result.data.message };
    };
    
    const logout = () => {
        authService.logout();
        token.value = null;
        user.value = null;
    };
    
    const loadUserProfile = async () => {
        const result = await authService.getProfile();
        if (result.success) {
            user.value = result.data;
        } else if (result.needsLogin) {
            logout();
        }
        loading.value = false;
    };
    
    const updateProfile = async (updates) => {
        const result = await authService.updateProfile(updates);
        
        if (result.success) {
            user.value = result.data;
            return { success: true };
        } else {
            if (result.needsLogin) logout();
            return { success: false, error: result.data.message };
        }
    };
    
    // Initialize on mount
    onMounted(() => {
        const savedToken = authService.getToken();
        if (savedToken && authService.isAuthenticated()) {
            token.value = savedToken;
            loadUserProfile();
        }
    });
    
    return {
        user: readonly(user),
        token: readonly(token),
        loading: readonly(loading),
        isAuthenticated,
        login,
        register,
        logout,
        updateProfile
    };
};
```

## 🛠️ **HTTP Client Configuration**

### **Axios Configuration**

```javascript
import axios from 'axios';

// Create axios instance
const apiClient = axios.create({
    baseURL: 'http://localhost:8000/api',
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json'
    }
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('auth_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Response interceptor to handle auth errors
apiClient.interceptors.response.use(
    (response) => response,
    async (error) => {
        if (error.response?.status === 401) {
            // Clear invalid token
            localStorage.removeItem('auth_token');
            localStorage.removeItem('token_expires');
            
            // Redirect to login or emit auth error event
            window.dispatchEvent(new CustomEvent('auth:logout'));
        }
        return Promise.reject(error);
    }
);

// API methods
export const authAPI = {
    register: (username, password) => 
        apiClient.post('/auth/register', { username, password }),
    
    login: (username, password) => 
        apiClient.post('/auth/login', { username, password }),
    
    refresh: () => 
        apiClient.post('/auth/refresh'),
    
    getProfile: () => 
        apiClient.get('/user/profile'),
    
    updateProfile: (updates) => 
        apiClient.put('/user/profile', updates),
    
    getUsers: (skip = 0, limit = 10) => 
        apiClient.get(`/users?skip=${skip}&limit=${limit}`)
};
```

### **Fetch API with Error Handling**

```javascript
class APIClient {
    constructor(baseUrl = 'http://localhost:8000/api') {
        this.baseUrl = baseUrl;
    }
    
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const token = localStorage.getItem('auth_token');
        
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...(token && { 'Authorization': `Bearer ${token}` }),
                ...options.headers
            },
            ...options
        };
        
        try {
            const response = await fetch(url, config);
            const data = await response.json();
            
            // Handle authentication errors
            if (response.status === 401) {
                localStorage.removeItem('auth_token');
                localStorage.removeItem('token_expires');
                window.dispatchEvent(new CustomEvent('auth:logout'));
                throw new Error('Authentication required');
            }
            
            if (!response.ok) {
                throw new Error(data.message || `HTTP ${response.status}`);
            }
            
            return data;
        } catch (error) {
            console.error(`API request failed: ${endpoint}`, error);
            throw error;
        }
    }
    
    // Convenience methods
    get(endpoint) {
        return this.request(endpoint);
    }
    
    post(endpoint, body) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(body)
        });
    }
    
    put(endpoint, body) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(body)
        });
    }
    
    delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }
}

const api = new APIClient();
```

## 🚨 **Error Handling Patterns**

### **Standard Error Response Format**

All API errors follow this format:
```json
{
    "error": true,
    "message": "Human-readable error message",
    "status_code": 400,
    "timestamp": "2025-09-12T21:00:00Z"
}
```

### **Error Handling Function**

```javascript
const handleAPIError = (error, statusCode) => {
    const errorMessages = {
        400: 'Invalid request data',
        401: 'Authentication required',
        403: 'Access forbidden',
        404: 'Resource not found',
        422: 'Validation error',
        429: 'Too many requests',
        500: 'Server error'
    };
    
    // Use custom message if available, otherwise use default
    const message = error.message || errorMessages[statusCode] || 'Unknown error';
    
    return {
        type: getErrorType(statusCode),
        message: message,
        statusCode: statusCode,
        needsLogin: statusCode === 401
    };
};

const getErrorType = (statusCode) => {
    if (statusCode >= 400 && statusCode < 500) return 'client';
    if (statusCode >= 500) return 'server';
    return 'unknown';
};
```

## 🔒 **Security Best Practices for Frontend**

### **Token Security**

```javascript
// Secure token storage (consider using httpOnly cookies in production)
const secureTokenStorage = {
    store: (tokenData) => {
        // For development: localStorage
        localStorage.setItem('auth_token', tokenData.access_token);
        localStorage.setItem('token_expires', Date.now() + (tokenData.expires_in * 1000));
        
        // For production: consider httpOnly cookies or secure storage
    },
    
    get: () => {
        return localStorage.getItem('auth_token');
    },
    
    clear: () => {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('token_expires');
    },
    
    isValid: () => {
        const token = localStorage.getItem('auth_token');
        const expires = localStorage.getItem('token_expires');
        return token && expires && Date.now() < parseInt(expires);
    }
};
```

### **Input Validation**

```javascript
const validateInput = {
    username: (username) => {
        if (!username || username.length < 3) {
            return { valid: false, error: 'Username must be at least 3 characters' };
        }
        if (username.length > 50) {
            return { valid: false, error: 'Username must be less than 50 characters' };
        }
        if (!/^[a-zA-Z0-9_]+$/.test(username)) {
            return { valid: false, error: 'Username can only contain letters, numbers, and underscores' };
        }
        return { valid: true };
    },
    
    password: (password) => {
        if (!password || password.length < 8) {
            return { valid: false, error: 'Password must be at least 8 characters' };
        }
        return { valid: true };
    }
};
```

## 📱 **UI State Management**

### **Authentication States**

```javascript
const AUTH_STATES = {
    LOADING: 'loading',
    AUTHENTICATED: 'authenticated',
    UNAUTHENTICATED: 'unauthenticated',
    ERROR: 'error'
};

const useAuthState = () => {
    const [authState, setAuthState] = useState(AUTH_STATES.LOADING);
    const [user, setUser] = useState(null);
    const [error, setError] = useState(null);
    
    const login = async (username, password) => {
        setAuthState(AUTH_STATES.LOADING);
        setError(null);
        
        try {
            const authService = new JDAuthService();
            const result = await authService.login(username, password);
            
            if (result.success) {
                const profileResult = await authService.getProfile();
                if (profileResult.success) {
                    setUser(profileResult.data);
                    setAuthState(AUTH_STATES.AUTHENTICATED);
                    return { success: true };
                }
            }
            
            setError(result.data.message);
            setAuthState(AUTH_STATES.ERROR);
            return { success: false, error: result.data.message };
            
        } catch (err) {
            setError(err.message);
            setAuthState(AUTH_STATES.ERROR);
            return { success: false, error: err.message };
        }
    };
    
    const logout = () => {
        const authService = new JDAuthService();
        authService.logout();
        setUser(null);
        setError(null);
        setAuthState(AUTH_STATES.UNAUTHENTICATED);
    };
    
    return {
        authState,
        user,
        error,
        login,
        logout,
        isAuthenticated: authState === AUTH_STATES.AUTHENTICATED,
        isLoading: authState === AUTH_STATES.LOADING
    };
};
```

## 🧪 **Testing Your Frontend Integration**

### **Manual Testing Checklist**

1. **Registration Flow**:
   ```javascript
   // Test successful registration
   await authService.register('testuser', 'testpass123');
   
   // Test duplicate username
   await authService.register('testuser', 'testpass123'); // Should fail
   
   // Test invalid data
   await authService.register('ab', '123'); // Should fail
   ```

2. **Login Flow**:
   ```javascript
   // Test successful login
   await authService.login('testuser', 'testpass123');
   
   // Test invalid credentials
   await authService.login('testuser', 'wrongpass'); // Should fail
   
   // Test nonexistent user
   await authService.login('nonexistent', 'anypass'); // Should fail
   ```

3. **Protected Routes**:
   ```javascript
   // Test with valid token
   await authService.getProfile(); // Should work
   
   // Test without token
   authService.logout();
   await authService.getProfile(); // Should fail with 401
   ```

4. **Token Refresh**:
   ```javascript
   // Test token refresh
   await authService.refreshToken(); // Should get new token
   ```

### **Error Scenarios to Handle**

```javascript
const errorScenarios = {
    // Network errors
    networkError: () => {
        // Handle fetch failures, timeouts
        return { type: 'network', message: 'Connection failed' };
    },
    
    // Validation errors (400, 422)
    validationError: (response) => {
        return { type: 'validation', message: response.message };
    },
    
    // Authentication errors (401)
    authError: () => {
        // Clear tokens, redirect to login
        authService.logout();
        return { type: 'auth', message: 'Please log in again' };
    },
    
    // Authorization errors (403)
    forbiddenError: () => {
        return { type: 'forbidden', message: 'Access denied' };
    },
    
    // Server errors (500)
    serverError: () => {
        return { type: 'server', message: 'Server error, please try again' };
    }
};
```

## 📋 **Complete API Reference for Frontend**

### **Authentication Endpoints**

| Method | Endpoint | Auth Required | Purpose |
|--------|----------|---------------|---------|
| POST | `/api/auth/register` | No | Register new user |
| POST | `/api/auth/login` | No | Login user |
| POST | `/api/auth/refresh` | Yes | Refresh JWT token |

### **User Endpoints**

| Method | Endpoint | Auth Required | Purpose |
|--------|----------|---------------|---------|
| GET | `/api/user/profile` | Yes | Get user profile |
| PUT | `/api/user/profile` | Yes | Update user profile |
| GET | `/api/user/protected` | Yes | Example protected endpoint |

### **Admin Endpoints**

| Method | Endpoint | Auth Required | Purpose |
|--------|----------|---------------|---------|
| GET | `/api/users` | Yes (Admin) | List all users |

### **System Endpoints**

| Method | Endpoint | Auth Required | Purpose |
|--------|----------|---------------|---------|
| GET | `/health` | No | Application health check |
| GET | `/` | No | Application information |

## 🎯 **Frontend Integration Checklist**

### **Required Features**
- [ ] User registration form
- [ ] Login form  
- [ ] Token storage and management
- [ ] Protected route wrapper
- [ ] Automatic token refresh
- [ ] Logout functionality
- [ ] Error handling and display
- [ ] Loading states

### **Optional Features**
- [ ] Profile management page
- [ ] Admin user management
- [ ] Remember me functionality
- [ ] Password strength indicator
- [ ] Form validation
- [ ] Toast notifications for errors

### **Security Considerations**
- [ ] Input validation on frontend
- [ ] Secure token storage
- [ ] HTTPS in production
- [ ] XSS prevention
- [ ] CSRF protection (if using cookies)

## 🚀 **Quick Start Template**

```html
<!DOCTYPE html>
<html>
<head>
    <title>JDauth Frontend</title>
</head>
<body>
    <div id="app">
        <!-- Login Form -->
        <form id="loginForm" style="display: block;">
            <h2>Login</h2>
            <input type="text" id="username" placeholder="Username" required>
            <input type="password" id="password" placeholder="Password" required>
            <button type="submit">Login</button>
            <button type="button" onclick="showRegister()">Register</button>
        </form>
        
        <!-- Register Form -->
        <form id="registerForm" style="display: none;">
            <h2>Register</h2>
            <input type="text" id="regUsername" placeholder="Username" required>
            <input type="password" id="regPassword" placeholder="Password" required>
            <button type="submit">Register</button>
            <button type="button" onclick="showLogin()">Back to Login</button>
        </form>
        
        <!-- User Dashboard -->
        <div id="dashboard" style="display: none;">
            <h2>Welcome, <span id="userDisplay"></span>!</h2>
            <button onclick="getProfile()">Get Profile</button>
            <button onclick="logout()">Logout</button>
            <div id="profileData"></div>
        </div>
        
        <div id="message"></div>
    </div>

    <script>
        const authService = new JDAuthService();
        
        // Initialize
        if (authService.isAuthenticated()) {
            showDashboard();
            loadProfile();
        }
        
        // Event handlers
        document.getElementById('loginForm').onsubmit = async (e) => {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            const result = await authService.login(username, password);
            if (result.success) {
                showDashboard();
                loadProfile();
            } else {
                showMessage(result.data.message, 'error');
            }
        };
        
        document.getElementById('registerForm').onsubmit = async (e) => {
            e.preventDefault();
            const username = document.getElementById('regUsername').value;
            const password = document.getElementById('regPassword').value;
            
            const result = await authService.register(username, password);
            if (result.success) {
                showMessage('Registration successful! Please login.', 'success');
                showLogin();
            } else {
                showMessage(result.data.message, 'error');
            }
        };
        
        // UI functions
        function showLogin() {
            document.getElementById('loginForm').style.display = 'block';
            document.getElementById('registerForm').style.display = 'none';
            document.getElementById('dashboard').style.display = 'none';
        }
        
        function showRegister() {
            document.getElementById('loginForm').style.display = 'none';
            document.getElementById('registerForm').style.display = 'block';
            document.getElementById('dashboard').style.display = 'none';
        }
        
        function showDashboard() {
            document.getElementById('loginForm').style.display = 'none';
            document.getElementById('registerForm').style.display = 'none';
            document.getElementById('dashboard').style.display = 'block';
        }
        
        async function loadProfile() {
            const result = await authService.getProfile();
            if (result.success) {
                document.getElementById('userDisplay').textContent = result.data.username;
            }
        }
        
        async function getProfile() {
            const result = await authService.getProfile();
            if (result.success) {
                document.getElementById('profileData').innerHTML = 
                    `<pre>${JSON.stringify(result.data, null, 2)}</pre>`;
            } else {
                showMessage(result.error, 'error');
            }
        }
        
        function logout() {
            authService.logout();
            showLogin();
            showMessage('Logged out successfully', 'info');
        }
        
        function showMessage(message, type) {
            const messageDiv = document.getElementById('message');
            messageDiv.textContent = message;
            messageDiv.className = type;
            setTimeout(() => messageDiv.textContent = '', 3000);
        }
    </script>
</body>
</html>
```

This guide provides everything an LLM needs to build a frontend that integrates perfectly with your JDauth FastAPI service! 🚀
