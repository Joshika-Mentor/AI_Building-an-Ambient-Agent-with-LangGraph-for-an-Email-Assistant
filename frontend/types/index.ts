/**
 * ThreatLens AI - TypeScript Type Definitions
 */

// ─── User Types ─────────────────────────────────────────────────

export type UserRole = 'security_analyst' | 'soc_member' | 'administrator' | 'researcher';

export interface User {
  id: number;
  email: string;
  username: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  last_login: string | null;
  created_at: string;
  updated_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  username: string;
  password: string;
  full_name: string;
  role: UserRole;
}

// ─── File Analysis Types ────────────────────────────────────────

export type AnalysisStatus = 'pending' | 'analyzing' | 'completed' | 'failed';
export type RiskLevel = 'Critical' | 'High' | 'Medium' | 'Low' | 'Clean';

export interface PEHeaderInfo {
  entry_point: string | null;
  image_base: string | null;
  number_of_sections: number | null;
  timestamp: string | null;
  characteristics: string[] | null;
  is_dll: boolean | null;
  is_exe: boolean | null;
  machine_type: string | null;
  sections: PESection[] | null;
}

export interface PESection {
  name: string;
  virtual_size: number;
  raw_size: number;
  entropy: number;
  is_suspicious: boolean;
}

export interface SuspiciousAPI {
  dll: string;
  function: string;
  description: string;
}

export interface YARAMatch {
  rule_name: string;
  namespace: string;
  tags: string[];
  description: string;
  severity: string;
  category: string;
  strings_matched: number;
}

export interface StaticAnalysisResult {
  pe_info: PEHeaderInfo | null;
  suspicious_strings: string[] | null;
  suspicious_urls: string[] | null;
  suspicious_ips: string[] | null;
  suspicious_apis: SuspiciousAPI[] | null;
  yara_matches: YARAMatch[] | null;
  behavioral_indicators: string[] | null;
}

export interface FileAnalysis {
  id: number;
  filename: string;
  original_name: string;
  file_size: number;
  file_type: string | null;
  mime_type: string | null;
  md5_hash: string | null;
  sha256_hash: string | null;
  status: AnalysisStatus;
  risk_score: number | null;
  risk_level: RiskLevel | null;
  analysis: StaticAnalysisResult | null;
  uploaded_by: number;
  upload_date: string;
  analysis_completed_at: string | null;
  error_message: string | null;
}

export interface FileListResponse {
  files: FileAnalysis[];
  total: number;
  page: number;
  page_size: number;
}

// ─── Classification Types ───────────────────────────────────────

export interface ClassificationResult {
  id: number;
  file_analysis_id: number;
  malware_class: string;
  malware_family: string | null;
  confidence_score: number;
  risk_score: number;
  model_version: string | null;
  class_probabilities: Record<string, number> | null;
  incident_id: string | null;
  classified_at: string;
}

// ─── Threat Types ───────────────────────────────────────────────

export interface ThreatIncident {
  id: number;
  incident_id: string;
  title: string;
  description: string | null;
  severity: string;
  status: string;
  threat_type: string | null;
  risk_score: number | null;
  assigned_to: number | null;
  created_at: string;
  updated_at: string | null;
  resolved_at: string | null;
}

// ─── Alert Types ────────────────────────────────────────────────

export interface Alert {
  id: number;
  title: string;
  description: string | null;
  severity: string;
  status: string;
  source: string | null;
  alert_type: string | null;
  related_file_id: number | null;
  assigned_to: number | null;
  is_read: boolean;
  created_at: string;
  acknowledged_at: string | null;
  resolved_at: string | null;
}

export interface AlertListResponse {
  alerts: Alert[];
  total: number;
  page: number;
  page_size: number;
  unread_count: number;
}

// ─── Analytics Types ────────────────────────────────────────────

export interface OverviewStats {
  total_scans: number;
  threats_detected: number;
  average_risk_score: number;
  active_alerts: number;
  scans_today: number;
  critical_alerts: number;
}

export interface MalwareDistribution {
  distribution: Record<string, number>;
  total: number;
}

export interface ThreatTrend {
  date: string;
  count: number;
  risk_avg: number;
}

export interface RiskDistribution {
  clean: number;
  low: number;
  medium: number;
  high: number;
  critical: number;
}

// ─── Classification List Types ──────────────────────────────────

export interface ClassificationListResponse {
  classifications: ClassificationResult[];
  total: number;
  page: number;
  page_size: number;
}

export interface ClassificationStatsResponse {
  total_classifications: number;
  malware_distribution: Record<string, number>;
  avg_confidence: number;
  avg_risk_score: number;
  recent_classifications: ClassificationResult[];
}

// ─── Threat List Types ──────────────────────────────────────────

export interface ThreatListResponse {
  threats: ThreatIncident[];
  total: number;
  page: number;
  page_size: number;
}

export interface ThreatStats {
  total_incidents: number;
  open_incidents: number;
  by_severity: Record<string, number>;
  by_status: Record<string, number>;
  by_threat_type: Record<string, number>;
}

// ─── Alert Stats Types ──────────────────────────────────────────

export interface AlertStats {
  total_alerts: number;
  by_severity: Record<string, number>;
  by_status: Record<string, number>;
  recent_alerts: Alert[];
}

