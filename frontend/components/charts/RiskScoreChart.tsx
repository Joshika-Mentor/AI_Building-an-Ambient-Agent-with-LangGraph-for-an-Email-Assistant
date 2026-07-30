'use client';

import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { BarChart3 } from 'lucide-react';
import type { RiskDistribution } from '@/types';

interface RiskScoreChartProps {
  data: RiskDistribution;
  className?: string;
}

const RISK_CONFIG = [
  { key: 'clean', label: 'Clean', color: '#00ff88' },
  { key: 'low', label: 'Low', color: '#00d4ff' },
  { key: 'medium', label: 'Medium', color: '#ffaa00' },
  { key: 'high', label: 'High', color: '#ff6b35' },
  { key: 'critical', label: 'Critical', color: '#ff3366' },
];

export default function RiskScoreChart({ data, className = '' }: RiskScoreChartProps) {
  const chartData = RISK_CONFIG.map((config) => ({
    name: config.label,
    count: data[config.key as keyof RiskDistribution] || 0,
    color: config.color,
  }));

  const total = chartData.reduce((sum, d) => sum + d.count, 0);

  return (
    <div className={`glass rounded-2xl p-6 ${className}`}>
      <h3 className="text-base font-semibold text-[var(--color-text)] mb-4 flex items-center gap-2">
        <BarChart3 className="w-5 h-5 text-[var(--color-primary)]" />
        Risk Distribution
      </h3>

      {total === 0 ? (
        <div className="h-[200px] flex items-center justify-center">
          <p className="text-sm text-[var(--color-text-muted)]">No data to display</p>
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={chartData} barSize={32}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis
              dataKey="name"
              tick={{ fontSize: 11, fill: '#94a3b8' }}
              axisLine={{ stroke: 'rgba(255,255,255,0.08)' }}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 10, fill: '#94a3b8' }}
              axisLine={false}
              tickLine={false}
              allowDecimals={false}
            />
            <Tooltip
              contentStyle={{
                background: 'rgba(30,41,59,0.95)',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '12px',
                fontSize: '12px',
                color: '#f1f5f9',
              }}
              formatter={(value: number) => [`${value} files`, '']}
            />
            <Bar dataKey="count" radius={[6, 6, 0, 0]}>
              {chartData.map((entry) => (
                <Cell key={entry.name} fill={entry.color} fillOpacity={0.8} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
