'use client';

import { Bell, Search, LogOut, User } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

const roleBadgeColors: Record<string, string> = {
  security_analyst: 'bg-[var(--color-primary)]/15 text-[var(--color-primary)]',
  soc_member: 'bg-[var(--color-warning)]/15 text-[var(--color-warning)]',
  administrator: 'bg-[var(--color-danger)]/15 text-[var(--color-danger)]',
  researcher: 'bg-[var(--color-purple)]/15 text-[var(--color-purple)]',
};

const roleLabels: Record<string, string> = {
  security_analyst: 'Analyst',
  soc_member: 'SOC',
  administrator: 'Admin',
  researcher: 'Researcher',
};

export default function Header() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [showMenu, setShowMenu] = useState(false);

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  return (
    <header className="h-16 glass-strong border-b border-[var(--color-border)] flex items-center justify-between px-6 sticky top-0 z-30">
      {/* Search */}
      <div className="relative w-72">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-muted)]" />
        <input
          type="text"
          placeholder="Search files, threats, alerts..."
          className="w-full pl-10 pr-4 py-2 rounded-lg bg-white/5 border border-[var(--color-border)] text-sm text-[var(--color-text)] placeholder:text-[var(--color-text-muted)]/50 focus:outline-none focus:border-[var(--color-primary)]/40 transition-colors"
        />
      </div>

      {/* Right side */}
      <div className="flex items-center gap-4">
        {/* Notification bell */}
        <button className="relative p-2 rounded-lg hover:bg-white/5 text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-[var(--color-danger)] animate-pulse-glow" />
        </button>

        {/* User menu */}
        <div className="relative">
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="flex items-center gap-3 px-3 py-1.5 rounded-xl hover:bg-white/5 transition-colors"
          >
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)] flex items-center justify-center">
              <User className="w-4 h-4 text-[var(--color-surface)]" />
            </div>
            <div className="text-left hidden md:block">
              <div className="text-sm font-medium text-[var(--color-text)]">{user?.full_name || 'User'}</div>
              <div className={`text-xs px-1.5 py-0.5 rounded inline-block ${roleBadgeColors[user?.role || ''] || ''}`}>
                {roleLabels[user?.role || ''] || user?.role}
              </div>
            </div>
          </button>

          {showMenu && (
            <div className="absolute right-0 top-full mt-2 w-48 glass-strong rounded-xl py-2 animate-fade-in">
              <button
                onClick={handleLogout}
                className="w-full flex items-center gap-2 px-4 py-2 text-sm text-[var(--color-danger)] hover:bg-white/5 transition-colors"
              >
                <LogOut className="w-4 h-4" />
                Sign Out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
