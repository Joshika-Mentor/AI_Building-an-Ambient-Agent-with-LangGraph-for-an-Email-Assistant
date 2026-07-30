'use client';

import { useEffect, useState } from 'react';
import {
  Shield, Scan, AlertTriangle, Bell, TrendingUp, Activity,
  Target, ArrowRight, ArrowUp, ArrowDown, Clock, Eye,
  FileText, Loader2, RefreshCw, Upload, Zap,
} from 'lucide-react';
import {
  AreaChart, Area, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import Link from 'next/link';
import api from '@/lib/api';
import type { OverviewStats, FileAnalysis, ThreatTrend } from '@/types';

const RISK_COLORS = ['#10b981', '#6366f1', '#f59e0b', '#f97316', '#ef4444'];
const CLASS_COLORS: Record<string, string> = {
  Clean: '#10b981', Adware: '#f59e0b', Trojan: '#ef4444', Ransomware: '#ef4444',
  Worm: '#a855f7', Spyware: '#f59e0b', Backdoor: '#ec4899',
};

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="glass rounded-xl px-3 py-2 border border-[var(--color-border)] shadow-lg">
      <p className="text-[10px] text-[var(--color-text-muted)] mb-0.5">{label}</p>
      {payload.map((p: any, i: number) => (
        <p key={i} className="text-xs font-semibold" style={{ color: p.color }}>{p.name}: {p.value}</p>
      ))}
    </div>
  );
};

