'use client';

import { useState, useEffect } from 'react';
import {
  BarChart3, TrendingUp, Shield, AlertTriangle, Activity,
  Target, Eye, RefreshCw, Loader2, ArrowUp, ArrowDown,
} from 'lucide-react';
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
  Legend,
} from 'recharts';
import api from '@/lib/api';
import type {
  OverviewStats, MalwareDistribution, ThreatTrend, RiskDistribution,
} from '@/types';

// ─── Color Palette ──────────────────────────────────────────────────

const CHART_COLORS = {
  primary: '#6366f1',
  accent: '#10b981',
  warning: '#f59e0b',
  danger: '#ef4444',
  purple: '#a855f7',
  cyan: '#06b6d4',
  pink: '#ec4899',
};

const PIE_COLORS = ['#10b981', '#f59e0b', '#ef4444', '#a855f7', '#6366f1', '#06b6d4', '#ec4899'];

const RISK_GRADIENT = [
  { name: 'Clean', color: '#10b981' },
  { name: 'Low', color: '#6366f1' },
  { name: 'Medium', color: '#f59e0b' },
  { name: 'High', color: '#f97316' },
  { name: 'Critical', color: '#ef4444' },
];

// ─── Custom Tooltip ─────────────────────────────────────────────────

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="glass rounded-xl px-4 py-3 border border-[var(--color-border)] shadow-lg">
      <p className="text-xs text-[var(--color-text-muted)] mb-1">{label}</p>
      {payload.map((p: any, i: number) => (
        <p key={i} className="text-sm font-semibold" style={{ color: p.color }}>
          {p.name}: {typeof p.value === 'number' ? p.value.toLocaleString() : p.value}
        </p>
      ))}
    </div>
  );
};

interface TrendsResponse { trends: ThreatTrend[]; period: string; }

