'use client';

import { useState, useEffect } from 'react';
import { AlertTriangle, Clock, User, Search, ChevronDown, ChevronUp, Shield, Target, Activity, Loader2, RefreshCw, ArrowRight } from 'lucide-react';
import api from '@/lib/api';
import type { ThreatIncident } from '@/types';

const severityConfig: Record<string, { color: string; bg: string; icon: string }> = {
  Critical: { color: 'text-[var(--color-danger)]', bg: 'bg-[var(--color-danger)]/10', icon: '🔴' },
  High: { color: 'text-[#ff6b35]', bg: 'bg-[#ff6b35]/10', icon: '🟠' },
  Medium: { color: 'text-[var(--color-warning)]', bg: 'bg-[var(--color-warning)]/10', icon: '🟡' },
  Low: { color: 'text-[var(--color-primary)]', bg: 'bg-[var(--color-primary)]/10', icon: '🔵' },
  Clean: { color: 'text-[var(--color-accent)]', bg: 'bg-[var(--color-accent)]/10', icon: '🟢' },
};

const statusConfig: Record<string, { color: string; bg: string; label: string }> = {
  open: { color: 'text-[var(--color-danger)]', bg: 'bg-[var(--color-danger)]/10', label: 'Open' },
  investigating: { color: 'text-[var(--color-warning)]', bg: 'bg-[var(--color-warning)]/10', label: 'Investigating' },
  contained: { color: 'text-[var(--color-primary)]', bg: 'bg-[var(--color-primary)]/10', label: 'Contained' },
  resolved: { color: 'text-[var(--color-accent)]', bg: 'bg-[var(--color-accent)]/10', label: 'Resolved' },
};

interface ThreatStats {
  total_incidents: number;
  open_incidents: number;
  by_severity: Record<string, number>;
  by_status: Record<string, number>;
  by_threat_type: Record<string, number>;
}

