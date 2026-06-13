import React, { createContext, useReducer, useEffect, useCallback, ReactNode } from 'react';
import * as SecureStore from 'expo-secure-store';
import { AuthState, UserProfile } from '../types';
import { apiClient } from '../api/client';

const TOKEN_KEY = 'auth_token';
const USER_KEY = 'auth_user';

type AuthAction =
  | { type: 'RESTORE_TOKEN'; token: string; user: UserProfile }
  | { type: 'LOGIN'; token: string; user: UserProfile }
  | { type: 'LOGOUT' }
  | { type: 'SET_LOADING'; isLoading: boolean };

interface AuthContextValue {
  state: AuthState;
  login: (token: string, user: UserProfile) => Promise<void>;
  logout: () => Promise<void>;
  loginWithToken: (token: string) => Promise<void>;
}

const initialState: AuthState = {
  token: null,
  user: null,
  isLoading: true,
  isAuthenticated: false,
};

function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'RESTORE_TOKEN':
      return {
        ...state,
        token: action.token,
        user: action.user,
        isLoading: false,
        isAuthenticated: true,
      };
    case 'LOGIN':
      return {
        ...state,
        token: action.token,
        user: action.user,
        isLoading: false,
        isAuthenticated: true,
      };
    case 'LOGOUT':
      return {
        ...state,
        token: null,
        user: null,
        isLoading: false,
        isAuthenticated: false,
      };
    case 'SET_LOADING':
      return { ...state, isLoading: action.isLoading };
    default:
      return state;
  }
}

export const AuthContext = createContext<AuthContextValue>({
  state: initialState,
  login: async () => {},
  logout: async () => {},
  loginWithToken: async () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(authReducer, initialState);

  useEffect(() => {
    async function restoreToken() {
      try {
        const token = await SecureStore.getItemAsync(TOKEN_KEY);
        const userJson = await SecureStore.getItemAsync(USER_KEY);
        if (token && userJson) {
          const user = JSON.parse(userJson) as UserProfile;
          apiClient.setToken(token);
          dispatch({ type: 'RESTORE_TOKEN', token, user });
          return;
        }
      } catch {
        await SecureStore.deleteItemAsync(TOKEN_KEY);
        await SecureStore.deleteItemAsync(USER_KEY);
      }
      dispatch({ type: 'SET_LOADING', isLoading: false });
    }
    restoreToken();
  }, []);

  const login = useCallback(async (token: string, user: UserProfile) => {
    await SecureStore.setItemAsync(TOKEN_KEY, token);
    await SecureStore.setItemAsync(USER_KEY, JSON.stringify(user));
    apiClient.setToken(token);
    dispatch({ type: 'LOGIN', token, user });
  }, []);

  const loginWithToken = useCallback(async (token: string) => {
    await SecureStore.setItemAsync(TOKEN_KEY, token);
    apiClient.setToken(token);
    try {
      const user = await apiClient.getUser();
      await SecureStore.setItemAsync(USER_KEY, JSON.stringify(user));
      dispatch({ type: 'LOGIN', token, user });
    } catch {
      await SecureStore.deleteItemAsync(TOKEN_KEY);
      apiClient.clearToken();
      dispatch({ type: 'SET_LOADING', isLoading: false });
    }
  }, []);

  const logout = useCallback(async () => {
    await SecureStore.deleteItemAsync(TOKEN_KEY);
    await SecureStore.deleteItemAsync(USER_KEY);
    apiClient.clearToken();
    dispatch({ type: 'LOGOUT' });
  }, []);

  return (
    <AuthContext.Provider value={{ state, login, logout, loginWithToken }}>
      {children}
    </AuthContext.Provider>
  );
}