export default function AnalyticsPage() {
  const [overview, setOverview] = useState<OverviewStats | null>(null);
  const [distribution, setDistribution] = useState<MalwareDistribution | null>(null);
  const [trends, setTrends] = useState<ThreatTrend[]>([]);
  const [riskDist, setRiskDist] = useState<RiskDistribution | null>(null);
  const [trendPeriod, setTrendPeriod] = useState('30d');
  const [loading, setLoading] = useState(true);

  useEffect(() => { fetchAll(); }, []);
  useEffect(() => { fetchTrends(); }, [trendPeriod]);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [ovRes, distRes, trendRes, riskRes] = await Promise.allSettled([
        api.get<OverviewStats>('/analytics/overview'),
        api.get<MalwareDistribution>('/analytics/malware-distribution'),
        api.get<TrendsResponse>('/analytics/trends', { params: { period: trendPeriod } }),
        api.get<RiskDistribution>('/analytics/risk-distribution'),
      ]);

      if (ovRes.status === 'fulfilled') setOverview(ovRes.value.data);
      if (distRes.status === 'fulfilled') setDistribution(distRes.value.data);
      if (trendRes.status === 'fulfilled') setTrends(trendRes.value.data.trends);
      if (riskRes.status === 'fulfilled') setRiskDist(riskRes.value.data);
    } catch (err) {
      console.error('Analytics fetch failed:', err);
    } finally { setLoading(false); }
  };

  const fetchTrends = async () => {
    try {
      const res = await api.get<TrendsResponse>('/analytics/trends', { params: { period: trendPeriod } });
      setTrends(res.data.trends);
    } catch {}
  };

  // ─── Derived Data ─────────────────────────────────────────────────

  const pieData = distribution
    ? Object.entries(distribution.distribution).map(([name, value]) => ({ name, value }))
    : [];

  const riskBarData = riskDist
    ? RISK_GRADIENT.map(r => ({
        name: r.name,
        count: (riskDist as any)[r.name.toLowerCase()] || 0,
        color: r.color,
      }))
    : [];

  const totalRisk = riskBarData.reduce((a, d) => a + d.count, 0);

  // Radar data from overview stats
  const radarData = overview ? [
    { metric: 'Scan Volume', value: Math.min(overview.total_scans, 100), fullMark: 100 },
    { metric: 'Threat Rate', value: overview.threats_detected > 0 ? Math.min((overview.threats_detected / Math.max(overview.total_scans, 1)) * 100, 100) : 0, fullMark: 100 },
    { metric: 'Avg Risk', value: overview.average_risk_score, fullMark: 100 },
    { metric: 'Active Alerts', value: Math.min(overview.active_alerts * 10, 100), fullMark: 100 },
    { metric: 'Critical', value: Math.min(overview.critical_alerts * 20, 100), fullMark: 100 },
    { metric: 'Today Scans', value: Math.min(overview.scans_today * 10, 100), fullMark: 100 },
  ] : [];

  if (loading) {
    return (
      <div className="flex items-center justify-center py-32">
        <Loader2 className="w-10 h-10 text-[var(--color-primary)] animate-spin" />
        <span className="ml-4 text-lg text-[var(--color-text-muted)]">Loading analytics...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--color-text)]">Analytics Dashboard</h1>
          <p className="text-sm text-[var(--color-text-muted)] mt-1">
            Real-time security analytics, detection trends, and threat intelligence overview.
          </p>
        </div>
        <button
          onClick={fetchAll}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[var(--color-primary)]/10 text-[var(--color-primary)] hover:bg-[var(--color-primary)]/20 transition-colors text-sm font-medium"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Overview KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {[
          { label: 'Total Scans', value: overview?.total_scans || 0, icon: Eye, color: CHART_COLORS.primary, change: overview?.scans_today || 0, changeLabel: 'today' },
          { label: 'Threats Found', value: overview?.threats_detected || 0, icon: Shield, color: CHART_COLORS.danger, change: null, changeLabel: '' },
          { label: 'Avg Risk', value: `${overview?.average_risk_score || 0}`, icon: TrendingUp, color: CHART_COLORS.warning, change: null, changeLabel: '' },
          { label: 'Active Alerts', value: overview?.active_alerts || 0, icon: AlertTriangle, color: CHART_COLORS.purple, change: null, changeLabel: '' },
          { label: 'Scans Today', value: overview?.scans_today || 0, icon: Activity, color: CHART_COLORS.cyan, change: null, changeLabel: '' },
          { label: 'Critical', value: overview?.critical_alerts || 0, icon: Target, color: CHART_COLORS.danger, change: null, changeLabel: '' },
        ].map((kpi, i) => (
          <div key={i} className={`glass rounded-2xl p-4 animate-slide-up stagger-${Math.min(i + 1, 6)}`}>
            <div className="flex items-center justify-between mb-2">
              <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: `${kpi.color}15` }}>
                <kpi.icon className="w-4 h-4" style={{ color: kpi.color }} />
              </div>
              {kpi.change !== null && kpi.change > 0 && (
                <span className="flex items-center gap-0.5 text-[10px] text-[var(--color-accent)] font-medium">
                  <ArrowUp className="w-3 h-3" />{kpi.change} {kpi.changeLabel}
                </span>
              )}
            </div>
            <div className="text-xl font-bold text-[var(--color-text)]">{kpi.value}</div>
            <div className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider mt-0.5">{kpi.label}</div>
          </div>
        ))}
      </div>

      {/* Charts Row 1: Trends + Risk Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Threat Trends (2/3 width) */}
        <div className="lg:col-span-2 glass rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-[var(--color-text)]">Detection Trends</h3>
            <div className="flex items-center gap-1 p-0.5 rounded-lg bg-white/5">
              {['7d', '30d', '90d'].map((p) => (
                <button
                  key={p}
                  onClick={() => setTrendPeriod(p)}
                  className={`px-2.5 py-1 rounded-md text-[10px] font-medium transition-all ${
                    trendPeriod === p
                      ? 'bg-[var(--color-primary)]/20 text-[var(--color-primary)]'
                      : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]'
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>
          {trends.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <AreaChart data={trends} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="scanGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={CHART_COLORS.primary} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={CHART_COLORS.primary} stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="riskGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={CHART_COLORS.danger} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={CHART_COLORS.danger} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis
                  dataKey="date" tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.4)' }}
                  tickFormatter={(v) => { const d = new Date(v); return `${d.getMonth()+1}/${d.getDate()}`; }}
                  axisLine={false} tickLine={false}
                />
                <YAxis tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.4)' }} axisLine={false} tickLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="count" name="Scans" stroke={CHART_COLORS.primary} fill="url(#scanGrad)" strokeWidth={2} />
                <Area type="monotone" dataKey="risk_avg" name="Avg Risk" stroke={CHART_COLORS.danger} fill="url(#riskGrad)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-[280px] text-sm text-[var(--color-text-muted)]">
              No trend data yet. Upload and analyze files to see trends.
            </div>
          )}
        </div>

        {/* Risk Distribution (1/3 width) */}
        <div className="glass rounded-2xl p-6">
          <h3 className="text-sm font-semibold text-[var(--color-text)] mb-4">Risk Distribution</h3>
          {totalRisk > 0 ? (
            <>
              <div className="space-y-3 mb-4">
                {riskBarData.map((d) => (
                  <div key={d.name} className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-[var(--color-text-muted)]">{d.name}</span>
                      <span className="font-mono font-bold" style={{ color: d.color }}>
                        {d.count}
                      </span>
                    </div>
                    <div className="h-2 rounded-full bg-white/5 overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-700"
                        style={{
                          width: `${(d.count / totalRisk) * 100}%`,
                          backgroundColor: d.color,
                          minWidth: d.count > 0 ? '8px' : '0',
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
              <div className="text-center pt-2 border-t border-[var(--color-border)]">
                <div className="text-2xl font-bold text-[var(--color-text)]">{totalRisk}</div>
                <div className="text-[10px] text-[var(--color-text-muted)] uppercase">Total Analyzed</div>
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-48 text-sm text-[var(--color-text-muted)]">
              No risk data yet.
            </div>
          )}
        </div>
      </div>

      {/* Charts Row 2: Pie + Radar */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Malware Distribution Pie */}
        <div className="glass rounded-2xl p-6">
          <h3 className="text-sm font-semibold text-[var(--color-text)] mb-4">Malware Class Distribution</h3>
          {pieData.length > 0 ? (
            <div className="flex items-center gap-6">
              <ResponsiveContainer width="55%" height={240}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={90}
                    paddingAngle={3}
                    dataKey="value"
                    strokeWidth={0}
                  >
                    {pieData.map((_, i) => (
                      <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                </PieChart>
              </ResponsiveContainer>
              <div className="flex-1 space-y-2">
                {pieData.sort((a, b) => b.value - a.value).map((d, i) => (
                  <div key={d.name} className="flex items-center gap-2">
                    <div className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: PIE_COLORS[i % PIE_COLORS.length] }} />
                    <span className="text-xs text-[var(--color-text-muted)] flex-1 truncate">{d.name}</span>
                    <span className="text-xs font-bold text-[var(--color-text)]">{d.value}</span>
                    <span className="text-[10px] text-[var(--color-text-muted)]">
                      ({distribution ? ((d.value / distribution.total) * 100).toFixed(0) : 0}%)
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-[240px] text-sm text-[var(--color-text-muted)]">
              No classification data yet.
            </div>
          )}
        </div>

        {/* Security Radar */}
        <div className="glass rounded-2xl p-6">
          <h3 className="text-sm font-semibold text-[var(--color-text)] mb-4">Security Posture Radar</h3>
          {radarData.length > 0 && overview && overview.total_scans > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <RadarChart data={radarData} cx="50%" cy="50%" outerRadius="70%">
                <PolarGrid stroke="rgba(255,255,255,0.08)" />
                <PolarAngleAxis dataKey="metric" tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.5)' }} />
                <PolarRadiusAxis tick={false} axisLine={false} domain={[0, 100]} />
                <Radar
                  name="Current"
                  dataKey="value"
                  stroke={CHART_COLORS.primary}
                  fill={CHART_COLORS.primary}
                  fillOpacity={0.2}
                  strokeWidth={2}
                />
              </RadarChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-[240px] text-sm text-[var(--color-text-muted)]">
              Upload files to populate security radar.
            </div>
          )}
        </div>
      </div>

      {/* Charts Row 3: Bar chart of scans by risk level */}
      <div className="glass rounded-2xl p-6">
        <h3 className="text-sm font-semibold text-[var(--color-text)] mb-4">Scans by Risk Level</h3>
        {totalRisk > 0 ? (
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={riskBarData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: 'rgba(255,255,255,0.5)' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.4)' }} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="count" name="Files" radius={[6, 6, 0, 0]}>
                {riskBarData.map((d, i) => (
                  <Cell key={i} fill={d.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex items-center justify-center h-[200px] text-sm text-[var(--color-text-muted)]">
            No data yet.
          </div>
        )}
      </div>
    </div>
  );
}
