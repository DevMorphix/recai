import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { api, User } from '@/services/api';
import { Preferences } from '@capacitor/preferences';

const TOKEN_KEY = 'auth_token';

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null);
  const token = ref<string | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);

  const isAuthenticated = computed(() => !!token.value && !!user.value);

  async function initialize() {
    try {
      const stored = await Preferences.get({ key: TOKEN_KEY });
      if (stored.value) {
        token.value = stored.value;
        api.setToken(stored.value);
        await fetchUser();
      }
    } catch (err) {
      console.error('Failed to initialize auth:', err);
      await logout();
    }
  }

  async function register(name: string, email: string, password: string) {
    loading.value = true;
    error.value = null;
    try {
      const response = await api.register(name, email, password);
      token.value = response.token;
      user.value = response.user;
      api.setToken(response.token);
      await Preferences.set({ key: TOKEN_KEY, value: response.token });
      return true;
    } catch (err: any) {
      error.value = err.message || 'Registration failed';
      return false;
    } finally {
      loading.value = false;
    }
  }

  async function login(email: string, password: string) {
    loading.value = true;
    error.value = null;
    try {
      const response = await api.login(email, password);
      token.value = response.token;
      user.value = response.user;
      api.setToken(response.token);
      await Preferences.set({ key: TOKEN_KEY, value: response.token });
      return true;
    } catch (err: any) {
      error.value = err.message || 'Login failed';
      return false;
    } finally {
      loading.value = false;
    }
  }

  async function fetchUser() {
    if (!token.value) return;
    try {
      user.value = await api.getMe();
    } catch (err) {
      await logout();
    }
  }

  async function logout() {
    token.value = null;
    user.value = null;
    api.setToken(null);
    await Preferences.remove({ key: TOKEN_KEY });
  }

  async function updateProfile(updates: Partial<User>) {
    loading.value = true;
    error.value = null;
    try {
      user.value = await api.updateProfile(updates);
      return true;
    } catch (err: any) {
      error.value = err.message || 'Update failed';
      return false;
    } finally {
      loading.value = false;
    }
  }

  return {
    user,
    token,
    loading,
    error,
    isAuthenticated,
    initialize,
    register,
    login,
    logout,
    fetchUser,
    updateProfile,
  };
});