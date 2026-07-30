'use client';

import React from 'react';

type StatusType = 'online' | 'offline' | 'warning' | 'error' | 'pending' | 'analyzing' | 'completed';

interface StatusIndicatorProps {
  status: StatusType;
  label?: string;
  size?: 'sm' | 'md' | 'lg';
  pulse?: boolean;
  className?: string;
}

const statusConfig: Record<StatusType, { color: string; bg: string; label: string }> = {
  online: { color: 'bg-[var(--color-accent)]', bg: 'bg-[var(--color-accent)]/15', label: 'Online' },
  offline: { color: 'bg-gray-500', bg: 'bg-gray-500/15', label: 'Offline' },
  warning: { color: 'bg-[var(--color-warning)]', bg: 'bg-[var(--color-warning)]/15', label: 'Warning' },
  error: { color: 'bg-[var(--color-danger)]', bg: 'bg-[var(--color-danger)]/15', label: 'Error' },
  pending: { color: 'bg-[var(--color-warning)]', bg: 'bg-[var(--color-warning)]/15', label: 'Pending' },
  analyzing: { color: 'bg-[var(--color-primary)]', bg: 'bg-[var(--color-primary)]/15', label: 'Analyzing' },
  completed: { color: 'bg-[var(--color-accent)]', bg: 'bg-[var(--color-accent)]/15', label: 'Completed' },
};

const dotSizes = { sm: 'h-2 w-2', md: 'h-2.5 w-2.5', lg: 'h-3 w-3' };
const textSizes = { sm: 'text-xs', md: 'text-sm', lg: 'text-sm' };

export default function StatusIndicator({
  status,
  label,
  size = 'md',
  pulse = true,
  className = '',
}: StatusIndicatorProps) {
  const config = statusConfig[status];
  const displayLabel = label || config.label;
  const shouldPulse = pulse && ['online', 'analyzing'].includes(status);

  return (
    <span className={`inline-flex items-center gap-2 ${className}`}>
      <span className="relative flex">
        {shouldPulse && (
          <span className={`absolute inline-flex h-full w-full rounded-full ${config.color} opacity-50 animate-ping`} />
        )}
        <span className={`relative inline-flex rounded-full ${dotSizes[size]} ${config.color}`} />
      </span>
      {displayLabel && (
        <span className={`${textSizes[size]} font-medium text-[var(--color-text-muted)]`}>
          {displayLabel}
        </span>
      )}
    </span>
  );
}
