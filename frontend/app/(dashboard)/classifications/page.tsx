'use client';

import { useState, useEffect } from 'react';
import { GitBranch, Search, Filter, ChevronDown, ChevronUp, Brain, AlertTriangle, Shield, ArrowUpRight, RefreshCw, Loader2 } from 'lucide-react';
import api from '@/lib/api';
import type { ClassificationResult } from '@/types';

const classColors: Record<string, { bg: string; text: string; glow: string }> = {
  Clean: { bg: 'bg-[var(--color-accent)]/10', text: 'text-[var(--color-accent)]', glow: 'glow-green' },
  Adware: { bg: 'bg-[var(--color-warning)]/10', text: 'text-[var(--color-warning)]', glow: '' },
  Trojan: { bg: 'bg-[var(--color-danger)]/10', text: 'text-[var(--color-danger)]', glow: 'glow-red' },
  Ransomware: { bg: 'bg-[var(--color-danger)]/10', text: 'text-[var(--color-danger)]', glow: 'glow-red' },
  Worm: { bg: 'bg-[var(--color-purple)]/10', text: 'text-[var(--color-purple)]', glow: '' },
  Spyware: { bg: 'bg-[var(--color-warning)]/10', text: 'text-[var(--color-warning)]', glow: '' },
  Backdoor: { bg: 'bg-[var(--color-danger)]/10', text: 'text-[var(--color-danger)]', glow: 'glow-red' },
};

const MALWARE_CLASSES = ['All', 'Clean', 'Adware', 'Trojan', 'Ransomware', 'Worm', 'Spyware', 'Backdoor'];

interface ClassificationWithFile extends ClassificationResult {
  file_name?: string;
}

interface ClassificationListResponse {
  classifications: ClassificationResult[];
  total: number;
  page: number;
  page_size: number;
}

interface ClassificationStats {
  total_classifications: number;
  malware_distribution: Record<string, number>;
  avg_confidence: number;
  avg_risk_score: number;
  recent_classifications: ClassificationResult[];
}