export default function ThreatsPage() {
  const [threats, setThreats] = useState<ThreatIncident[]>([]);
  const [stats, setStats] = useState<ThreatStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [expandedDetail, setExpandedDetail] = useState<any>(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  useEffect(() => { fetchData(); }, [statusFilter, severityFilter, page]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const params: any = { page, page_size: 15 };
      if (statusFilter) params.status = statusFilter;
      if (severityFilter) params.severity = severityFilter;

      const [threatsRes, statsRes] = await Promise.allSettled([
        api.get('/threats/', { params }),
        api.get('/threats/stats'),
      ]);

      if (threatsRes.status === 'fulfilled') {
        setThreats(threatsRes.value.data.threats);
        setTotal(threatsRes.value.data.total);
      }
      if (statsRes.status === 'fulfilled') {
        setStats(statsRes.value.data);
      }
    } catch (err) {
      console.error('Failed to fetch threats:', err);
    } finally { setLoading(false); }
  };

  const handleStatusUpdate = async (threatId: number, newStatus: string) => {
    try {
      await api.put(`/threats/${threatId}/status`, { status: newStatus });
      fetchData();
    } catch (err) {
      console.error('Status update failed:', err);
    }
  };

  const toggleExpand = async (id: number) => {
    if (expandedId === id) {
      setExpandedId(null);
      setExpandedDetail(null);
      return;
    }
    setExpandedId(id);
    try {
      const res = await api.get(`/threats/${id}`);
      setExpandedDetail(res.data);
    } catch { setExpandedDetail(null); }
  };

  const totalPages = Math.ceil(total / 15);

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--color-text)]">Threat Monitoring</h1>
          <p className="text-sm text-[var(--color-text-muted)] mt-1">
            Monitor active threats, track incident lifecycle, and manage security responses.
          </p>
        </div>
        <button onClick={fetchData} className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[var(--color-primary)]/10 text-[var(--color-primary)] hover:bg-[var(--color-primary)]/20 transition-colors text-sm font-medium">
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="glass rounded-2xl p-5 animate-slide-up stagger-1">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-xl bg-[var(--color-danger)]/10 flex items-center justify-center">
              <Target className="w-5 h-5 text-[var(--color-danger)]" />
            </div>
          </div>
          <div className="text-2xl font-bold text-[var(--color-text)]">{stats?.total_incidents || 0}</div>
          <div className="text-xs text-[var(--color-text-muted)] mt-1">Total Incidents</div>
        </div>
        <div className="glass rounded-2xl p-5 animate-slide-up stagger-2">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-xl bg-[var(--color-warning)]/10 flex items-center justify-center">
              <AlertTriangle className="w-5 h-5 text-[var(--color-warning)]" />
            </div>
          </div>
          <div className="text-2xl font-bold text-[var(--color-warning)]">{stats?.open_incidents || 0}</div>
          <div className="text-xs text-[var(--color-text-muted)] mt-1">Open Incidents</div>
        </div>
        <div className="glass rounded-2xl p-5 animate-slide-up stagger-3">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-xl bg-[var(--color-primary)]/10 flex items-center justify-center">
              <Activity className="w-5 h-5 text-[var(--color-primary)]" />
            </div>
          </div>
          <div className="text-2xl font-bold text-[var(--color-text)]">{stats?.by_status?.investigating || 0}</div>
          <div className="text-xs text-[var(--color-text-muted)] mt-1">Under Investigation</div>
        </div>
        <div className="glass rounded-2xl p-5 animate-slide-up stagger-4">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-xl bg-[var(--color-accent)]/10 flex items-center justify-center">
              <Shield className="w-5 h-5 text-[var(--color-accent)]" />
            </div>
          </div>
          <div className="text-2xl font-bold text-[var(--color-accent)]">{stats?.by_status?.resolved || 0}</div>
          <div className="text-xs text-[var(--color-text-muted)] mt-1">Resolved</div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-1 p-1 rounded-xl bg-white/5 border border-[var(--color-border)]">
          {['', 'open', 'investigating', 'contained', 'resolved'].map((s) => (
            <button
              key={s}
              onClick={() => { setStatusFilter(s); setPage(1); }}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                statusFilter === s
                  ? 'bg-[var(--color-primary)]/20 text-[var(--color-primary)]'
                  : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-white/5'
              }`}
            >
              {s === '' ? 'All' : statusConfig[s]?.label || s}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-1 p-1 rounded-xl bg-white/5 border border-[var(--color-border)]">
          {['', 'Critical', 'High', 'Medium', 'Low'].map((s) => (
            <button
              key={s}
              onClick={() => { setSeverityFilter(s); setPage(1); }}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                severityFilter === s
                  ? 'bg-[var(--color-primary)]/20 text-[var(--color-primary)]'
                  : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-white/5'
              }`}
            >
              {s === '' ? 'All Severity' : `${severityConfig[s]?.icon || ''} ${s}`}
            </button>
          ))}
        </div>
      </div>

      {/* Threats List */}
      <div className="space-y-3">
        {loading ? (
          <div className="glass rounded-2xl flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 text-[var(--color-primary)] animate-spin" />
            <span className="ml-3 text-[var(--color-text-muted)]">Loading threats...</span>
          </div>
        ) : threats.length === 0 ? (
          <div className="glass rounded-2xl text-center py-20">
            <Shield className="w-12 h-12 text-[var(--color-accent)]/30 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-[var(--color-text)] mb-2">No Threats Found</h3>
            <p className="text-sm text-[var(--color-text-muted)]">
              Threats are auto-generated when high-risk malware is classified. Upload and classify files to see threats.
            </p>
          </div>
        ) : (
          threats.map((threat, i) => {
            const sev = severityConfig[threat.severity] || severityConfig['Medium'];
            const stat = statusConfig[threat.status] || statusConfig['open'];
            const isExpanded = expandedId === threat.id;

            return (
              <div key={threat.id} className={`glass rounded-2xl overflow-hidden animate-slide-up stagger-${Math.min(i + 1, 6)}`}>
                {/* Main Row */}
                <div
                  onClick={() => toggleExpand(threat.id)}
                  className="flex items-center gap-4 p-5 cursor-pointer hover:bg-white/3 transition-colors"
                >
                  {/* Severity indicator */}
                  <div className={`w-1.5 h-12 rounded-full ${sev.bg.replace('/10', '/60')}`} />

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-1">
                      <span className="text-xs font-mono text-[var(--color-primary)]">{threat.incident_id}</span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${sev.bg} ${sev.color}`}>
                        {threat.severity}
                      </span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${stat.bg} ${stat.color}`}>
                        {stat.label}
                      </span>
                      {threat.threat_type && (
                        <span className="text-xs text-[var(--color-text-muted)] bg-white/5 px-2 py-0.5 rounded">
                          {threat.threat_type}
                        </span>
                      )}
                    </div>
                    <h3 className="text-sm font-medium text-[var(--color-text)] truncate">{threat.title}</h3>
                  </div>

                  {/* Risk + Time */}
                  <div className="text-right flex-shrink-0">
                    {threat.risk_score && (
                      <div className={`text-lg font-bold ${
                        threat.risk_score >= 80 ? 'risk-critical' :
                        threat.risk_score >= 60 ? 'risk-high' :
                        threat.risk_score >= 40 ? 'risk-medium' : 'risk-low'
                      }`}>
                        {threat.risk_score.toFixed(1)}
                      </div>
                    )}
                    <div className="text-xs text-[var(--color-text-muted)] flex items-center gap-1 justify-end mt-1">
                      <Clock className="w-3 h-3" />
                      {new Date(threat.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                    </div>
                  </div>

                  {/* Expand */}
                  <div className="flex-shrink-0">
                    {isExpanded ? <ChevronUp className="w-5 h-5 text-[var(--color-text-muted)]" /> : <ChevronDown className="w-5 h-5 text-[var(--color-text-muted)]" />}
                  </div>
                </div>

                {/* Expanded Detail */}
                {isExpanded && (
                  <div className="px-5 pb-5 pt-0 border-t border-[var(--color-border)] animate-fade-in">
                    {/* Description */}
                    {threat.description && (
                      <p className="text-sm text-[var(--color-text-muted)] mt-4 mb-4">{threat.description}</p>
                    )}

                    {/* Timeline */}
                    {expandedDetail?.timeline && expandedDetail.timeline.length > 0 && (
                      <div className="mb-4">
                        <h4 className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-3">Timeline</h4>
                        <div className="space-y-2 pl-4 border-l-2 border-[var(--color-border)]">
                          {expandedDetail.timeline.map((event: any, ei: number) => (
                            <div key={ei} className="relative pl-4">
                              <div className="absolute -left-[9px] top-1 w-3 h-3 rounded-full bg-[var(--color-primary)]/30 border-2 border-[var(--color-primary)]" />
                              <div className="text-sm text-[var(--color-text)]">{event.action}</div>
                              <div className="text-xs text-[var(--color-text-muted)]">
                                {new Date(event.timestamp).toLocaleString()} {event.details && `— ${event.details}`}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Status Actions */}
                    <div className="flex items-center gap-2 mt-4">
                      <span className="text-xs text-[var(--color-text-muted)] mr-2">Update Status:</span>
                      {['open', 'investigating', 'contained', 'resolved'].map((s) => {
                        const sc = statusConfig[s];
                        const isCurrent = threat.status === s;
                        return (
                          <button
                            key={s}
                            onClick={(e) => { e.stopPropagation(); handleStatusUpdate(threat.id, s); }}
                            disabled={isCurrent}
                            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                              isCurrent
                                ? `${sc.bg} ${sc.color} ring-1 ring-current`
                                : 'text-[var(--color-text-muted)] bg-white/5 hover:bg-white/10'
                            }`}
                          >
                            {sc.label}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} className="px-3 py-1.5 rounded-lg text-xs text-[var(--color-text-muted)] hover:bg-white/5 disabled:opacity-30 transition-colors">Previous</button>
          {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
            const pn = page <= 3 ? i + 1 : page - 2 + i;
            if (pn > totalPages) return null;
            return (
              <button key={pn} onClick={() => setPage(pn)} className={`w-8 h-8 rounded-lg text-xs font-medium transition-all ${page === pn ? 'bg-[var(--color-primary)]/20 text-[var(--color-primary)]' : 'text-[var(--color-text-muted)] hover:bg-white/5'}`}>{pn}</button>
            );
          })}
          <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages} className="px-3 py-1.5 rounded-lg text-xs text-[var(--color-text-muted)] hover:bg-white/5 disabled:opacity-30 transition-colors">Next</button>
        </div>
      )}
    </div>
  );
}
