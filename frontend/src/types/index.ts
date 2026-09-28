export type UserRole = 'ADMIN' | 'SECURITY_ANALYST' | 'OPERATOR' | 'VIEWER';

export interface User {
  id: number;
  name: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export type CameraStatus = 'ONLINE' | 'OFFLINE' | 'DEGRADED' | 'UNKNOWN';

export interface ZoneCoordinate {
  x: number;
  y: number;
}

export interface RestrictedZone {
  id: string;
  name: string;
  polygon: ZoneCoordinate[];
  alert_severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
}

export interface VirtualLine {
  id: string;
  name: string;
  p1: ZoneCoordinate;
  p2: ZoneCoordinate;
  direction: 'BOTH' | 'A_TO_B' | 'B_TO_A';
  alert_severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
}

export interface Camera {
  id: number;
  name: string;
  camera_identifier: string;
  location: string;
  latitude?: number;
  longitude?: number;
  stream_url?: string;
  status: CameraStatus;
  zone?: string;
  restricted_zones?: RestrictedZone[];
  virtual_lines?: VirtualLine[];
  recent_events_count?: number;
  created_at?: string;
  updated_at?: string;
}

export interface DemoVideoInfo {
  id: string;
  title: string;
  filename: string;
  scenario: string;
  duration_seconds: number;
  resolution: string;
  description: string;
  target_camera: string;
}

export interface Video {
  id: number;
  filename: string;
  original_filename?: string;
  path: string;
  processed_path?: string;
  processed_url?: string;
  duration?: number;
  resolution?: string;
  fps?: number;
  total_frames?: number;
  file_size_bytes?: number;
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  error_message?: string;
  total_detections_count?: number;
  total_tracked_objects_count?: number;
  total_incidents_count?: number;
  processing_progress?: number;
  camera_id?: number;
  created_at?: string;
}

export interface Detection {
  id: number;
  video_id: number;
  camera_id?: number;
  timestamp_offset: number;
  frame_number: number;
  object_type: string;
  confidence: number;
  bbox: [number, number, number, number];
  tracking_id?: number;
}

export type EventType =
  | 'PERSON_DETECTED'
  | 'VEHICLE_DETECTED'
  | 'MULTIPLE_PERSONS'
  | 'LINE_CROSSING'
  | 'RESTRICTED_ZONE_ENTRY'
  | 'LOITERING'
  | 'UNUSUAL_ACTIVITY'
  | 'OBJECT_LEFT_BEHIND'
  | 'CAMERA_TAMPERING'
  | 'CAMERA_OFFLINE';

export type SeverityLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface SecurityEvent {
  id: number;
  event_type: EventType;
  severity: SeverityLevel;
  camera_id?: number;
  camera_name?: string;
  video_id?: number;
  timestamp: string;
  description: string;
  confidence: number;
  status?: string;
  metadata?: Record<string, any>;
  snapshot_path?: string;
  clip_path?: string;
  incident_id?: number;
  created_at?: string;
}

export type AlertStatus = 'NEW' | 'ACKNOWLEDGED' | 'INVESTIGATING' | 'RESOLVED' | 'DISMISSED';

export interface Alert {
  id: number;
  event_id?: number;
  event?: SecurityEvent;
  camera_id?: number;
  camera_name?: string;
  severity: SeverityLevel;
  title: string;
  message: string;
  status: AlertStatus;
  acknowledged_by?: string;
  acknowledged_at?: string;
  created_at: string;
}

export type IncidentStatus = 'OPEN' | 'IN_PROGRESS' | 'RESOLVED' | 'CLOSED';

export interface Incident {
  id: number;
  incident_number: string;
  title: string;
  description: string;
  severity: SeverityLevel;
  status: IncidentStatus;
  ai_summary?: string;
  ai_recommendations?: string[];
  analyst_notes?: string;
  created_at: string;
  updated_at: string;
  events?: SecurityEvent[];
  alerts?: Alert[];
  evidence_count?: number;
}

export interface Evidence {
  id: number;
  incident_id?: number;
  event_id?: number;
  evidence_type: 'SNAPSHOT' | 'VIDEO_CLIP' | 'REPORT' | 'METADATA';
  file_path: string;
  file_url: string;
  file_size_bytes?: number;
  checksum_sha256?: string;
  timestamp: string;
  created_at?: string;
}

export interface AnalyticsOverview {
  total_cameras: number;
  active_cameras: number;
  total_events_today: number;
  active_alerts: number;
  critical_incidents: number;
  events_by_type: Record<string, number>;
  events_by_severity: Record<string, number>;
  camera_health_summary?: Record<string, number>;
  recent_activity_timeline?: Array<{ timestamp: string; count: number; severity: string }>;
}
