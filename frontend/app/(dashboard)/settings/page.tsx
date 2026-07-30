'use client';

import { useState } from 'react';
import {
  Settings, User, Bell, Shield, Key, Moon, Sun, Monitor,
  Mail, Lock, Eye, EyeOff, Save, CheckCircle, AlertTriangle,
} from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';

type ThemeOption = 'dark' | 'light' | 'system';

export default function SettingsPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'profile' | 'notifications' | 'security' | 'appearance' | 'api'>('profile');
  const [saved, setSaved] = useState(false);

  // Profile state
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [email, setEmail] = useState(user?.email || '');

  // Notification state
  const [emailAlerts, setEmailAlerts] = useState(true);
  const [criticalOnly, setCriticalOnly] = useState(false);
  const [weeklyReport, setWeeklyReport] = useState(true);
  const [inAppNotifications, setInAppNotifications] = useState(true);

  // Appearance
  const [theme, setTheme] = useState<ThemeOption>('dark');

  // Security
  const [showCurrentPw, setShowCurrentPw] = useState(false);
  const [showNewPw, setShowNewPw] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // API Keys
  const [vtApiKey, setVtApiKey] = useState('');
  const [showVtKey, setShowVtKey] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  const tabs = [
    { id: 'profile' as const, label: 'Profile', icon: User },
    { id: 'notifications' as const, label: 'Notifications', icon: Bell },
    { id: 'security' as const, label: 'Security', icon: Shield },
    { id: 'appearance' as const, label: 'Appearance', icon: Moon },
    { id: 'api' as const, label: 'API Keys', icon: Key },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[var(--color-text)]">Settings</h1>
        <p className="text-sm text-[var(--color-text-muted)] mt-1">
          Manage your profile, preferences, and platform configuration.
        </p>
      </div>

      {/* Success toast */}
      {saved && (
        <div className="flex items-center gap-2 bg-[var(--color-accent)]/10 border border-[var(--color-accent)]/30 rounded-xl px-4 py-3 text-sm text-[var(--color-accent)] animate-slide-up">
          <CheckCircle className="w-4 h-4" />
          Settings saved successfully
        </div>
      )}

      <div className="flex flex-col lg:flex-row gap-6">
        {/* Sidebar tabs */}
        <nav className="lg:w-56 flex-shrink-0">
          <div className="glass rounded-2xl p-2 flex lg:flex-col gap-1 overflow-x-auto lg:overflow-visible">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium
                    transition-all duration-200 whitespace-nowrap cursor-pointer
                    ${activeTab === tab.id
                      ? 'bg-[var(--color-primary)]/15 text-[var(--color-primary)]'
                      : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-white/5'
                    }
                  `}
                >
                  <Icon className="w-4 h-4 flex-shrink-0" />
                  {tab.label}
                </button>
              );
            })}
          </div>
        </nav>

        {/* Content area */}
        <div className="flex-1 min-w-0">
          {/* ── Profile ─────────────────────────────── */}
          {activeTab === 'profile' && (
            <div className="glass rounded-2xl p-6 space-y-6 animate-fade-in">
              <h2 className="text-lg font-semibold text-[var(--color-text)] flex items-center gap-2">
                <User className="w-5 h-5 text-[var(--color-primary)]" />
                Profile Information
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-[var(--color-text-muted)] mb-1.5">Full Name</label>
                  <input
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="w-full bg-white/5 border border-[var(--color-border)] rounded-xl px-4 py-2.5 text-sm text-[var(--color-text)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/40"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-[var(--color-text-muted)] mb-1.5">Email</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full bg-white/5 border border-[var(--color-border)] rounded-xl px-4 py-2.5 text-sm text-[var(--color-text)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/40"
                  />
                </div>
              </div>

              {/* Read-only fields */}
              <div className="space-y-3 pt-2 border-t border-[var(--color-border)]">
                {[
                  { label: 'Username', value: user?.username },
                  { label: 'Role', value: user?.role?.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase()) },
                  { label: 'Account Status', value: user?.is_active ? 'Active' : 'Inactive' },
                  { label: 'Member Since', value: user?.created_at ? new Date(user.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' }) : '—' },
                ].map((field) => (
                  <div key={field.label} className="flex items-center justify-between py-2">
                    <span className="text-sm text-[var(--color-text-muted)]">{field.label}</span>
                    <span className="text-sm font-medium text-[var(--color-text)]">{field.value || '—'}</span>
                  </div>
                ))}
              </div>

              <div className="flex justify-end">
                <button onClick={handleSave} className="flex items-center gap-2 bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-primary-dark)] text-[var(--color-surface)] px-5 py-2.5 rounded-xl font-semibold text-sm hover:shadow-[0_0_20px_rgba(0,212,255,0.3)] transition-all cursor-pointer">
                  <Save className="w-4 h-4" /> Save Changes
                </button>
              </div>
            </div>
          )}

          {/* ── Notifications ─────────────────────── */}
          {activeTab === 'notifications' && (
            <div className="glass rounded-2xl p-6 space-y-6 animate-fade-in">
              <h2 className="text-lg font-semibold text-[var(--color-text)] flex items-center gap-2">
                <Bell className="w-5 h-5 text-[var(--color-warning)]" />
                Notification Preferences
              </h2>

              <div className="space-y-4">
                {[
                  { label: 'Email alerts for new threats', description: 'Receive emails when high-severity threats are detected', state: emailAlerts, setter: setEmailAlerts },
                  { label: 'Critical alerts only', description: 'Only send emails for critical-severity detections', state: criticalOnly, setter: setCriticalOnly },
                  { label: 'Weekly security report', description: 'Receive a weekly summary of platform activity', state: weeklyReport, setter: setWeeklyReport },
                  { label: 'In-app notifications', description: 'Show notifications in the dashboard header', state: inAppNotifications, setter: setInAppNotifications },
                ].map((pref) => (
                  <div key={pref.label} className="flex items-center justify-between py-3 border-b border-[var(--color-border)] last:border-0">
                    <div>
                      <p className="text-sm font-medium text-[var(--color-text)]">{pref.label}</p>
                      <p className="text-xs text-[var(--color-text-muted)] mt-0.5">{pref.description}</p>
                    </div>
                    <button
                      onClick={() => pref.setter(!pref.state)}
                      className={`relative w-11 h-6 rounded-full transition-colors duration-200 cursor-pointer ${pref.state ? 'bg-[var(--color-primary)]' : 'bg-white/10'}`}
                    >
                      <span className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white transition-transform duration-200 ${pref.state ? 'translate-x-5' : ''}`} />
                    </button>
                  </div>
                ))}
              </div>

              <div className="flex justify-end">
                <button onClick={handleSave} className="flex items-center gap-2 bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-primary-dark)] text-[var(--color-surface)] px-5 py-2.5 rounded-xl font-semibold text-sm hover:shadow-[0_0_20px_rgba(0,212,255,0.3)] transition-all cursor-pointer">
                  <Save className="w-4 h-4" /> Save Preferences
                </button>
              </div>
            </div>
          )}

          {/* ── Security ──────────────────────────── */}
          {activeTab === 'security' && (
            <div className="glass rounded-2xl p-6 space-y-6 animate-fade-in">
              <h2 className="text-lg font-semibold text-[var(--color-text)] flex items-center gap-2">
                <Shield className="w-5 h-5 text-[var(--color-accent)]" />
                Security Settings
              </h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-[var(--color-text-muted)] mb-1.5">Current Password</label>
                  <div className="relative">
                    <input
                      type={showCurrentPw ? 'text' : 'password'}
                      value={currentPassword}
                      onChange={(e) => setCurrentPassword(e.target.value)}
                      className="w-full bg-white/5 border border-[var(--color-border)] rounded-xl px-4 py-2.5 text-sm text-[var(--color-text)] pr-10 focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/40"
                      placeholder="••••••••"
                    />
                    <button onClick={() => setShowCurrentPw(!showCurrentPw)} className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)] hover:text-[var(--color-text)] cursor-pointer">
                      {showCurrentPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-[var(--color-text-muted)] mb-1.5">New Password</label>
                    <div className="relative">
                      <input
                        type={showNewPw ? 'text' : 'password'}
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        className="w-full bg-white/5 border border-[var(--color-border)] rounded-xl px-4 py-2.5 text-sm text-[var(--color-text)] pr-10 focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/40"
                        placeholder="Min 8 characters"
                      />
                      <button onClick={() => setShowNewPw(!showNewPw)} className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)] hover:text-[var(--color-text)] cursor-pointer">
                        {showNewPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-[var(--color-text-muted)] mb-1.5">Confirm New Password</label>
                    <input
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      className="w-full bg-white/5 border border-[var(--color-border)] rounded-xl px-4 py-2.5 text-sm text-[var(--color-text)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/40"
                      placeholder="Re-enter password"
                    />
                  </div>
                </div>

                {newPassword && confirmPassword && newPassword !== confirmPassword && (
                  <div className="flex items-center gap-2 text-xs text-[var(--color-danger)]">
                    <AlertTriangle className="w-3 h-3" />
                    Passwords do not match
                  </div>
                )}
              </div>

              <div className="pt-4 border-t border-[var(--color-border)]">
                <h3 className="text-sm font-semibold text-[var(--color-text)] mb-3">Active Sessions</h3>
                <div className="glass rounded-xl p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-2 h-2 rounded-full bg-[var(--color-accent)]" />
                      <div>
                        <p className="text-sm text-[var(--color-text)]">Current session</p>
                        <p className="text-xs text-[var(--color-text-muted)]">Windows · Chrome · Last active now</p>
                      </div>
                    </div>
                    <span className="text-xs text-[var(--color-accent)] font-medium">Active</span>
                  </div>
                </div>
              </div>

              <div className="flex justify-end">
                <button onClick={handleSave} className="flex items-center gap-2 bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-primary-dark)] text-[var(--color-surface)] px-5 py-2.5 rounded-xl font-semibold text-sm hover:shadow-[0_0_20px_rgba(0,212,255,0.3)] transition-all cursor-pointer">
                  <Lock className="w-4 h-4" /> Update Password
                </button>
              </div>
            </div>
          )}

          {/* ── Appearance ─────────────────────────── */}
          {activeTab === 'appearance' && (
            <div className="glass rounded-2xl p-6 space-y-6 animate-fade-in">
              <h2 className="text-lg font-semibold text-[var(--color-text)] flex items-center gap-2">
                <Moon className="w-5 h-5 text-[var(--color-purple)]" />
                Appearance
              </h2>

              <div>
                <p className="text-sm text-[var(--color-text-muted)] mb-4">Choose your preferred theme</p>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { id: 'dark' as ThemeOption, label: 'Dark', icon: Moon, description: 'Cybersecurity dark theme' },
                    { id: 'light' as ThemeOption, label: 'Light', icon: Sun, description: 'Light mode' },
                    { id: 'system' as ThemeOption, label: 'System', icon: Monitor, description: 'Follow OS setting' },
                  ].map((opt) => {
                    const Icon = opt.icon;
                    return (
                      <button
                        key={opt.id}
                        onClick={() => setTheme(opt.id)}
                        className={`
                          flex flex-col items-center gap-2 p-4 rounded-xl border transition-all duration-200 cursor-pointer
                          ${theme === opt.id
                            ? 'border-[var(--color-primary)] bg-[var(--color-primary)]/10'
                            : 'border-[var(--color-border)] hover:border-white/20 hover:bg-white/[0.03]'
                          }
                        `}
                      >
                        <Icon className={`w-6 h-6 ${theme === opt.id ? 'text-[var(--color-primary)]' : 'text-[var(--color-text-muted)]'}`} />
                        <span className={`text-sm font-medium ${theme === opt.id ? 'text-[var(--color-primary)]' : 'text-[var(--color-text)]'}`}>{opt.label}</span>
                        <span className="text-[10px] text-[var(--color-text-muted)]">{opt.description}</span>
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {/* ── API Keys ───────────────────────────── */}
          {activeTab === 'api' && (
            <div className="glass rounded-2xl p-6 space-y-6 animate-fade-in">
              <h2 className="text-lg font-semibold text-[var(--color-text)] flex items-center gap-2">
                <Key className="w-5 h-5 text-[var(--color-warning)]" />
                API Keys & Integrations
              </h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-[var(--color-text-muted)] mb-1.5">VirusTotal API Key</label>
                  <div className="relative">
                    <input
                      type={showVtKey ? 'text' : 'password'}
                      value={vtApiKey}
                      onChange={(e) => setVtApiKey(e.target.value)}
                      className="w-full bg-white/5 border border-[var(--color-border)] rounded-xl px-4 py-2.5 text-sm text-[var(--color-text)] pr-10 font-mono focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/40"
                      placeholder="Enter your VT API key"
                    />
                    <button onClick={() => setShowVtKey(!showVtKey)} className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)] hover:text-[var(--color-text)] cursor-pointer">
                      {showVtKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  <p className="text-xs text-[var(--color-text-muted)] mt-1">Used for hash lookups and threat enrichment</p>
                </div>

                {/* Integration Status */}
                <div className="pt-4 border-t border-[var(--color-border)]">
                  <h3 className="text-sm font-semibold text-[var(--color-text)] mb-3">Integration Status</h3>
                  <div className="space-y-2">
                    {[
                      { name: 'VirusTotal', status: vtApiKey ? 'Connected' : 'Not configured', active: !!vtApiKey },
                      { name: 'SIEM/SOAR Webhook', status: 'Connected', active: true },
                      { name: 'Email Notifications', status: 'Not configured', active: false },
                      { name: 'Threat Intelligence Feed', status: 'Active', active: true },
                    ].map((integration) => (
                      <div key={integration.name} className="flex items-center justify-between py-2">
                        <span className="text-sm text-[var(--color-text)]">{integration.name}</span>
                        <span className={`flex items-center gap-1.5 text-xs font-medium ${integration.active ? 'text-[var(--color-accent)]' : 'text-[var(--color-text-muted)]'}`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${integration.active ? 'bg-[var(--color-accent)]' : 'bg-[var(--color-text-muted)]'}`} />
                          {integration.status}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="flex justify-end">
                <button onClick={handleSave} className="flex items-center gap-2 bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-primary-dark)] text-[var(--color-surface)] px-5 py-2.5 rounded-xl font-semibold text-sm hover:shadow-[0_0_20px_rgba(0,212,255,0.3)] transition-all cursor-pointer">
                  <Save className="w-4 h-4" /> Save Keys
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
