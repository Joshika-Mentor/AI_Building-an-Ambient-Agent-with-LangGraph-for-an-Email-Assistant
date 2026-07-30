'use client';

import { useState, useEffect } from 'react';
import {
  FileText, Shield, TrendingUp, AlertTriangle, Download,
  RefreshCw, Loader2, ChevronDown, ChevronUp, BarChart3,
  CheckCircle, XCircle, Target, Clock, Zap, Eye,
} from 'lucide-react';
import {
  PieChart, Pie, Cell, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import api from '@/lib/api';

// ─── Types ──────────────────────────────────────────────────────────

interface ExecutiveSummary {
  report_type: string;
  generated_at: string;
  security_score: number;
  overview: {
    total_scans: number;
    scans_this_week: number;
    scans_this_month: number;
    threats_detected: number;
    average_risk_score: number;
    detection_rate: number;
  };
  risk_distribution: Record<string, number>;
  malware_breakdown: Record<string, number>;
  incident_summary: { open_incidents: number; unresolved_alerts: number };
}

interface ThreatLandscape {
  report_type: string;
  generated_at: string;
  recent_detections: any[];
  top_threats: { class: string; count: number }[];
  top_families: { family: string; count: number }[];
  severity_breakdown: Record<string, number>;
}

// ─── Palette ────────────────────────────────────────────────────────

const COLORS = ['#10b981', '#6366f1', '#f59e0b', '#f97316', '#ef4444', '#a855f7', '#ec4899'];
const RISK_COLORS: Record<string, string> = {
  clean: '#10b981', low: '#6366f1', medium: '#f59e0b', high: '#f97316', critical: '#ef4444',
};

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="glass rounded-xl px-4 py-3 border border-[var(--color-border)] shadow-lg">
      <p className="text-xs text-[var(--color-text-muted)] mb-1">{label}</p>
      {payload.map((p: any, i: number) => (
        <p key={i} className="text-sm font-semibold" style={{ color: p.color || p.fill }}>
          {p.name}: {p.value}
        </p>
      ))}
    </div>
  );
};

