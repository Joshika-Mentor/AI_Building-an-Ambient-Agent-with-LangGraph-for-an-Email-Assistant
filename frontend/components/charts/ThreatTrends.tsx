'use client';

import React from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import { TrendingUp } from 'lucide-react';
import type { ThreatTrend } from '@/types';

interface ThreatTrendsProps {
  data: ThreatTrend[];
  className?: string;
}

export default function ThreatTrends({ data, className = '' }: ThreatTrendsProps) {
  if (data.length === 0) {
    return (
      <div className={`glass rounded-2xl p-6 text-center ${className}`}>
        <TrendingUp className="w-10 h-10 text-[var(--color-text-muted)]/30 mx-auto mb-3" />
        <p className="text-sm text-[var(--color-text-muted)]">No trend data available</p>
      </div>
    );
  }

  return (
    <div className={`glass rounded-2xl p-6 ${className}`}>
      <h3 className="text-base font-semibold text-[var(--color-text)] mb-4 flex items-center gap-2">
        <TrendingUp className="w-5 h-5 text-[var(--color-primary)]" />
        Detection Trends
      </h3>
      <ResponsiveContainer width="100%" height={260}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#00d4ff" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#00d4ff" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="colorRisk" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ff3366" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#ff3366" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 10, fill: '#94a3b8' }}
            axisLine={{ stroke: 'rgba(255,255,255,0.08)' }}
            tickLine={false}
          />
          <YAxis
            yAxisId="left"
            tick={{ fontSize: 10, fill: '#94a3b8' }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            yAxisId="right"
            orientation="right"
            tick={{ fontSize: 10, fill: '#94a3b8' }}
            axisLine={false}
            tickLine={false}
            domain={[0, 100]}
          />
          <Tooltip
            contentStyle={{
              background: 'rgba(30,41,59,0.95)',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '12px',
              fontSize: '12px',
              color: '#f1f5f9',
            }}
          />
          <Area
            yAxisId="left"
            type="monotone"
            dataKey="count"
            name="Detections"
            stroke="#00d4ff"
            fill="url(#colorCount)"
            strokeWidth={2}
          />
          <Area
            yAxisId="right"
            type="monotone"
            dataKey="risk_avg"
            name="Avg Risk"
            stroke="#ff3366"
            fill="url(#colorRisk)"
            strokeWidth={2}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
