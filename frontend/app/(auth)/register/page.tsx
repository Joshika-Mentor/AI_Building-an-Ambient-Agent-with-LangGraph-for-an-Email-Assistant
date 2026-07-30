'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Shield, Mail, Lock, User, Loader2, Eye, EyeOff, BadgeCheck } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import toast from 'react-hot-toast';
import type { UserRole } from '@/types';

const roles: { value: UserRole; label: string; desc: string }[] = [
  { value: 'security_analyst', label: 'Security Analyst', desc: 'Upload files, run scans, view reports' },
  { value: 'soc_member', label: 'SOC Team Member', desc: 'Monitor threats, review alerts, track incidents' },
  { value: 'researcher', label: 'Researcher', desc: 'Analyze malware samples, access datasets' },
  { value: 'administrator', label: 'Administrator', desc: 'Full platform access & user management' },
];

export default function RegisterPage() {
  const router = useRouter();
  const { register, isLoading } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    full_name: '',
    role: 'security_analyst' as UserRole,
  });
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await register(formData);
      toast.success('Account created successfully!');
      router.push('/dashboard');
    } catch (err: any) {
      toast.error(err.message || 'Registration failed');
    }
  };

  const updateField = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <div className="min-h-screen bg-[var(--color-surface)] grid-bg scan-line-bg flex items-center justify-center px-6 py-12">
      <div className="fixed top-1/3 right-1/4 w-80 h-80 bg-[var(--color-accent)] opacity-5 rounded-full blur-[100px]" />
      <div className="fixed bottom-1/3 left-1/4 w-80 h-80 bg-[var(--color-primary)] opacity-5 rounded-full blur-[100px]" />

      <div className="w-full max-w-lg animate-slide-up">
        {/* Logo */}
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)] flex items-center justify-center">
              <Shield className="w-7 h-7 text-[var(--color-surface)]" />
            </div>
          </Link>
          <h1 className="text-2xl font-bold text-[var(--color-text)]">Create Account</h1>
          <p className="text-sm text-[var(--color-text-muted)] mt-1">Join ThreatLens AI Platform</p>
        </div>

        <form onSubmit={handleSubmit} className="glass-strong rounded-2xl p-8 glow-cyan">
          {/* Full Name */}
          <div className="mb-4">
            <label htmlFor="reg-name" className="block text-sm font-medium text-[var(--color-text-muted)] mb-2">Full Name</label>
            <div className="relative">
              <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-muted)]" />
              <input id="reg-name" type="text" value={formData.full_name} onChange={(e) => updateField('full_name', e.target.value)} placeholder="John Doe" required className="w-full pl-11 pr-4 py-3 rounded-xl bg-white/5 border border-[var(--color-border)] text-[var(--color-text)] placeholder:text-[var(--color-text-muted)]/50 focus:outline-none focus:border-[var(--color-primary)]/50 focus:ring-1 focus:ring-[var(--color-primary)]/20 transition-all text-sm" />
            </div>
          </div>

          {/* Username */}
          <div className="mb-4">
            <label htmlFor="reg-username" className="block text-sm font-medium text-[var(--color-text-muted)] mb-2">Username</label>
            <div className="relative">
              <BadgeCheck className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-muted)]" />
              <input id="reg-username" type="text" value={formData.username} onChange={(e) => updateField('username', e.target.value)} placeholder="johndoe" required pattern="^[a-zA-Z0-9_]+$" minLength={3} className="w-full pl-11 pr-4 py-3 rounded-xl bg-white/5 border border-[var(--color-border)] text-[var(--color-text)] placeholder:text-[var(--color-text-muted)]/50 focus:outline-none focus:border-[var(--color-primary)]/50 focus:ring-1 focus:ring-[var(--color-primary)]/20 transition-all text-sm" />
            </div>
          </div>

          {/* Email */}
          <div className="mb-4">
            <label htmlFor="reg-email" className="block text-sm font-medium text-[var(--color-text-muted)] mb-2">Email</label>
            <div className="relative">
              <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-muted)]" />
              <input id="reg-email" type="email" value={formData.email} onChange={(e) => updateField('email', e.target.value)} placeholder="analyst@threatlens.ai" required className="w-full pl-11 pr-4 py-3 rounded-xl bg-white/5 border border-[var(--color-border)] text-[var(--color-text)] placeholder:text-[var(--color-text-muted)]/50 focus:outline-none focus:border-[var(--color-primary)]/50 focus:ring-1 focus:ring-[var(--color-primary)]/20 transition-all text-sm" />
            </div>
          </div>

          {/* Password */}
          <div className="mb-5">
            <label htmlFor="reg-password" className="block text-sm font-medium text-[var(--color-text-muted)] mb-2">Password</label>
            <div className="relative">
              <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-muted)]" />
              <input id="reg-password" type={showPassword ? 'text' : 'password'} value={formData.password} onChange={(e) => updateField('password', e.target.value)} placeholder="Min 8 characters" required minLength={8} className="w-full pl-11 pr-11 py-3 rounded-xl bg-white/5 border border-[var(--color-border)] text-[var(--color-text)] placeholder:text-[var(--color-text-muted)]/50 focus:outline-none focus:border-[var(--color-primary)]/50 focus:ring-1 focus:ring-[var(--color-primary)]/20 transition-all text-sm" />
              <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3.5 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)] hover:text-[var(--color-text)]">
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {/* Role Selection */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-[var(--color-text-muted)] mb-3">Select Your Role</label>
            <div className="grid grid-cols-2 gap-2">
              {roles.map((role) => (
                <button
                  key={role.value}
                  type="button"
                  onClick={() => updateField('role', role.value)}
                  className={`p-3 rounded-xl border text-left transition-all ${
                    formData.role === role.value
                      ? 'border-[var(--color-primary)]/50 bg-[var(--color-primary)]/10'
                      : 'border-[var(--color-border)] bg-white/3 hover:bg-white/5'
                  }`}
                >
                  <div className={`text-sm font-medium ${formData.role === role.value ? 'text-[var(--color-primary)]' : 'text-[var(--color-text)]'}`}>
                    {role.label}
                  </div>
                  <div className="text-xs text-[var(--color-text-muted)] mt-0.5">{role.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Submit */}
          <button type="submit" disabled={isLoading} className="w-full py-3 rounded-xl font-semibold bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-accent)] text-[var(--color-surface)] hover:opacity-90 transition-opacity disabled:opacity-50 flex items-center justify-center gap-2">
            {isLoading ? (<><Loader2 className="w-4 h-4 animate-spin" />Creating Account...</>) : 'Create Account'}
          </button>

          <p className="text-center text-sm text-[var(--color-text-muted)] mt-6">
            Already have an account?{' '}
            <Link href="/login" className="text-[var(--color-primary)] hover:underline font-medium">Sign In</Link>
          </p>
        </form>
      </div>
    </div>
  );
}
