'use client';

import React from 'react';
import { Globe, AlertTriangle, Shield, Activity } from 'lucide-react';

interface ThreatMapProps {
  threats?: { region: string; count: number; severity: string }[];
  className?: string;
}

const regionData = [
  { id: 'na', name: 'North America', x: 22, y: 35, threats: 23 },
  { id: 'eu', name: 'Europe', x: 52, y: 28, threats: 18 },
  { id: 'as', name: 'Asia Pacific', x: 75, y: 38, threats: 31 },
  { id: 'sa', name: 'South America', x: 30, y: 65, threats: 7 },
  { id: 'af', name: 'Africa', x: 52, y: 55, threats: 5 },
  { id: 'me', name: 'Middle East', x: 60, y: 40, threats: 12 },
];

function getColor(count: number): string {
  if (count >= 25) return 'var(--color-danger)';
  if (count >= 15) return 'var(--color-warning)';
  if (count >= 8) return 'var(--color-primary)';
  return 'var(--color-accent)';
}

export default function ThreatMap({ className = '' }: ThreatMapProps) {
  const totalThreats = regionData.reduce((sum, r) => sum + r.threats, 0);

  return (
    <div className={`glass rounded-2xl p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-base font-semibold text-[var(--color-text)] flex items-center gap-2">
            <Globe className="w-5 h-5 text-[var(--color-primary)]" />
            Global Threat Map
          </h3>
          <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
            Active threat sources by region
          </p>
        </div>
        <div className="text-right">
          <p className="text-lg font-bold font-mono text-[var(--color-text)]">{totalThreats}</p>
          <p className="text-xs text-[var(--color-text-muted)]">Total Sources</p>
        </div>
      </div>

      {/* Simplified map visualization */}
      <div className="relative w-full aspect-[2/1] rounded-xl bg-white/[0.02] border border-[var(--color-border)] overflow-hidden">
        {/* Grid lines */}
        <div className="absolute inset-0 grid-bg opacity-30" />

        {/* Threat points */}
        {regionData.map((region) => {
          const color = getColor(region.threats);
          return (
            <div
              key={region.id}
              className="absolute group"
              style={{ left: `${region.x}%`, top: `${region.y}%`, transform: 'translate(-50%, -50%)' }}
            >
              {/* Ping effect */}
              <div
                className="absolute w-8 h-8 rounded-full animate-ping opacity-20"
                style={{ background: color, left: '-8px', top: '-8px' }}
              />
              {/* Dot */}
              <div
                className="relative w-3 h-3 rounded-full z-10 cursor-pointer"
                style={{ background: color, boxShadow: `0 0 8px ${color}80` }}
              />

              {/* Tooltip */}
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-20">
                <div className="glass-strong rounded-lg px-3 py-2 whitespace-nowrap text-xs">
                  <p className="font-semibold text-[var(--color-text)]">{region.name}</p>
                  <p className="text-[var(--color-text-muted)]">
                    {region.threats} active threats
                  </p>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 mt-4 text-xs text-[var(--color-text-muted)]">
        {[
          { label: 'Critical (25+)', color: 'var(--color-danger)' },
          { label: 'High (15+)', color: 'var(--color-warning)' },
          { label: 'Medium (8+)', color: 'var(--color-primary)' },
          { label: 'Low (<8)', color: 'var(--color-accent)' },
        ].map((item) => (
          <span key={item.label} className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full" style={{ background: item.color }} />
            {item.label}
          </span>
        ))}
      </div>
    </div>
  );
}
