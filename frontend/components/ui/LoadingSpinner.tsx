'use client';

import React from 'react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  label?: string;
  fullScreen?: boolean;
  className?: string;
}

const sizeStyles = {
  sm: 'w-4 h-4 border-2',
  md: 'w-8 h-8 border-[3px]',
  lg: 'w-12 h-12 border-4',
  xl: 'w-16 h-16 border-4',
};

export default function LoadingSpinner({
  size = 'md',
  label,
  fullScreen = false,
  className = '',
}: LoadingSpinnerProps) {
  const spinner = (
    <div className={`flex flex-col items-center gap-3 ${className}`}>
      <div
        className={`
          rounded-full animate-spin
          border-[var(--color-primary)]/20
          border-t-[var(--color-primary)]
          ${sizeStyles[size]}
        `}
        style={{
          boxShadow: '0 0 12px rgba(0, 212, 255, 0.15)',
        }}
      />
      {label && (
        <p className="text-sm text-[var(--color-text-muted)] animate-pulse">{label}</p>
      )}
    </div>
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-[var(--color-surface)]/80 backdrop-blur-sm">
        {spinner}
      </div>
    );
  }

  return spinner;
}