interface RecentFile {
  id: number; original_name: string; risk_score: number | null;
  risk_level: string | null; status: string; upload_date: string;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<OverviewStats | null>(null);
  const [recentFiles, setRecentFiles] = useState<RecentFile[]>([]);
  const [trends, setTrends] = useState<ThreatTrend[]>([]);
  const [riskDist, setRiskDist] = useState<any>(null);
  const [malwareDist, setMalwareDist] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { fetchDashboard(); }, []);

  const fetchDashboard = async () => {
    setLoading(true);
    try {
      const [ovRes, filesRes, trendRes, riskRes, malRes] = await Promise.allSettled([
        api.get('/analytics/overview'),
        api.get('/files/', { params: { page: 1, page_size: 5 } }),
        api.get('/analytics/trends', { params: { period: '7d' } }),
        api.get('/analytics/risk-distribution'),
        api.get('/analytics/malware-distribution'),
      ]);

      if (ovRes.status === 'fulfilled') setStats(ovRes.value.data);
      if (filesRes.status === 'fulfilled') setRecentFiles(filesRes.value.data.files || []);
      if (trendRes.status === 'fulfilled') setTrends(trendRes.value.data.trends || []);
      if (riskRes.status === 'fulfilled') setRiskDist(riskRes.value.data);
      if (malRes.status === 'fulfilled') setMalwareDist(malRes.value.data);
    } catch {}
    finally { setLoading(false); }
  };

  const riskPieData = riskDist ? [
    { name: 'Clean', value: riskDist.clean || 0, color: '#10b981' },
    { name: 'Low', value: riskDist.low || 0, color: '#6366f1' },
    { name: 'Medium', value: riskDist.medium || 0, color: '#f59e0b' },
    { name: 'High', value: riskDist.high || 0, color: '#f97316' },
    { name: 'Critical', value: riskDist.critical || 0, color: '#ef4444' },
  ].filter(d => d.value > 0) : [];

  const riskColor = (level: string | null) => {
    switch (level) {
      case 'Critical': return 'text-[var(--color-danger)]';
      case 'High': return 'text-[#f97316]';
      case 'Medium': return 'text-[var(--color-warning)]';
      case 'Low': return 'text-[var(--color-primary)]';
      default: return 'text-[var(--color-accent)]';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-32">
        <Loader2 className="w-10 h-10 text-[var(--color-primary)] animate-spin" />
        <span className="ml-4 text-lg text-[var(--color-text-muted)]">Loading dashboard...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--color-text)]">Dashboard</h1>
          <p className="text-sm text-[var(--color-text-muted)] mt-1">
            Real-time threat intelligence and security operations overview.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link
            href="/dashboard/upload"
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-accent)] text-white text-sm font-medium hover:opacity-90 transition-opacity"
          >
            <Upload className="w-4 h-4" />
            Upload File
          </Link>
          <button
            onClick={fetchDashboard}
            className="flex items-center gap-2 px-3 py-2 rounded-xl bg-white/5 text-[var(--color-text-muted)] hover:bg-white/10 transition-colors text-sm"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {[
          { label: 'Total Scans', value: stats?.total_scans || 0, icon: Scan, color: '#6366f1', sub: stats?.scans_today ? `+${stats.scans_today} today` : null },
          { label: 'Threats Found', value: stats?.threats_detected || 0, icon: AlertTriangle, color: '#ef4444', sub: null },
          { label: 'Avg Risk', value: stats?.average_risk_score || 0, icon: TrendingUp, color: '#f59e0b', sub: null },
          { label: 'Active Alerts', value: stats?.active_alerts || 0, icon: Bell, color: '#a855f7', sub: null },
          { label: 'Today', value: stats?.scans_today || 0, icon: Activity, color: '#06b6d4', sub: null },
          { label: 'Critical', value: stats?.critical_alerts || 0, icon: Target, color: '#ef4444', sub: null },
        ].map((kpi, i) => (
          <div key={i} className={`glass rounded-2xl p-4 animate-slide-up stagger-${Math.min(i + 1, 6)}`}>
            <div className="flex items-center justify-between mb-2">
              <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: `${kpi.color}15` }}>
                <kpi.icon className="w-4 h-4" style={{ color: kpi.color }} />
              </div>
              {kpi.sub && (
                <span className="flex items-center gap-0.5 text-[10px] text-[var(--color-accent)] font-medium">
                  <ArrowUp className="w-3 h-3" />{kpi.sub}
                </span>
              )}
            </div>
            <div className="text-xl font-bold text-[var(--color-text)]">{kpi.value}</div>
            <div className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider mt-0.5">{kpi.label}</div>
          </div>
        ))}
      </div>

      {/* Main Content: Trend Chart + Risk Pie + Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Trend Chart (8 cols) */}
        <div className="lg:col-span-8 glass rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-[var(--color-text)]">7-Day Detection Trend</h3>
            <Link href="/dashboard/analytics" className="text-xs text-[var(--color-primary)] hover:underline flex items-center gap-1">
              Full Analytics <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
          {trends.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={trends} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="dashGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="date" tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.4)' }}
                  tickFormatter={(v) => { const d = new Date(v); return `${d.getMonth()+1}/${d.getDate()}`; }}
                  axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.4)' }} axisLine={false} tickLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="count" name="Scans" stroke="#6366f1" fill="url(#dashGrad)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-[200px] text-sm text-[var(--color-text-muted)]">
              Upload files to see trend data.
            </div>
          )}
        </div>

        {/* Right Side: Risk Pie + Quick Actions (4 cols) */}
        <div className="lg:col-span-4 space-y-4">
          {/* Risk Distribution Donut */}
          <div className="glass rounded-2xl p-5">
            <h3 className="text-sm font-semibold text-[var(--color-text)] mb-3">Risk Breakdown</h3>
            {riskPieData.length > 0 ? (
              <div className="flex items-center gap-3">
                <ResponsiveContainer width={110} height={110}>
                  <PieChart>
                    <Pie data={riskPieData} cx="50%" cy="50%" innerRadius={30} outerRadius={50} paddingAngle={3} dataKey="value" strokeWidth={0}>
                      {riskPieData.map((d, i) => <Cell key={i} fill={d.color} />)}
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
                <div className="flex-1 space-y-1.5">
                  {riskPieData.map(d => (
                    <div key={d.name} className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full" style={{ backgroundColor: d.color }} />
                      <span className="text-[10px] text-[var(--color-text-muted)] flex-1">{d.name}</span>
                      <span className="text-[10px] font-bold text-[var(--color-text)]">{d.value}</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-xs text-[var(--color-text-muted)] text-center py-6">No data yet</div>
            )}
          </div>

          {/* Quick Actions */}
          <div className="glass rounded-2xl p-5">
            <h3 className="text-sm font-semibold text-[var(--color-text)] mb-3">Quick Actions</h3>
            <div className="space-y-2">
              {[
                { href: '/dashboard/upload', label: 'Upload & Scan', icon: Upload, color: '#6366f1' },
                { href: '/dashboard/threats', label: 'View Threats', icon: AlertTriangle, color: '#ef4444' },
                { href: '/dashboard/reports', label: 'Generate Report', icon: FileText, color: '#10b981' },
              ].map((action) => (
                <Link
                  key={action.href}
                  href={action.href}
                  className="flex items-center gap-3 px-3 py-2.5 rounded-xl bg-white/3 hover:bg-white/6 transition-colors group"
                >
                  <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ background: `${action.color}15` }}>
                    <action.icon className="w-3.5 h-3.5" style={{ color: action.color }} />
                  </div>
                  <span className="text-xs text-[var(--color-text-muted)] group-hover:text-[var(--color-text)] transition-colors flex-1">{action.label}</span>
                  <ArrowRight className="w-3 h-3 text-[var(--color-text-muted)] opacity-0 group-hover:opacity-100 transition-opacity" />
                </Link>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Recent Files */}
      <div className="glass rounded-2xl overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--color-border)]">
          <h3 className="text-sm font-semibold text-[var(--color-text)]">Recent Scans</h3>
          <Link href="/dashboard/classifications" className="text-xs text-[var(--color-primary)] hover:underline flex items-center gap-1">
            View All <ArrowRight className="w-3 h-3" />
          </Link>
        </div>
        {recentFiles.length > 0 ? (
          <>
            <div className="grid grid-cols-[1fr_80px_80px_100px] gap-4 px-6 py-2 bg-white/2">
              <div className="text-[10px] font-semibold text-[var(--color-text-muted)] uppercase">File</div>
              <div className="text-[10px] font-semibold text-[var(--color-text-muted)] uppercase">Risk</div>
              <div className="text-[10px] font-semibold text-[var(--color-text-muted)] uppercase">Status</div>
              <div className="text-[10px] font-semibold text-[var(--color-text-muted)] uppercase">Date</div>
            </div>
            {recentFiles.map((file, i) => (
              <div key={file.id} className={`grid grid-cols-[1fr_80px_80px_100px] gap-4 px-6 py-3 border-b border-[var(--color-border)] hover:bg-white/2 transition-colors animate-slide-up stagger-${Math.min(i + 1, 5)}`}>
                <div className="text-sm text-[var(--color-text)] truncate">{file.original_name}</div>
                <div>
                  {file.risk_score !== null ? (
                    <span className={`text-sm font-bold ${riskColor(file.risk_level)}`}>{file.risk_score.toFixed(0)}</span>
                  ) : (
                    <span className="text-xs text-[var(--color-text-muted)]">—</span>
                  )}
                </div>
                <div>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold uppercase ${
                    file.status === 'completed' ? 'bg-[var(--color-accent)]/10 text-[var(--color-accent)]' :
                    file.status === 'failed' ? 'bg-[var(--color-danger)]/10 text-[var(--color-danger)]' :
                    'bg-[var(--color-warning)]/10 text-[var(--color-warning)]'
                  }`}>
                    {file.status}
                  </span>
                </div>
                <div className="text-xs text-[var(--color-text-muted)]">
                  {new Date(file.upload_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                </div>
              </div>
            ))}
          </>
        ) : (
          <div className="text-center py-12">
            <Scan className="w-10 h-10 text-[var(--color-text-muted)]/30 mx-auto mb-3" />
            <p className="text-sm text-[var(--color-text-muted)]">No scans yet. Upload a file to get started.</p>
          </div>
        )}
      </div>
    </div>
  );
}
