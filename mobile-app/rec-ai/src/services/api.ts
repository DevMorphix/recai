import axios, { AxiosInstance } from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3001/api';

// Types
export interface User {
  _id: string;
  name: string;
  email: string;
  createdAt: string;
}

export interface Recording {
  _id: string;
  user: string;
  title: string;
  audioUrl?: string;
  duration: number;
  status: 'pending' | 'transcribing' | 'transcribed' | 'summarized' | 'completed' | 'failed';
  transcript?: string;
  summary?: string;
  minutes?: string;
  actionItems?: { task: string; assignee: string; priority: string; deadline: string | null }[];
  createdAt: string;
  updatedAt: string;
}

export interface AuthResponse {
  token: string;
  user: User;
}

export interface ApiError {
  message: string;
  errors?: Record<string, string>;
}

class ApiService {
  private api: AxiosInstance;
  private token: string | null = null;

  constructor() {
    this.api = axios.create({
      baseURL: API_URL,
      headers: { 'Content-Type': 'application/json' },
      timeout: 60000,
    });

    // Request interceptor - add token
    this.api.interceptors.request.use((config) => {
      if (this.token) {
        config.headers.Authorization = `Bearer ${this.token}`;
      }
      return config;
    });

    // Response interceptor - handle errors
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        const message = error.response?.data?.error || error.response?.data?.message || error.message || 'An error occurred';
        const err = new Error(message) as any;
        err.responseData = error.response?.data;
        return Promise.reject(err);
      }
    );
  }

  setToken(token: string | null) {
    this.token = token;
  }

  // Auth
  async register(name: string, email: string, password: string): Promise<{ message: string; email: string }> {
    const { data } = await this.api.post<{ message: string; email: string }>('/auth/register', { name, email, password });
    return data;
  }

  async sendVerification(email: string): Promise<void> {
    await this.api.post('/auth/send-verification', { email });
  }

  async verifyEmail(email: string, otp: string): Promise<AuthResponse> {
    const { data } = await this.api.post<AuthResponse>('/auth/verify-email', { email, otp });
    return data;
  }

  async forgotPassword(email: string): Promise<void> {
    await this.api.post('/auth/forgot-password', { email });
  }

  async resetPassword(email: string, otp: string, newPassword: string): Promise<void> {
    await this.api.post('/auth/reset-password', { email, otp, newPassword });
  }

  async login(email: string, password: string): Promise<AuthResponse> {
    const { data } = await this.api.post<AuthResponse>('/auth/login', { email, password });
    return data;
  }

  async googleLogin(idToken: string): Promise<AuthResponse> {
    const { data } = await this.api.post<AuthResponse>('/auth/google', { idToken });
    return data;
  }

  async getMe(): Promise<User> {
    const { data } = await this.api.get<{ user: User }>('/auth/me');
    return data.user;
  }

  async updateProfile(updates: Partial<User>): Promise<User> {
    const { data } = await this.api.patch<{ user: User }>('/auth/profile', updates);
    return data.user;
  }

  // Recordings
  async getRecordings(): Promise<Recording[]> {
    const { data } = await this.api.get<{ recordings: Recording[] }>('/recordings');
    return data.recordings;
  }

  async getRecording(id: string): Promise<Recording> {
    const { data } = await this.api.get<{ recording: Recording }>(`/recordings/${id}`);
    return data.recording;
  }

  async getUploadUrl(mimeType: string): Promise<{ uploadUrl: string; key: string }> {
    const { data } = await this.api.post<{ uploadUrl: string; key: string }>('/recordings/upload-url', { mimeType });
    return data;
  }

  async uploadToR2(uploadUrl: string, blob: Blob, mimeType: string): Promise<void> {
    await fetch(uploadUrl, {
      method: 'PUT',
      body: blob,
      headers: { 'Content-Type': mimeType },
    });
  }

  async createRecording(recordingData: {
    audioData?: string;
    audioKey?: string;
    duration: number;
    mimeType: string;
    title?: string;
    autoTranscribe?: boolean;
  }): Promise<Recording> {
    const { data } = await this.api.post<{ recording: Recording }>('/recordings', recordingData, {
      timeout: 300000, // 5 minutes — backend may transcribe synchronously
    });
    return data.recording;
  }

  async updateRecording(id: string, updates: Partial<Recording>): Promise<Recording> {
    const { data } = await this.api.patch<{ recording: Recording }>(`/recordings/${id}`, updates);
    return data.recording;
  }

  async deleteRecording(id: string): Promise<void> {
    await this.api.delete(`/recordings/${id}`);
  }

  async transcribeRecording(id: string): Promise<Recording> {
    const { data } = await this.api.post<{ recording: Recording }>(`/recordings/${id}/transcribe`, null, {
      timeout: 300000, // 5 minutes — server-side timeout matches
    });
    return data.recording;
  }

  async summarizeRecording(id: string): Promise<Recording> {
    const { data } = await this.api.post<{ recording: Recording }>(`/recordings/${id}/summarize`);
    return data.recording;
  }

  async generateMinutes(id: string): Promise<Recording> {
    const { data } = await this.api.post<{ recording: Recording }>(`/recordings/${id}/minutes`);
    return data.recording;
  }

  async generateActionItems(id: string): Promise<Recording> {
    const { data } = await this.api.post<{ recording: Recording }>(`/recordings/${id}/actions`);
    return data.recording;
  }

  async generateTitle(id: string): Promise<Recording> {
    const { data } = await this.api.post<{ recording: Recording }>(`/recordings/${id}/generate-title`);
    return data.recording;
  }
}

export const api = new ApiService();