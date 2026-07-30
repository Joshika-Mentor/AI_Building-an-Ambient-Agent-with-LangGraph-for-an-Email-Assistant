'use client';

import React from 'react';

type CardGlow = 'none' | 'cyan' | 'green' | 'red';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  glow?: CardGlow;
  hover?: boolean;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  onClick?: () => void;
}

interface CardHeaderProps {
  children: React.ReactNode;
  className?: string;
  action?: React.ReactNode;
}

interface CardFooterProps {
  children: React.ReactNode;
  className?: string;
}

const glowStyles: Record<CardGlow, string> = {
  none: '',
  cyan: 'glow-cyan',
  green: 'glow-green',
  red: 'glow-red',
};

const paddingStyles = {
  none: '',
  sm: 'p-4',
  md: 'p-6',
  lg: 'p-8',
};

export function Card({
  children,
  className = '',
  glow = 'none',
  hover = false,
  padding = 'md',
  onClick,
}: CardProps) {
  return (
    <div
      className={`
        glass rounded-2xl
        ${paddingStyles[padding]}
        ${glowStyles[glow]}
        ${hover ? 'hover:bg-white/[0.08] hover:border-white/15 transition-all duration-300 cursor-pointer' : ''}
        ${className}
      `}
      onClick={onClick}
    >
      {children}
    </div>
  );
}

export function CardHeader({ children, className = '', action }: CardHeaderProps) {
  return (
    <div className={`flex items-center justify-between mb-4 ${className}`}>
      <div>{children}</div>
      {action && <div>{action}</div>}
    </div>
  );
}

export function CardFooter({ children, className = '' }: CardFooterProps) {
  return (
    <div className={`mt-4 pt-4 border-t border-[var(--color-border)] ${className}`}>
      {children}
    </div>
  );
}

export default Card;
