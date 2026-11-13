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
  checksum_sha256?: string;
  source_timestamp?: string;
  mime_type?: string;
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  error_message?: string;
  total_detections_count?: number;
  total_tracked_objects_count?: number;
  total_incidents_count?: number;
  processing_progress?: number;
  camera_id?: number;
  created_at?: string;
}

export interface VideoIngestionStatus {
  id: number;
  filename: string;
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  duration?: number;
  resolution?: string;
  fps?: number;
  total_frames?: number;
  file_size_bytes?: number;
  checksum_sha256?: string;
  source_timestamp?: string;
  error_message?: string;
  created_at?: string;
}

export interface RTSPTestResponse {
  connected: boolean;
  stream_url: string;
  fps?: number;
  resolution?: string;
  latency_ms?: number;
  message: string;
  tested_at: string;
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

export type RelationshipType =
  | 'OBSERVED_BY'
  | 'DETECTED_IN'
  | 'TRIGGERED'
  | 'PART_OF'
  | 'SUPPORTS'
  | 'CONFLICTS_WITH'
  | 'CORROBORATES'
  | 'EXTRACTED_FROM'
  | 'ANALYZED_BY'
  | 'DOCUMENTED_IN'
  | 'SUPERSEDES'
  | 'FLAGS_MISSING';

export type ProvenanceType =
  | 'DIRECT_OBSERVATION'
  | 'INFERRED_ASSOCIATION'
  | 'ANALYST_ASSERTION'
  | 'DERIVED_SYNTHESIS';

export type ObservationType =
  | 'DIRECT_FACT'
  | 'INFERRED_HYPOTHESIS'
  | 'CONFLICT_RECORD'
  | 'MISSING_DATA_GAP';

export interface EventLink {
  id: number;
  incident_id: number;
  source_node_type: string;
  source_node_id: number;
  source_ref?: string;
  target_node_type: string;
  target_node_id: number;
  target_ref?: string;
  relationship_type: RelationshipType;
  provenance_type: ProvenanceType;
  creation_reason: string;
  confidence: number;
  source_timestamp?: string;
  target_timestamp?: string;
  is_conflict: boolean;
  conflict_details?: Record<string, any>;
  is_missing_evidence: boolean;
  metadata_json?: Record<string, any>;
  valid_from: string;
  valid_to?: string;
  created_at: string;
}

export interface GraphNode {
  id: string;
  node_type: string;
  entity_id: number;
  label: string;
  timestamp?: string;
  provenance_type: string;
  status?: string;
  metadata?: Record<string, any>;
}

export interface EventGraphResponse {
  incident_id: number;
  incident_number: string;
  nodes: GraphNode[];
  edges: EventLink[];
  total_nodes: number;
  total_edges: number;
  conflicts_count: number;
  missing_evidence_count: number;
  direct_facts_count: number;
  inferred_count: number;
}

export interface EvidenceChainStep {
  step_number: number;
  node_type: string;
  node_id: number;
  label: string;
  timestamp?: string;
  provenance_type: string;
  relationship_from_parent?: string;
  creation_reason?: string;
  is_verified_in_db: boolean;
  source_identifier?: string;
  evidence_sha256?: string;
  details?: Record<string, any>;
}

export interface EvidenceChainResponse {
  incident_id: number;
  incident_number: string;
  chain: EvidenceChainStep[];
  is_chain_intact: boolean;
  unresolved_conflicts: number;
  missing_evidence_gaps: number;
}

export type StatementType = 'OBSERVATION' | 'CV_DETECTION' | 'MODEL_INTERPRETATION' | 'HUMAN_ANNOTATION';
export type CitationValidationStatus = 'VERIFIED' | 'FLAGGED_UNSUPPORTED' | 'FLAGGED_TIMESTAMP_MISMATCH' | 'FLAGGED_NONEXISTENT';
export type ReviewStatus = 'DRAFT' | 'PENDING_REVIEW' | 'APPROVED' | 'REJECTED';

export interface FactualStatementItem {
  statement_id: number;
  text: string;
  statement_type: StatementType;
  referenced_entity_type?: string;
  referenced_entity_id?: number;
  timestamp?: string;
  supporting_evidence_ids: number[];
  citation_status: CitationValidationStatus;
  validation_notes?: string;
  human_correction?: string;
}

export interface ConflictingEvidenceItem {
  description: string;
  conflicting_nodes: string[];
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
}

export interface MissingEvidenceItem {
  description: string;
  interval?: string;
  impact?: string;
}

export interface EvidenceUsedItem {
  evidence_id: number;
  evidence_type: string;
  file_path: string;
  checksum_sha256?: string;
  timestamp?: string;
}

export interface IncidentReportSections {
  executive_summary: string;
  factual_statements: FactualStatementItem[];
  conflicting_evidence: ConflictingEvidenceItem[];
  missing_evidence_gaps: MissingEvidenceItem[];
  containment_recommendations: string[];
  insufficient_evidence: boolean;
  insufficient_evidence_reason?: string;
  evidence_used: EvidenceUsedItem[];
}

export interface AuditHistoryEntry {
  timestamp: string;
  action: string;
  user_id?: number;
  details?: Record<string, any>;
}

export interface ReportResponse {
  id: number;
  report_number: string;
  incident_id: number;
  title: string;
  status: string;
  review_status: ReviewStatus;
  model_name?: string;
  prompt_version?: string;
  sections: IncidentReportSections;
  unsupported_claim_count: number;
  valid_citation_rate: number;
  generated_by_user_id?: number;
  approved_by_user_id?: number;
  approved_at?: string;
  file_path?: string;
  pdf_download_url?: string;
  checksum_sha256?: string;
  created_at: string;
  audit_history: AuditHistoryEntry[];
}

// Phase 8: Edge Operation and Store-and-Forward Types
export type NetworkState = 'ONLINE' | 'OFFLINE' | 'DEGRADED';

export interface BufferStats {
  total_buffered_events: number;
  pending_sync_count: number;
  synced_count: number;
  quarantined_count: number;
  pending_evidence_count: number;
  oldest_pending_timestamp?: string;
  db_file_size_bytes: number;
}

export interface DiskMetrics {
  total_bytes: number;
  free_bytes: number;
  used_bytes: number;
  used_percent: number;
  buffer_size_bytes: number;
  buffer_size_mb: number;
  max_quota_mb: number;
  quota_utilization_percent: number;
  is_warning: boolean;
  is_quota_breached: boolean;
}

export interface EdgeStatusResponse {
  edge_node_id: string;
  network_state: NetworkState;
  last_state_change: string;
  offline_reason?: string;
  buffer_stats: BufferStats;
  disk_metrics: DiskMetrics;
}

export interface SyncResponse {
  session_id: string;
  status: string;
  events_synced: number;
  evidence_synced: number;
  duplicates_prevented: number;
  conflicts_resolved: number;
  bytes_transferred: number;
  duration_ms: number;
  errors_count: number;
  remaining_pending: number;
  message?: string;
}

export interface PurgeResponse {
  files_deleted: number;
  bytes_freed: number;
  bytes_freed_mb: number;
  remaining_buffer_mb: number;
  status: string;
}

export interface BufferedEventItem {
  id: number;
  client_event_id: string;
  event_type: string;
  severity: string;
  camera_id?: number;
  video_id?: number;
  detected_at: string;
  description: string;
  confidence: number;
  metadata_json: Record<string, any>;
  snapshot_path?: string;
  clip_path?: string;
  edge_node_id?: string;
  status: string;
  retry_count: number;
  next_retry_at?: string;
  last_error?: string;
  created_at: string;
}

export interface EdgeBenchmarkResponse {
  test_name: string;
  total_events_generated: number;
  events_recovered: number;
  event_loss_pct: number;
  duplicate_events_prevented: number;
  duplicate_detection_accuracy_pct: number;
  recovery_time_ms: number;
  mean_sync_delay_ms: number;
  timestamp_preservation_accuracy_pct: number;
  evidence_hash_match_pct: number;
  buffer_db_size_bytes: number;
  status: string;
}

export interface CopilotToolCall {
  tool_name: string;
  arguments: Record<string, any>;
  result?: Record<string, any>;
  status: string;
  execution_time_ms: number;
}

export interface CopilotPendingConfirmation {
  action_id: string;
  action_type: string;
  description: string;
  target_id: number;
  parameters: Record<string, any>;
  prompt: string;
}

export interface CopilotChatResponse {
  response: string;
  tool_calls: CopilotToolCall[];
  pending_confirmation?: CopilotPendingConfirmation;
  suggested_queries: string[];
  model_used: string;
}

export interface CopilotChatRequest {
  message: string;
  conversation_history?: Array<{ role: string; content: string }>;
  camera_id?: number;
  incident_id?: number;
  confirmed_action?: CopilotPendingConfirmation;
}

export interface AuditLogEntry {
  id: number;
  user_id?: number;
  user_email?: string;
  action: string;
  resource_type?: string;
  resource_id?: string;
  details: Record<string, any>;
  ip_address?: string;
  created_at: string;
}

export interface SystemSettings {
  app_name: string;
  app_version: string;
  app_env: string;
  edge_mode: boolean;
  edge_node_id: string;
  edge_buffer_max_disk_mb: number;
  edge_buffer_retention_days: number;
  gemini_model: string;
  max_upload_size_mb: number;
  max_video_duration_seconds: number;
  total_audit_logs_count: number;
  edge_sync_batch_size?: number;
}

export interface UpdateSettingsRequest {
  edge_buffer_retention_days?: number;
  edge_sync_batch_size?: number;
}


