'use client';

import { useState, useEffect } from 'react';
import { Bell, BellRing, Check, CheckCheck, Eye, UserCheck, Filter, Loader2, RefreshCw, ShieldAlert, ShieldCheck, Clock } from 'lucide-react';
import api from '@/lib/api';
import type { Alert, AlertListResponse } from '@/types';

const severityStyles: Record<string, { color: string; bg: string; dot: string }> = {
  Critical: { color: 'text-[var(--color-danger)]', bg: 'bg-[var(--color-danger)]/10', dot: 'bg-[var(--color-danger)]' },
  High: { color: 'text-[#ff6b35]', bg: 'bg-[#ff6b35]/10', dot: 'bg-[#ff6b35]' },
  Medium: { color: 'text-[var(--color-warning)]', bg: 'bg-[var(--color-warning)]/10', dot: 'bg-[var(--color-warning)]' },
  Low: { color: 'text-[var(--color-primary)]', bg: 'bg-[var(--color-primary)]/10', dot: 'bg-[var(--color-primary)]' },
};

const statusStyles: Record<string, { color: string; bg: string; icon: any }> = {
  new: { color: 'text-[var(--color-danger)]', bg: 'bg-[var(--color-danger)]/10', icon: BellRing },
  acknowledged: { color: 'text-[var(--color-warning)]', bg: 'bg-[var(--color-warning)]/10', icon: Eye },
  investigating: { color: 'text-[var(--color-primary)]', bg: 'bg-[var(--color-primary)]/10', icon: Filter },
  resolved: { color: 'text-[var(--color-accent)]', bg: 'bg-[var(--color-accent)]/10', icon: CheckCheck },
};