export default function ClassificationsPage() {
  const [classifications, setClassifications] = useState<ClassificationResult[]>([]);
  const [stats, setStats] = useState<ClassificationStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('All');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchData();
  }, [filter, page]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const params: any = { page, page_size: 15 };
      if (filter !== 'All') params.malware_class = filter;

      const [classRes, statsRes] = await Promise.allSettled([
        api.get<ClassificationListResponse>('/classifications/', { params }),
        api.get<ClassificationStats>('/classifications/stats'),
      ]);

      if (classRes.status === 'fulfilled') {
        setClassifications(classRes.value.data.classifications);
        setTotal(classRes.value.data.total);
      }
      if (statsRes.status === 'fulfilled') {
        setStats(statsRes.value.data);
      }
    } catch (err) {
      console.error('Failed to fetch classifications:', err);
    } finally {
      setLoading(false);
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.85) return 'bg-[var(--color-accent)]';
    if (confidence >= 0.65) return 'bg-[var(--color-primary)]';
    if (confidence >= 0.45) return 'bg-[var(--color-warning)]';
    return 'bg-[var(--color-danger)]';
  };

  const totalPages = Math.ceil(total / 15);
  const filtered = searchQuery
    ? classifications.filter(c =>
        c.malware_class.toLowerCase().includes(searchQuery.toLowerCase()) ||
        c.malware_family?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        c.incident_id?.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : classifications;

  // Distribution for chart
  const distributionData = stats?.malware_distribution || {};
  const maxDistribution = Math.max(...Object.values(distributionData), 1);

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--color-text)]">Malware Classifications</h1>
          <p className="text-sm text-[var(--color-text-muted)] mt-1">
            ML-powered classification results with confidence scoring and family identification.
          </p>
        </div>
        <button
          onClick={fetchData}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[var(--color-primary)]/10 text-[var(--color-primary)] hover:bg-[var(--color-primary)]/20 transition-colors text-sm font-medium"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { label: 'Total Classifications', value: stats?.total_classifications || 0, icon: GitBranch, color: 'var(--color-primary)' },
          { label: 'Avg Confidence', value: `${((stats?.avg_confidence || 0) * 100).toFixed(1)}%`, icon: Brain, color: 'var(--color-accent)' },
          { label: 'Avg Risk Score', value: (stats?.avg_risk_score || 0).toFixed(1), icon: AlertTriangle, color: 'var(--color-warning)' },
          { label: 'Threats Detected', value: Object.entries(distributionData).filter(([k]) => k !== 'Clean').reduce((a, [, v]) => a + v, 0), icon: Shield, color: 'var(--color-danger)' },
        ].map((stat, i) => (
          <div key={i} className={`glass rounded-2xl p-5 animate-slide-up stagger-${i + 1}`}>
            <div className="flex items-center justify-between mb-3">
              <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: `${stat.color}15` }}>
                <stat.icon className="w-5 h-5" style={{ color: stat.color }} />
              </div>
            </div>
            <div className="text-2xl font-bold text-[var(--color-text)]">{stat.value}</div>
            <div className="text-xs text-[var(--color-text-muted)] mt-1">{stat.label}</div>
          </div>
        ))}
      </div>

      {/* Distribution Chart */}
      {Object.keys(distributionData).length > 0 && (
        <div className="glass rounded-2xl p-6">
          <h3 className="text-sm font-semibold text-[var(--color-text)] mb-4">Malware Distribution</h3>
          <div className="space-y-3">
            {Object.entries(distributionData).sort(([,a], [,b]) => b - a).map(([cls, count]) => {
              const colors = classColors[cls] || { bg: 'bg-white/10', text: 'text-white', glow: '' };
              return (
                <div key={cls} className="flex items-center gap-4">
                  <div className="w-24 text-sm text-[var(--color-text-muted)]">{cls}</div>
                  <div className="flex-1 h-7 rounded-lg bg-white/5 overflow-hidden relative">
                    <div
                      className={`h-full rounded-lg transition-all duration-700 ${colors.bg.replace('/10', '/30')}`}
                      style={{ width: `${(count / maxDistribution) * 100}%`, minWidth: count > 0 ? '24px' : '0' }}
                    />
                    <div className="absolute inset-0 flex items-center px-3">
                      <span className={`text-xs font-mono font-bold ${colors.text}`}>{count}</span>
                    </div>
                  </div>
                  <div className="w-14 text-right text-xs text-[var(--color-text-muted)]">
                    {stats?.total_classifications ? ((count / stats.total_classifications) * 100).toFixed(1) : 0}%
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Filters & Search */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-muted)]" />
          <input
            type="text"
            placeholder="Search by class, family, or incident..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 rounded-xl bg-white/5 border border-[var(--color-border)] text-sm text-[var(--color-text)] placeholder:text-[var(--color-text-muted)]/50 focus:outline-none focus:border-[var(--color-primary)]/40 transition-colors"
          />
        </div>
        <div className="flex items-center gap-1 p-1 rounded-xl bg-white/5 border border-[var(--color-border)]">
          {MALWARE_CLASSES.map((cls) => (
            <button
              key={cls}
              onClick={() => { setFilter(cls); setPage(1); }}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                filter === cls
                  ? 'bg-[var(--color-primary)]/20 text-[var(--color-primary)]'
                  : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-white/5'
              }`}
            >
              {cls}
            </button>
          ))}
        </div>
      </div>

      {/* Classifications Table */}
      <div className="glass rounded-2xl overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 text-[var(--color-primary)] animate-spin" />
            <span className="ml-3 text-[var(--color-text-muted)]">Loading classifications...</span>
          </div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-20">
            <GitBranch className="w-12 h-12 text-[var(--color-primary)]/30 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-[var(--color-text)] mb-2">No Classifications Found</h3>
            <p className="text-sm text-[var(--color-text-muted)]">
              Upload and analyze files, then run ML classification to see results here.
            </p>
          </div>
        ) : (
          <>
            {/* Table Header */}
            <div className="grid grid-cols-[1fr_140px_140px_120px_100px_120px_40px] gap-4 px-6 py-3 border-b border-[var(--color-border)] bg-white/3">
              <div className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">Classification</div>
              <div className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">Family</div>
              <div className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">Confidence</div>
              <div className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">Risk</div>
              <div className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">Model</div>
              <div className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">Date</div>
              <div></div>
            </div>

            {/* Table Rows */}
            {filtered.map((c, i) => {
              const colors = classColors[c.malware_class] || { bg: 'bg-white/10', text: 'text-white', glow: '' };
              const isExpanded = expandedId === c.id;

              return (
                <div key={c.id} className={`animate-slide-up stagger-${Math.min(i + 1, 6)}`}>
                  <div
                    onClick={() => setExpandedId(isExpanded ? null : c.id)}
                    className="grid grid-cols-[1fr_140px_140px_120px_100px_120px_40px] gap-4 px-6 py-4 border-b border-[var(--color-border)] hover:bg-white/3 transition-colors cursor-pointer"
                  >
                    {/* Class */}
                    <div className="flex items-center gap-3">
                      <span className={`px-2.5 py-1 rounded-lg text-xs font-bold ${colors.bg} ${colors.text}`}>
                        {c.malware_class}
                      </span>
                      {c.incident_id && (
                        <span className="text-xs text-[var(--color-primary)] font-mono">{c.incident_id}</span>
                      )}
                    </div>

                    {/* Family */}
                    <div className="flex items-center">
                      <span className="text-sm text-[var(--color-text)]">{c.malware_family || '—'}</span>
                    </div>

                    {/* Confidence Bar */}
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-2 rounded-full bg-white/10 overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-500 ${getConfidenceColor(c.confidence_score)}`}
                          style={{ width: `${c.confidence_score * 100}%` }}
                        />
                      </div>
                      <span className="text-xs font-mono text-[var(--color-text-muted)] w-10 text-right">
                        {(c.confidence_score * 100).toFixed(1)}%
                      </span>
                    </div>

                    {/* Risk Score */}
                    <div className="flex items-center">
                      <span className={`text-sm font-bold ${
                        c.risk_score >= 80 ? 'risk-critical' :
                        c.risk_score >= 60 ? 'risk-high' :
                        c.risk_score >= 40 ? 'risk-medium' :
                        c.risk_score >= 20 ? 'risk-low' : 'risk-clean'
                      }`}>
                        {c.risk_score.toFixed(1)}
                      </span>
                    </div>

                    {/* Model */}
                    <div className="flex items-center">
                      <span className="text-xs text-[var(--color-text-muted)] font-mono truncate">{c.model_version || '—'}</span>
                    </div>

                    {/* Date */}
                    <div className="flex items-center">
                      <span className="text-xs text-[var(--color-text-muted)]">
                        {new Date(c.classified_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>

                    {/* Expand */}
                    <div className="flex items-center justify-center">
                      {isExpanded ? (
                        <ChevronUp className="w-4 h-4 text-[var(--color-text-muted)]" />
                      ) : (
                        <ChevronDown className="w-4 h-4 text-[var(--color-text-muted)]" />
                      )}
                    </div>
                  </div>

                  {/* Expanded Details */}
                  {isExpanded && c.class_probabilities && (
                    <div className="px-6 py-4 bg-white/2 border-b border-[var(--color-border)] animate-fade-in">
                      <h4 className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-3">
                        Class Probability Distribution
                      </h4>
                      <div className="grid grid-cols-7 gap-2">
                        {Object.entries(c.class_probabilities)
                          .sort(([, a], [, b]) => b - a)
                          .map(([cls, prob]) => {
                            const clsColors = classColors[cls] || { bg: 'bg-white/10', text: 'text-white', glow: '' };
                            return (
                              <div key={cls} className="text-center">
                                <div className="h-20 flex items-end justify-center mb-1">
                                  <div
                                    className={`w-8 rounded-t-lg transition-all duration-500 ${clsColors.bg.replace('/10', '/40')}`}
                                    style={{ height: `${Math.max(prob * 100, 4)}%` }}
                                  />
                                </div>
                                <div className="text-[10px] text-[var(--color-text-muted)] truncate">{cls}</div>
                                <div className={`text-xs font-bold ${prob > 0.5 ? clsColors.text : 'text-[var(--color-text-muted)]'}`}>
                                  {(prob * 100).toFixed(1)}%
                                </div>
                              </div>
                            );
                          })}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-3 py-1.5 rounded-lg text-xs text-[var(--color-text-muted)] hover:bg-white/5 disabled:opacity-30 transition-colors"
          >
            Previous
          </button>
          {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
            const pageNum = page <= 3 ? i + 1 : page - 2 + i;
            if (pageNum > totalPages) return null;
            return (
              <button
                key={pageNum}
                onClick={() => setPage(pageNum)}
                className={`w-8 h-8 rounded-lg text-xs font-medium transition-all ${
                  page === pageNum
                    ? 'bg-[var(--color-primary)]/20 text-[var(--color-primary)]'
                    : 'text-[var(--color-text-muted)] hover:bg-white/5'
                }`}
              >
                {pageNum}
              </button>
            );
          })}
          <button
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="px-3 py-1.5 rounded-lg text-xs text-[var(--color-text-muted)] hover:bg-white/5 disabled:opacity-30 transition-colors"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
