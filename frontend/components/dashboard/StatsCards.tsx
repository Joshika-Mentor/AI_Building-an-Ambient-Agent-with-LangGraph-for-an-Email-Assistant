'use client';

import React from 'react';
import type { RiskLevel } from '@/types';

interface StatCard {
  label: string;
  value: string | number;
  change?: number;
  icon: React.ReactNode;
  color?: string;
}

interface StatsCardsProps {
  stats: StatCard[];
  className?: string;
}

export default function StatsCards({ stats, className = '' }: StatsCardsProps) {
  return (
    <div className={`grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 ${className}`}>
      {stats.map((stat, i) => (
        <div
          key={stat.label}
          className={`glass rounded-2xl p-5 animate-slide-up stagger-${i + 1} hover:bg-white/[0.06] transition-all duration-300`}
        >
          <div className="flex items-start justify-between">
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider">
                {stat.label}
              </p>
              <p
                className="text-2xl font-bold mt-1 font-mono"
                style={{ color: stat.color || 'var(--color-text)' }}
              >
                {stat.value}
              </p>
            </div>
            <div
              className="flex-shrink-0 p-2.5 rounded-xl"
              style={{ background: `${stat.color || 'var(--color-primary)'}15` }}
            >
              {stat.icon}
            </div>
          </div>

          {stat.change !== undefined && (
            <div className="mt-3 flex items-center gap-1">
              <span
                className={`text-xs font-semibold ${
                  stat.change >= 0 ? 'text-[var(--color-accent)]' : 'text-[var(--color-danger)]'
                }`}
              >
                {stat.change >= 0 ? '↑' : '↓'} {Math.abs(stat.change)}%
              </span>
              <span className="text-xs text-[var(--color-text-muted)]">vs last week</span>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
