'use client';

import React from 'react';

interface RiskGaugeProps {
  score: number;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  className?: string;
}

const sizeConfig = {
  sm: { width: 80, stroke: 6, fontSize: 14, labelSize: 8 },
  md: { width: 120, stroke: 8, fontSize: 22, labelSize: 11 },
  lg: { width: 160, stroke: 10, fontSize: 30, labelSize: 13 },
};

function getRiskColor(score: number): string {
  if (score >= 80) return '#ff3366';
  if (score >= 60) return '#ff6b35';
  if (score >= 40) return '#ffaa00';
  if (score >= 20) return '#00d4ff';
  return '#00ff88';
}

function getRiskLabel(score: number): string {
  if (score >= 80) return 'Critical';
  if (score >= 60) return 'High';
  if (score >= 40) return 'Medium';
  if (score >= 20) return 'Low';
  return 'Clean';
}

export default function RiskGauge({
  score,
  size = 'md',
  showLabel = true,
  className = '',
}: RiskGaugeProps) {
  const config = sizeConfig[size];
  const radius = (config.width - config.stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = Math.min(100, Math.max(0, score));
  const dashOffset = circumference - (progress / 100) * circumference;
  const color = getRiskColor(score);
  const label = getRiskLabel(score);

  return (
    <div className={`flex flex-col items-center ${className}`}>
      <svg
        width={config.width}
        height={config.width}
        className="transform -rotate-90"
      >
        {/* Background circle */}
        <circle
          cx={config.width / 2}
          cy={config.width / 2}
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.06)"
          strokeWidth={config.stroke}
        />
        {/* Progress circle */}
        <circle
          cx={config.width / 2}
          cy={config.width / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={config.stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          style={{
            transition: 'stroke-dashoffset 1s ease-in-out, stroke 0.3s ease',
            filter: `drop-shadow(0 0 6px ${color}50)`,
          }}
        />
        {/* Score text */}
        <text
          x={config.width / 2}
          y={config.width / 2}
          textAnchor="middle"
          dominantBaseline="central"
          fill={color}
          fontSize={config.fontSize}
          fontWeight="700"
          fontFamily="var(--font-mono)"
          transform={`rotate(90, ${config.width / 2}, ${config.width / 2})`}
        >
          {Math.round(score)}
        </text>
      </svg>
      {showLabel && (
        <span
          className="mt-1 font-semibold uppercase tracking-wide"
          style={{ color, fontSize: config.labelSize }}
        >
          {label}
        </span>
      )}
    </div>
  );
}
