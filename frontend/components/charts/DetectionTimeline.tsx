'use client';

import React from 'react';
import { Activity, Shield, AlertTriangle, CheckCircle } from 'lucide-react';

interface TimelineEvent {
  id: string | number;
  type: 'scan' | 'detection' | 'alert' | 'resolved';
  title: string;
  description: string;
  timestamp: string;
}

interface DetectionTimelineProps {
  events: TimelineEvent[];
  maxItems?: number;
  className?: string;
}

const typeConfig = {
  scan: { icon: Activity, color: 'var(--color-primary)', bg: 'bg-[var(--color-primary)]/15' },
  detection: { icon: Shield, color: 'var(--color-danger)', bg: 'bg-[var(--color-danger)]/15' },
  alert: { icon: AlertTriangle, color: 'var(--color-warning)', bg: 'bg-[var(--color-warning)]/15' },
  resolved: { icon: CheckCircle, color: 'var(--color-accent)', bg: 'bg-[var(--color-accent)]/15' },
};

function formatTimestamp(ts: string): string {
  const date = new Date(ts);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const mins = Math.floor(diff / 60000);

  if (mins < 1) return 'Just now';
  if (mins < 60) return `${mins}m ago`;
  if (mins < 1440) return `${Math.floor(mins / 60)}h ago`;
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

export default function DetectionTimeline({ events, maxItems = 8, className = '' }: DetectionTimelineProps) {
  const displayEvents = events.slice(0, maxItems);

  if (displayEvents.length === 0) {
    return (
      <div className={`glass rounded-2xl p-6 text-center ${className}`}>
        <Activity className="w-10 h-10 text-[var(--color-text-muted)]/30 mx-auto mb-3" />
        <p className="text-sm text-[var(--color-text-muted)]">No recent activity</p>
      </div>
    );
  }

  return (
    <div className={`glass rounded-2xl p-6 ${className}`}>
      <h3 className="text-base font-semibold text-[var(--color-text)] mb-4 flex items-center gap-2">
        <Activity className="w-5 h-5 text-[var(--color-primary)]" />
        Detection Timeline
      </h3>
      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-[15px] top-0 bottom-0 w-px bg-[var(--color-border)]" />

        <div className="space-y-4">
          {displayEvents.map((event, i) => {
            const config = typeConfig[event.type];
            const Icon = config.icon;
            return (
              <div key={event.id} className={`relative flex gap-4 pl-0 animate-slide-up stagger-${Math.min(i + 1, 6)}`}>
                {/* Icon */}
                <div className={`relative z-10 flex-shrink-0 w-[30px] h-[30px] rounded-full ${config.bg} flex items-center justify-center`}>
                  <Icon className="w-3.5 h-3.5" style={{ color: config.color }} />
                </div>
                {/* Content */}
                <div className="flex-1 min-w-0 pb-1">
                  <p className="text-sm font-medium text-[var(--color-text)]">{event.title}</p>
                  <p className="text-xs text-[var(--color-text-muted)] mt-0.5 truncate">{event.description}</p>
                  <p className="text-[10px] text-[var(--color-text-muted)]/60 mt-1">{formatTimestamp(event.timestamp)}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