export default function ReportsPage() {
  const [activeTab, setActiveTab] = useState<'executive' | 'landscape'>('executive');
  const [executive, setExecutive] = useState<ExecutiveSummary | null>(null);
  const [landscape, setLandscape] = useState<ThreatLandscape | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedSection, setExpandedSection] = useState<string | null>('overview');

  useEffect(() => { fetchReports(); }, []);

  const fetchReports = async () => {
    setLoading(true);
    try {
      const [execRes, landRes] = await Promise.allSettled([
        api.get<ExecutiveSummary>('/reports/executive-summary'),
        api.get<ThreatLandscape>('/reports/threat-landscape'),
      ]);

      if (execRes.status === 'fulfilled') setExecutive(execRes.value.data);
      if (landRes.status === 'fulfilled') setLandscape(landRes.value.data);
    } catch (err) {
      console.error('Report fetch failed:', err);
    } finally { setLoading(false); }
  };

  const downloadReport = () => {
    const report = activeTab === 'executive' ? executive : landscape;
    if (!report) return;
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `threatlens_${activeTab}_report_${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const toggleSection = (key: string) => {
    setExpandedSection(expandedSection === key ? null : key);
  };

  // ─── Derived Data ─────────────────────────────────────────────────

  const riskPieData = executive
    ? Object.entries(executive.risk_distribution).map(([name, value]) => ({
        name: name.charAt(0).toUpperCase() + name.slice(1),
        value,
        color: RISK_COLORS[name] || '#6366f1',
      }))
    : [];

  const malwareBarData = executive
    ? Object.entries(executive.malware_breakdown)
        .sort(([, a], [, b]) => b - a)
        .map(([name, value], i) => ({
          name,
          count: value,
          color: COLORS[i % COLORS.length],
        }))
    : [];

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-[var(--color-accent)]';
    if (score >= 60) return 'text-[var(--color-primary)]';
    if (score >= 40) return 'text-[var(--color-warning)]';
    return 'text-[var(--color-danger)]';
  };

  const getScoreLabel = (score: number) => {
    if (score >= 80) return 'Excellent';
    if (score >= 60) return 'Good';
    if (score >= 40) return 'Fair';
    if (score >= 20) return 'Poor';
    return 'Critical';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-32">
        <Loader2 className="w-10 h-10 text-[var(--color-primary)] animate-spin" />
        <span className="ml-4 text-lg text-[var(--color-text-muted)]">Generating reports...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--color-text)]">Security Reports</h1>
          <p className="text-sm text-[var(--color-text-muted)] mt-1">
            Comprehensive security reports, executive summaries, and threat landscape analysis.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={downloadReport}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[var(--color-accent)]/10 text-[var(--color-accent)] hover:bg-[var(--color-accent)]/20 transition-colors text-sm font-medium"
          >
            <Download className="w-4 h-4" />
            Export JSON
          </button>
          <button
            onClick={fetchReports}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[var(--color-primary)]/10 text-[var(--color-primary)] hover:bg-[var(--color-primary)]/20 transition-colors text-sm font-medium"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </div>

      {/* Tab Switcher */}
      <div className="flex items-center gap-1 p-1 rounded-xl bg-white/5 border border-[var(--color-border)] w-fit">
        {[
          { key: 'executive', label: 'Executive Summary', icon: FileText },
          { key: 'landscape', label: 'Threat Landscape', icon: Target },
        ].map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key as any)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === key
                ? 'bg-[var(--color-primary)]/20 text-[var(--color-primary)]'
                : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-white/5'
            }`}
          >
            <Icon className="w-4 h-4" />
            {label}
          </button>
        ))}
      </div>

      {/* ═══ Executive Summary Tab ═══ */}
      {activeTab === 'executive' && executive && (
        <div className="space-y-4">
          {/* Security Score Hero */}
          <div className="glass rounded-2xl p-8 text-center animate-slide-up">
            <div className="text-xs text-[var(--color-text-muted)] uppercase tracking-widest mb-3">Security Health Score</div>
            <div className={`text-7xl font-black ${getScoreColor(executive.security_score)} mb-2`}>
              {executive.security_score}
            </div>
            <div className={`text-lg font-medium ${getScoreColor(executive.security_score)}`}>
              {getScoreLabel(executive.security_score)}
            </div>
            <div className="mt-4 w-full max-w-md mx-auto h-3 rounded-full bg-white/5 overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-1000"
                style={{
                  width: `${executive.security_score}%`,
                  background: `linear-gradient(90deg, ${
                    executive.security_score >= 60 ? '#10b981' : executive.security_score >= 40 ? '#f59e0b' : '#ef4444'
                  }, ${
                    executive.security_score >= 80 ? '#06b6d4' : executive.security_score >= 60 ? '#10b981' : '#f97316'
                  })`,
                }}
              />
            </div>
            <div className="text-xs text-[var(--color-text-muted)] mt-3">
              Generated {new Date(executive.generated_at).toLocaleString()} · Last 30 days
            </div>
          </div>

          {/* KPI Row */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            {[
              { label: 'Total Scans', value: executive.overview.total_scans, icon: Eye },
              { label: 'This Week', value: executive.overview.scans_this_week, icon: Clock },
              { label: 'This Month', value: executive.overview.scans_this_month, icon: BarChart3 },
              { label: 'Threats', value: executive.overview.threats_detected, icon: Shield },
              { label: 'Avg Risk', value: executive.overview.average_risk_score, icon: TrendingUp },
              { label: 'Detection Rate', value: `${executive.overview.detection_rate}%`, icon: Zap },
            ].map((k, i) => (
              <div key={i} className={`glass rounded-xl p-4 animate-slide-up stagger-${Math.min(i + 1, 6)}`}>
                <k.icon className="w-4 h-4 text-[var(--color-primary)] mb-2" />
                <div className="text-lg font-bold text-[var(--color-text)]">{k.value}</div>
                <div className="text-[10px] text-[var(--color-text-muted)] uppercase">{k.label}</div>
              </div>
            ))}
          </div>

          {/* Charts: Risk Distribution + Malware Breakdown */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Risk Pie */}
            <div className="glass rounded-2xl p-6">
              <h3 className="text-sm font-semibold text-[var(--color-text)] mb-4">Risk Distribution</h3>
              {riskPieData.some(d => d.value > 0) ? (
                <div className="flex items-center gap-4">
                  <ResponsiveContainer width="50%" height={200}>
                    <PieChart>
                      <Pie data={riskPieData} cx="50%" cy="50%" innerRadius={45} outerRadius={75} paddingAngle={3} dataKey="value" strokeWidth={0}>
                        {riskPieData.map((d, i) => (
                          <Cell key={i} fill={d.color} />
                        ))}
                      </Pie>
                      <Tooltip content={<CustomTooltip />} />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="flex-1 space-y-2">
                    {riskPieData.filter(d => d.value > 0).map((d) => (
                      <div key={d.name} className="flex items-center gap-2">
                        <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: d.color }} />
                        <span className="text-xs text-[var(--color-text-muted)] flex-1">{d.name}</span>
                        <span className="text-xs font-bold text-[var(--color-text)]">{d.value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-center h-[200px] text-sm text-[var(--color-text-muted)]">No data</div>
              )}
            </div>

            {/* Malware Bar Chart */}
            <div className="glass rounded-2xl p-6">
              <h3 className="text-sm font-semibold text-[var(--color-text)] mb-4">Malware Classification Breakdown</h3>
              {malwareBarData.length > 0 ? (
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={malwareBarData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="name" tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.4)' }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.4)' }} axisLine={false} tickLine={false} />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar dataKey="count" name="Detections" radius={[6, 6, 0, 0]}>
                      {malwareBarData.map((d, i) => (
                        <Cell key={i} fill={d.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-[200px] text-sm text-[var(--color-text-muted)]">No classifications yet</div>
              )}
            </div>
          </div>

          {/* Incident Summary */}
          <div className="glass rounded-2xl p-6">
            <h3 className="text-sm font-semibold text-[var(--color-text)] mb-4">Incident Summary</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="rounded-xl bg-white/3 p-5 flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-[var(--color-warning)]/10 flex items-center justify-center">
                  <AlertTriangle className="w-6 h-6 text-[var(--color-warning)]" />
                </div>
                <div>
                  <div className="text-2xl font-bold text-[var(--color-text)]">{executive.incident_summary.open_incidents}</div>
                  <div className="text-xs text-[var(--color-text-muted)]">Open Incidents</div>
                </div>
              </div>
              <div className="rounded-xl bg-white/3 p-5 flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-[var(--color-danger)]/10 flex items-center justify-center">
                  <XCircle className="w-6 h-6 text-[var(--color-danger)]" />
                </div>
                <div>
                  <div className="text-2xl font-bold text-[var(--color-text)]">{executive.incident_summary.unresolved_alerts}</div>
                  <div className="text-xs text-[var(--color-text-muted)]">Unresolved Alerts</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ═══ Threat Landscape Tab ═══ */}
      {activeTab === 'landscape' && landscape && (
        <div className="space-y-4">
          {/* Top Threats + Top Families */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Top Threats */}
            <div className="glass rounded-2xl p-6 animate-slide-up stagger-1">
              <h3 className="text-sm font-semibold text-[var(--color-text)] mb-4">Top Threat Categories</h3>
              {landscape.top_threats.length > 0 ? (
                <div className="space-y-3">
                  {landscape.top_threats.map((t, i) => {
                    const max = landscape.top_threats[0]?.count || 1;
                    return (
                      <div key={t.class} className="space-y-1">
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-[var(--color-text)]">{t.class}</span>
                          <span className="font-mono font-bold" style={{ color: COLORS[i % COLORS.length] }}>{t.count}</span>
                        </div>
                        <div className="h-2 rounded-full bg-white/5 overflow-hidden">
                          <div
                            className="h-full rounded-full transition-all duration-700"
                            style={{ width: `${(t.count / max) * 100}%`, backgroundColor: COLORS[i % COLORS.length], minWidth: '8px' }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="text-sm text-[var(--color-text-muted)] text-center py-8">No threat data yet</div>
              )}
            </div>

            {/* Top Families */}
            <div className="glass rounded-2xl p-6 animate-slide-up stagger-2">
              <h3 className="text-sm font-semibold text-[var(--color-text)] mb-4">Top Malware Families</h3>
              {landscape.top_families.length > 0 ? (
                <div className="space-y-3">
                  {landscape.top_families.map((f, i) => {
                    const max = landscape.top_families[0]?.count || 1;
                    return (
                      <div key={f.family} className="flex items-center gap-3">
                        <div className="w-6 h-6 rounded-md flex items-center justify-center text-[10px] font-bold text-white" style={{ backgroundColor: COLORS[i % COLORS.length] }}>
                          {i + 1}
                        </div>
                        <span className="text-sm text-[var(--color-text)] flex-1">{f.family}</span>
                        <span className="text-sm font-bold text-[var(--color-text-muted)]">{f.count}</span>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="text-sm text-[var(--color-text-muted)] text-center py-8">No family data yet</div>
              )}
            </div>
          </div>

          {/* Severity Breakdown */}
          {Object.keys(landscape.severity_breakdown).length > 0 && (
            <div className="glass rounded-2xl p-6 animate-slide-up stagger-3">
              <h3 className="text-sm font-semibold text-[var(--color-text)] mb-4">Incident Severity Distribution</h3>
              <div className="grid grid-cols-4 gap-3">
                {['Critical', 'High', 'Medium', 'Low'].map((sev) => {
                  const count = landscape.severity_breakdown[sev] || 0;
                  const sevColors: Record<string, string> = { Critical: '#ef4444', High: '#f97316', Medium: '#f59e0b', Low: '#6366f1' };
                  return (
                    <div key={sev} className="rounded-xl bg-white/3 p-4 text-center">
                      <div className="text-3xl font-black mb-1" style={{ color: sevColors[sev] }}>{count}</div>
                      <div className="text-xs text-[var(--color-text-muted)]">{sev}</div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Recent Detections Table */}
          <div className="glass rounded-2xl overflow-hidden animate-slide-up stagger-4">
            <div className="px-6 py-4 border-b border-[var(--color-border)]">
              <h3 className="text-sm font-semibold text-[var(--color-text)]">Recent Detections</h3>
            </div>
            {landscape.recent_detections.length > 0 ? (
              <>
                <div className="grid grid-cols-[1fr_100px_100px_80px_80px_120px] gap-4 px-6 py-2 border-b border-[var(--color-border)] bg-white/2">
                  <div className="text-[10px] font-semibold text-[var(--color-text-muted)] uppercase">File</div>
                  <div className="text-[10px] font-semibold text-[var(--color-text-muted)] uppercase">Class</div>
                  <div className="text-[10px] font-semibold text-[var(--color-text-muted)] uppercase">Family</div>
                  <div className="text-[10px] font-semibold text-[var(--color-text-muted)] uppercase">Confidence</div>
                  <div className="text-[10px] font-semibold text-[var(--color-text-muted)] uppercase">Risk</div>
                  <div className="text-[10px] font-semibold text-[var(--color-text-muted)] uppercase">Date</div>
                </div>
                {landscape.recent_detections.map((d, i) => (
                  <div key={i} className="grid grid-cols-[1fr_100px_100px_80px_80px_120px] gap-4 px-6 py-3 border-b border-[var(--color-border)] hover:bg-white/2 transition-colors">
                    <div className="text-sm text-[var(--color-text)] truncate">{d.file_name}</div>
                    <div>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        d.malware_class === 'Clean' ? 'bg-[var(--color-accent)]/10 text-[var(--color-accent)]' :
                        'bg-[var(--color-danger)]/10 text-[var(--color-danger)]'
                      }`}>
                        {d.malware_class}
                      </span>
                    </div>
                    <div className="text-xs text-[var(--color-text-muted)]">{d.malware_family || '—'}</div>
                    <div className="text-xs font-mono text-[var(--color-text)]">{(d.confidence * 100).toFixed(0)}%</div>
                    <div className={`text-xs font-bold ${
                      d.risk_score >= 80 ? 'text-[var(--color-danger)]' :
                      d.risk_score >= 60 ? 'text-[#f97316]' :
                      d.risk_score >= 40 ? 'text-[var(--color-warning)]' :
                      'text-[var(--color-accent)]'
                    }`}>
                      {d.risk_score?.toFixed(1)}
                    </div>
                    <div className="text-xs text-[var(--color-text-muted)]">
                      {d.date ? new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—'}
                    </div>
                  </div>
                ))}
              </>
            ) : (
              <div className="text-center py-12 text-sm text-[var(--color-text-muted)]">
                No recent detections. Classify files to populate this report.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Empty state when no data */}
      {activeTab === 'executive' && !executive && (
        <div className="glass rounded-2xl p-12 text-center">
          <FileText className="w-12 h-12 text-[var(--color-primary)]/30 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-[var(--color-text)] mb-2">No Report Data</h3>
          <p className="text-sm text-[var(--color-text-muted)]">Upload and classify files to generate security reports.</p>
        </div>
      )}
    </div>
  );
}
