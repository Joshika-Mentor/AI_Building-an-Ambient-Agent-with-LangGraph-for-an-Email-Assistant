'use client';

import React from 'react';
import { Upload, Search, Shield, FileText, BarChart3, Bell } from 'lucide-react';
import { useRouter } from 'next/navigation';

interface QuickActionsProps {
  className?: string;
}

const actions = [
  { label: 'Upload File', icon: Upload, href: '/upload', color: 'var(--color-primary)' },
  { label: 'View Threats', icon: Shield, href: '/threats', color: 'var(--color-danger)' },
  { label: 'Analytics', icon: BarChart3, href: '/analytics', color: 'var(--color-accent)' },
  { label: 'Reports', icon: FileText, href: '/reports', color: 'var(--color-purple)' },
  { label: 'Alerts', icon: Bell, href: '/alerts', color: 'var(--color-warning)' },
  { label: 'Classify', icon: Search, href: '/classifications', color: 'var(--color-primary-dark)' },
];

export default function QuickActions({ className = '' }: QuickActionsProps) {
  const router = useRouter();

  return (
    <div className={`glass rounded-2xl p-5 ${className}`}>
      <h3 className="text-base font-semibold text-[var(--color-text)] mb-4">Quick Actions</h3>
      <div className="grid grid-cols-3 sm:grid-cols-6 gap-3">
        {actions.map((action) => {
          const Icon = action.icon;
          return (
            <button
              key={action.label}
              onClick={() => router.push(action.href)}
              className="flex flex-col items-center gap-2 p-3 rounded-xl hover:bg-white/[0.06] transition-all duration-200 group cursor-pointer"
            >
              <div
                className="p-2.5 rounded-xl transition-all duration-200 group-hover:scale-110"
                style={{ background: `${action.color}15` }}
              >
                <Icon className="w-5 h-5" style={{ color: action.color }} />
              </div>
              <span className="text-xs text-[var(--color-text-muted)] group-hover:text-[var(--color-text)] transition-colors">
                {action.label}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
