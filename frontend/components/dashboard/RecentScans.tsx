'use client';

import React from 'react';
import { FileSearch, Clock } from 'lucide-react';
import type { FileAnalysis } from '@/types';
import Badge from '@/components/ui/Badge';

interface RecentScansProps {
  scans: FileAnalysis[];
  onViewDetails?: (id: number) => void;
  className?: string;
}

function getRiskVariant(level: string | null) {
  switch (level) {
    case 'Critical': return 'danger' as const;
    case 'High': return 'warning' as const;
    case 'Medium': return 'warning' as const;
    case 'Low': return 'info' as const;
    default: return 'success' as const;
  }
}

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function RecentScans({ scans, onViewDetails, className = '' }: RecentScansProps) {
  if (scans.length === 0) {
    return (
      <div className={`glass rounded-2xl p-8 text-center ${className}`}>
        <FileSearch className="w-10 h-10 text-[var(--color-text-muted)]/30 mx-auto mb-3" />
        <p className="text-sm text-[var(--color-text-muted)]">No recent scans</p>
        <p className="text-xs text-[var(--color-text-muted)]/60 mt-1">Upload a file to get started</p>
      </div>
    );
  }

  return (
    <div className={`glass rounded-2xl ${className}`}>
      <div className="p-4 border-b border-[var(--color-border)]">
        <h3 className="text-base font-semibold text-[var(--color-text)] flex items-center gap-2">
          <Clock className="w-5 h-5 text-[var(--color-primary)]" />
          Recent Scans
        </h3>
      </div>
      <div className="divide-y divide-[var(--color-border)]">
        {scans.map((scan) => (
          <div
            key={scan.id}
            className="flex items-center gap-4 px-4 py-3 hover:bg-white/[0.03] transition-colors cursor-pointer"
            onClick={() => onViewDetails?.(scan.id)}
          >
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-[var(--color-text)] truncate">
                {scan.original_name}
              </p>
              <p className="text-xs text-[var(--color-text-muted)] flex items-center gap-2 mt-0.5">
                <span>{formatBytes(scan.file_size)}</span>
                <span>·</span>
                <span>{timeAgo(scan.upload_date)}</span>
              </p>
            </div>
            <div className="flex items-center gap-3 flex-shrink-0">
              {scan.risk_score !== null && (
                <span className="text-xs font-mono font-bold" style={{
                  color: scan.risk_score >= 60 ? 'var(--color-danger)' : scan.risk_score >= 30 ? 'var(--color-warning)' : 'var(--color-accent)',
                }}>
                  {scan.risk_score}
                </span>
              )}
              <Badge variant={getRiskVariant(scan.risk_level)} size="sm">
                {scan.risk_level || 'Pending'}
              </Badge>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
