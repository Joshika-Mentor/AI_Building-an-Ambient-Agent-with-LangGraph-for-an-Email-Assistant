'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Shield, LayoutDashboard, Upload, GitBranch, AlertTriangle, Bell, BarChart3, Users, Settings, ChevronLeft, ChevronRight, FileText } from 'lucide-react';
import { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';

const navItems = [
  { href: '/dashboard', icon: LayoutDashboard, label: 'Dashboard', roles: null },
  { href: '/dashboard/upload', icon: Upload, label: 'Upload & Analyze', roles: ['security_analyst', 'administrator', 'researcher'] },
  { href: '/dashboard/classifications', icon: GitBranch, label: 'Classifications', roles: null },
  { href: '/dashboard/threats', icon: AlertTriangle, label: 'Threats', roles: null },
  { href: '/dashboard/alerts', icon: Bell, label: 'Alerts', roles: null },
  { href: '/dashboard/analytics', icon: BarChart3, label: 'Analytics', roles: null },
  { href: '/dashboard/reports', icon: FileText, label: 'Reports', roles: null },
  { href: '/dashboard/users', icon: Users, label: 'Users', roles: ['administrator'] },
  { href: '/dashboard/settings', icon: Settings, label: 'Settings', roles: null },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user } = useAuth();
  const [collapsed, setCollapsed] = useState(false);

  const filteredItems = navItems.filter(
    (item) => !item.roles || (user && item.roles.includes(user.role))
  );

  return (
    <aside className={`fixed left-0 top-0 h-full z-40 glass-strong transition-all duration-300 flex flex-col ${collapsed ? 'w-[72px]' : 'w-60'}`}>
      {/* Logo */}
      <div className="h-16 flex items-center px-4 border-b border-[var(--color-border)]">
        <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)] flex items-center justify-center flex-shrink-0">
          <Shield className="w-5 h-5 text-[var(--color-surface)]" />
        </div>
        {!collapsed && <span className="ml-3 text-base font-bold text-[var(--color-text)] whitespace-nowrap">ThreatLens AI</span>}
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
        {filteredItems.map((item) => {
          const isActive = pathname === item.href || (item.href !== '/dashboard' && pathname?.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all group ${
                isActive
                  ? 'bg-[var(--color-primary)]/10 text-[var(--color-primary)]'
                  : 'text-[var(--color-text-muted)] hover:bg-white/5 hover:text-[var(--color-text)]'
              }`}
            >
              <item.icon className={`w-[18px] h-[18px] flex-shrink-0 ${isActive ? 'text-[var(--color-primary)]' : ''}`} />
              {!collapsed && <span className="whitespace-nowrap">{item.label}</span>}
              {isActive && !collapsed && (
                <div className="ml-auto w-1.5 h-1.5 rounded-full bg-[var(--color-primary)] animate-pulse-glow" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* Collapse toggle */}
      <div className="p-3 border-t border-[var(--color-border)]">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="w-full flex items-center justify-center p-2 rounded-lg hover:bg-white/5 text-[var(--color-text-muted)] transition-colors"
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>
    </aside>
  );
}
