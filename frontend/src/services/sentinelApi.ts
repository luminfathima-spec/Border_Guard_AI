import { apiClient } from './api';
import type {
  User, Camera, Video, SecurityEvent, Alert, Incident,
  Evidence, AnalyticsOverview, DemoVideoInfo
} from '../types';

export const authApi = {
  login: async (email: string, password: string) => {
    const res = await apiClient.post('/auth/login', { email, password });
    return res.data;
  },
  getMe: async (): Promise<User> => {
    const res = await apiClient.get('/auth/me');
    return res.data;
  },
};

export const cameraApi = {
  list: async (params?: { status?: string; zone?: string }): Promise<Camera[]> => {
    const res = await apiClient.get('/cameras', { params });
    return res.data;
  },
  get: async (id: number): Promise<Camera> => {
    const res = await apiClient.get(`/cameras/${id}`);
    return res.data;
  },
  create: async (data: Partial<Camera>): Promise<Camera> => {
    const res = await apiClient.post('/cameras', data);
    return res.data;
  },
  update: async (id: number, data: Partial<Camera>): Promise<Camera> => {
    const res = await apiClient.patch(`/cameras/${id}`, data);
    return res.data;
  },
};

export const videoApi = {
  list: async (params?: { camera_id?: number; status?: string }): Promise<Video[]> => {
    const res = await apiClient.get('/videos', { params });
    return res.data;
  },
  get: async (id: number): Promise<Video> => {
    const res = await apiClient.get(`/videos/${id}`);
    return res.data;
  },
  getDemos: async (): Promise<DemoVideoInfo[]> => {
    const res = await apiClient.get('/videos/demos');
    return res.data;
  },
  ingestDemo: async (demoId: string, cameraId?: number): Promise<{ message: string; video: Video; analytics: any }> => {
    const formData = new FormData();
    formData.append('demo_id', demoId);
    if (cameraId) formData.append('camera_id', cameraId.toString());
    const res = await apiClient.post('/videos/demo/ingest', formData);
    return res.data;
  },
  upload: async (file: File, cameraId?: number): Promise<{ message: string; video: Video }> => {
    const formData = new FormData();
    formData.append('file', file);
    if (cameraId) formData.append('camera_id', cameraId.toString());
    formData.append('auto_process', 'true');
    const res = await apiClient.post('/videos/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },
  process: async (id: number, options?: { confidence_threshold?: number; process_every_n_frames?: number }): Promise<any> => {
    const res = await apiClient.post(`/videos/${id}/process`, options || {});
    return res.data;
  },
};

export const eventApi = {
  list: async (params?: { camera_id?: number; event_type?: string; severity?: string; incident_id?: number; limit?: number }): Promise<SecurityEvent[]> => {
    const res = await apiClient.get('/events', { params });
    return res.data;
  },
  get: async (id: number): Promise<SecurityEvent> => {
    const res = await apiClient.get(`/events/${id}`);
    return res.data;
  },
};

export const alertApi = {
  list: async (params?: { status?: string; severity?: string; camera_id?: number; limit?: number }): Promise<Alert[]> => {
    const res = await apiClient.get('/alerts', { params });
    return res.data;
  },
  updateStatus: async (id: number, status: string): Promise<Alert> => {
    const res = await apiClient.patch(`/alerts/${id}`, { status });
    return res.data;
  },
};

export const incidentApi = {
  list: async (params?: { status?: string; severity?: string }): Promise<Incident[]> => {
    const res = await apiClient.get('/incidents', { params });
    return res.data;
  },
  get: async (id: number): Promise<Incident> => {
    const res = await apiClient.get(`/incidents/${id}`);
    return res.data;
  },
  update: async (id: number, data: Partial<Incident>): Promise<Incident> => {
    const res = await apiClient.patch(`/incidents/${id}`, data);
    return res.data;
  },
};

export const evidenceApi = {
  list: async (params?: { incident_id?: number; event_id?: number; evidence_type?: string }): Promise<Evidence[]> => {
    const res = await apiClient.get('/evidence', { params });
    return res.data;
  },
};

export const analyticsApi = {
  getOverview: async (): Promise<AnalyticsOverview> => {
    const res = await apiClient.get('/analytics/overview');
    return res.data;
  },
};

export const aiApi = {
  summarizeIncident: async (incidentId: number, customInstructions?: string) => {
    const res = await apiClient.post(`/ai/incidents/${incidentId}/summarize`, {
      custom_instructions: customInstructions,
    });
    return res.data;
  },
  chat: async (message: string, conversationHistory: Array<{ role: string; content: string }>) => {
    const res = await apiClient.post('/ai/assistant/chat', {
      message,
      conversation_history: conversationHistory,
    });
    return res.data;
  },
  generateReport: async (incidentId: number) => {
    const res = await apiClient.post(`/ai/incidents/${incidentId}/report`);
    return res.data;
  },
};
