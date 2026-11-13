import { apiClient } from './api';
import type {
  User, Camera, Video, SecurityEvent, Alert, Incident,
  Evidence, AnalyticsOverview, DemoVideoInfo,
  VideoIngestionStatus, RTSPTestResponse,
  EventGraphResponse, EvidenceChainResponse, EventLink,
  ReportResponse, AuditHistoryEntry,
  EdgeStatusResponse, NetworkState, SyncResponse,
  PurgeResponse, BufferedEventItem, EdgeBenchmarkResponse,
  CopilotChatRequest, CopilotChatResponse,
  AuditLogEntry, SystemSettings, UpdateSettingsRequest
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
  testStream: async (stream_url: string, timeout_seconds: number = 5): Promise<RTSPTestResponse> => {
    const res = await apiClient.post('/cameras/test-stream', { stream_url, timeout_seconds });
    return res.data;
  },
  testConnection: async (camera_id: number): Promise<RTSPTestResponse> => {
    const res = await apiClient.post(`/cameras/${camera_id}/test-connection`);
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
  getStatus: async (id: number): Promise<VideoIngestionStatus> => {
    const res = await apiClient.get(`/videos/${id}/status`);
    return res.data;
  },
  getStreamUrl: (id: number): string => {
    const token = localStorage.getItem('sentinel_token');
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
    return `${baseUrl}/videos/${id}/stream${token ? `?token=${encodeURIComponent(token)}` : ''}`;
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
  analyzeIncident: async (incidentId: number, customInstructions?: string, forceMock?: boolean) => {
    const res = await apiClient.post(`/ai/incidents/${incidentId}/analyze`, {
      custom_instructions: customInstructions,
      force_mock: forceMock,
    });
    return res.data;
  },
  getAnalyses: async (incidentId: number) => {
    const res = await apiClient.get(`/ai/incidents/${incidentId}/analyses`);
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

export const eventGraphApi = {
  getGraph: async (incidentId: number): Promise<EventGraphResponse> => {
    const res = await apiClient.get(`/incidents/${incidentId}/graph`);
    return res.data;
  },
  getEvidenceChain: async (incidentId: number): Promise<EvidenceChainResponse> => {
    const res = await apiClient.get(`/incidents/${incidentId}/evidence-chain`);
    return res.data;
  },
  createLink: async (incidentId: number, linkData: any): Promise<EventLink> => {
    const res = await apiClient.post(`/incidents/${incidentId}/graph/links`, linkData);
    return res.data;
  },
  recordObservation: async (incidentId: number, obsData: any) => {
    const res = await apiClient.post(`/incidents/${incidentId}/observations`, obsData);
    return res.data;
  },
  supersedeObservation: async (incidentId: number, obsId: number, newObsData: any, reason: string) => {
    const res = await apiClient.post(`/incidents/${incidentId}/observations/${obsId}/supersede`, newObsData, {
      params: { reason },
    });
    return res.data;
  },
  validateGraph: async (incidentId: number) => {
    const res = await apiClient.post(`/incidents/${incidentId}/graph/validate`);
    return res.data;
  },
  autoSynthesize: async (incidentId: number): Promise<EventGraphResponse> => {
    const res = await apiClient.post(`/incidents/${incidentId}/graph/auto-synthesize`);
    return res.data;
  },
};

export const reportApi = {
  generate: async (
    incidentId: number,
    options?: { customInstructions?: string; forceMock?: boolean; modelName?: string }
  ): Promise<ReportResponse> => {
    const res = await apiClient.post(`/reports/incidents/${incidentId}/generate`, {
      custom_instructions: options?.customInstructions,
      force_mock: options?.forceMock,
      model_name: options?.modelName,
    });
    return res.data;
  },
  get: async (reportId: number): Promise<ReportResponse> => {
    const res = await apiClient.get(`/reports/${reportId}`);
    return res.data;
  },
  getByIncident: async (incidentId: number): Promise<ReportResponse[]> => {
    const res = await apiClient.get(`/reports/incidents/${incidentId}`);
    return res.data;
  },
  correctStatement: async (
    reportId: number,
    statementId: number,
    data: { corrected_text: string; analyst_comment: string }
  ): Promise<ReportResponse> => {
    const res = await apiClient.patch(`/reports/${reportId}/statements/${statementId}`, data);
    return res.data;
  },
  review: async (
    reportId: number,
    data: { action: 'APPROVE' | 'REJECT' | 'REQUEST_REVISIONS'; reviewer_comments?: string }
  ): Promise<ReportResponse> => {
    const res = await apiClient.post(`/reports/${reportId}/review`, data);
    return res.data;
  },
  getAuditHistory: async (reportId: number): Promise<AuditHistoryEntry[]> => {
    const res = await apiClient.get(`/reports/${reportId}/audit-history`);
    return res.data;
  },
  getPdfDownloadUrl: (reportId: number): string => {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
    const token = localStorage.getItem('sentinel_token');
    return `${baseUrl}/reports/${reportId}/export-pdf${token ? `?token=${encodeURIComponent(token)}` : ''}`;
  },
};

export const edgeApi = {
  getStatus: async (): Promise<EdgeStatusResponse> => {
    const res = await apiClient.get('/edge/status');
    return res.data;
  },
  updateNetworkState: async (state: NetworkState, reason?: string): Promise<EdgeStatusResponse> => {
    const res = await apiClient.post('/edge/network-state', { state, reason });
    return res.data;
  },
  triggerSync: async (batchSize?: number, forceSync?: boolean): Promise<SyncResponse> => {
    const res = await apiClient.post('/edge/sync', { batch_size: batchSize, force_sync: forceSync });
    return res.data;
  },
  getBufferedEvents: async (limit?: number): Promise<BufferedEventItem[]> => {
    const res = await apiClient.get('/edge/buffer/events', { params: { limit } });
    return res.data;
  },
  purgeBuffer: async (): Promise<PurgeResponse> => {
    const res = await apiClient.post('/edge/buffer/purge');
    return res.data;
  },
  runBenchmark: async (numEvents?: number, simulateRestart?: boolean): Promise<EdgeBenchmarkResponse> => {
    const res = await apiClient.post('/edge/benchmark', {
      num_events: numEvents ?? 20,
      simulate_restart: simulateRestart ?? true,
    });
    return res.data;
  },
};

export const copilotApi = {
  chat: async (req: CopilotChatRequest): Promise<CopilotChatResponse> => {
    const res = await apiClient.post('/ai/copilot/chat', req);
    return res.data;
  },
};

export const auditApi = {
  getLogs: async (params?: { action?: string; resource_type?: string; limit?: number; offset?: number }): Promise<AuditLogEntry[]> => {
    const res = await apiClient.get('/audit/logs', { params });
    return res.data;
  },
  getSettings: async (): Promise<SystemSettings> => {
    const res = await apiClient.get('/audit/settings');
    return res.data;
  },
  updateSettings: async (data: UpdateSettingsRequest): Promise<SystemSettings> => {
    const res = await apiClient.post('/audit/settings', data);
    return res.data;
  },
};