interface AlertStats {
  total_alerts: number;
  by_severity: Record<string, number>;
  by_status: Record<string, number>;
  recent_alerts: Alert[];
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [stats, setStats] = useState<AlertStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [severityFilter, setSeverityFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => { fetchData(); }, [severityFilter, statusFilter, page]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const params: any = { page, page_size: 15 };
      if (severityFilter) params.severity = severityFilter;
      if (statusFilter) params.status = statusFilter;

      const [alertsRes, statsRes] = await Promise.allSettled([
        api.get<AlertListResponse>('/alerts/', { params }),
        api.get<AlertStats>('/alerts/stats'),
      ]);

      if (alertsRes.status === 'fulfilled') {
        setAlerts(alertsRes.value.data.alerts);
        setTotal(alertsRes.value.data.total);
        setUnreadCount(alertsRes.value.data.unread_count);
      }
      if (statsRes.status === 'fulfilled') {
        setStats(statsRes.value.data);
      }
    } catch (err) {
      console.error('Failed to fetch alerts:', err);
    } finally { setLoading(false); }
  };

  const handleAcknowledge = async (id: number) => {
    try {
      await api.put(`/alerts/${id}/acknowledge`);
      fetchData();
    } catch (err) { console.error('Acknowledge failed:', err); }
  };

  const handleResolve = async (id: number) => {
    try {
      await api.put(`/alerts/${id}/resolve`);
      fetchData();
    } catch (err) { console.error('Resolve failed:', err); }
  };

  const totalPages = Math.ceil(total / 15);

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-[var(--color-text)]">Alert Center</h1>
            {unreadCount > 0 && (
              <span className="px-2.5 py-0.5 rounded-full bg-[var(--color-danger)]/20 text-[var(--color-danger)] text-xs font-bold animate-pulse-glow">
                {unreadCount} unread
              </span>
            )}
          </div>
          <p className="text-sm text-[var(--color-text-muted)] mt-1">
            Security alerts, threat notifications, and detection events.
          </p>
        </div>
        <button onClick={fetchData} className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[var(--color-primary)]/10 text-[var(--color-primary)] hover:bg-[var(--color-primary)]/20 transition-colors text-sm font-medium">
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <div className="glass rounded-2xl p-4 animate-slide-up stagger-1">
          <Bell className="w-5 h-5 text-[var(--color-primary)] mb-2" />
          <div className="text-xl font-bold text-[var(--color-text)]">{stats?.total_alerts || 0}</div>
          <div className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider">Total</div>
        </div>
        {['Critical', 'High', 'Medium', 'Low'].map((sev, i) => {
          const style = severityStyles[sev];
          const count = stats?.by_severity?.[sev] || 0;
          return (
            <div key={sev} className={`glass rounded-2xl p-4 animate-slide-up stagger-${i + 2}`}>
              <div className={`w-5 h-5 rounded-full ${style.bg} flex items-center justify-center mb-2`}>
                <div className={`w-2 h-2 rounded-full ${style.dot}`} />
              </div>
              <div className={`text-xl font-bold ${style.color}`}>{count}</div>
              <div className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider">{sev}</div>
            </div>
          );
        })}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-1 p-1 rounded-xl bg-white/5 border border-[var(--color-border)]">
          {['', 'new', 'acknowledged', 'investigating', 'resolved'].map((s) => {
            const label = s === '' ? 'All' : s.charAt(0).toUpperCase() + s.slice(1);
            return (
              <button
                key={s}
                onClick={() => { setStatusFilter(s); setPage(1); }}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  statusFilter === s
                    ? 'bg-[var(--color-primary)]/20 text-[var(--color-primary)]'
                    : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-white/5'
                }`}
              >
                {label}
              </button>
            );
          })}
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
              {s || 'All Severity'}
            </button>
          ))}
        </div>
      </div>

      {/* Alert List */}
      <div className="space-y-2">
        {loading ? (
          <div className="glass rounded-2xl flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 text-[var(--color-primary)] animate-spin" />
            <span className="ml-3 text-[var(--color-text-muted)]">Loading alerts...</span>
          </div>
        ) : alerts.length === 0 ? (
          <div className="glass rounded-2xl text-center py-20">
            <ShieldCheck className="w-12 h-12 text-[var(--color-accent)]/30 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-[var(--color-text)] mb-2">No Alerts</h3>
            <p className="text-sm text-[var(--color-text-muted)]">
              Alerts are auto-generated when malware is classified. All clear for now.
            </p>
          </div>
        ) : (
          alerts.map((alert, i) => {
            const sev = severityStyles[alert.severity] || severityStyles['Medium'];
            const stat = statusStyles[alert.status] || statusStyles['new'];
            const StatusIcon = stat.icon;

            return (
              <div
                key={alert.id}
                className={`glass rounded-xl p-4 flex items-start gap-4 transition-all hover:bg-white/3 animate-slide-up stagger-${Math.min(i + 1, 6)} ${
                  !alert.is_read ? 'border-l-2 border-l-[var(--color-primary)]' : ''
                }`}
              >
                {/* Severity Dot */}
                <div className={`mt-1 flex-shrink-0 w-8 h-8 rounded-lg ${sev.bg} flex items-center justify-center`}>
                  <ShieldAlert className={`w-4 h-4 ${sev.color}`} />
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1 flex-wrap">
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold uppercase ${sev.bg} ${sev.color}`}>
                      {alert.severity}
                    </span>
                    <span className={`flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-bold uppercase ${stat.bg} ${stat.color}`}>
                      <StatusIcon className="w-3 h-3" />
                      {alert.status}
                    </span>
                    {alert.source && (
                      <span className="text-[10px] text-[var(--color-text-muted)] bg-white/5 px-1.5 py-0.5 rounded">
                        {alert.source}
                      </span>
                    )}
                    {!alert.is_read && (
                      <span className="w-2 h-2 rounded-full bg-[var(--color-primary)] animate-pulse-glow" />
                    )}
                  </div>
                  <h4 className="text-sm font-medium text-[var(--color-text)] mb-1 truncate">{alert.title}</h4>
                  {alert.description && (
                    <p className="text-xs text-[var(--color-text-muted)] line-clamp-2">{alert.description}</p>
                  )}
                  <div className="flex items-center gap-3 mt-2 text-xs text-[var(--color-text-muted)]">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {new Date(alert.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-1 flex-shrink-0">
                  {alert.status === 'new' && (
                    <button
                      onClick={() => handleAcknowledge(alert.id)}
                      className="p-2 rounded-lg hover:bg-[var(--color-warning)]/10 text-[var(--color-text-muted)] hover:text-[var(--color-warning)] transition-colors"
                      title="Acknowledge"
                    >
                      <Check className="w-4 h-4" />
                    </button>
                  )}
                  {alert.status !== 'resolved' && (
                    <button
                      onClick={() => handleResolve(alert.id)}
                      className="p-2 rounded-lg hover:bg-[var(--color-accent)]/10 text-[var(--color-text-muted)] hover:text-[var(--color-accent)] transition-colors"
                      title="Resolve"
                    >
                      <CheckCheck className="w-4 h-4" />
                    </button>
                  )}
                </div>
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
