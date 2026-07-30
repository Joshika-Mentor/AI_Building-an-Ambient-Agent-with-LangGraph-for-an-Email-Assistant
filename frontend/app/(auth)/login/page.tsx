'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Shield, Mail, Lock, Loader2, Eye, EyeOff } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import toast from 'react-hot-toast';

export default function LoginPage() {
  const router = useRouter();
  const { login, isLoading } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login({ email, password });
      toast.success('Welcome back!');
      router.push('/dashboard');
    } catch (err: any) {
      toast.error(err.message || 'Login failed');
    }
  };

  return (
    <div className="min-h-screen bg-[var(--color-surface)] grid-bg scan-line-bg flex items-center justify-center px-6">
      {/* Background glow effects */}
      <div className="fixed top-1/4 left-1/4 w-96 h-96 bg-[var(--color-primary)] opacity-5 rounded-full blur-[100px]" />
      <div className="fixed bottom-1/4 right-1/4 w-96 h-96 bg-[var(--color-accent)] opacity-5 rounded-full blur-[100px]" />

      <div className="w-full max-w-md animate-slide-up">
        {/* Logo */}
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)] flex items-center justify-center">
              <Shield className="w-7 h-7 text-[var(--color-surface)]" />
            </div>
          </Link>
          <h1 className="text-2xl font-bold text-[var(--color-text)]">Welcome Back</h1>
          <p className="text-sm text-[var(--color-text-muted)] mt-1">Sign in to ThreatLens AI</p>
        </div>

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="glass-strong rounded-2xl p-8 glow-cyan">
          {/* Email */}
          <div className="mb-5">
            <label htmlFor="login-email" className="block text-sm font-medium text-[var(--color-text-muted)] mb-2">
              Email Address
            </label>
            <div className="relative">
              <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-muted)]" />
              <input
                id="login-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="analyst@threatlens.ai"
                required
                className="w-full pl-11 pr-4 py-3 rounded-xl bg-white/5 border border-[var(--color-border)] text-[var(--color-text)] placeholder:text-[var(--color-text-muted)]/50 focus:outline-none focus:border-[var(--color-primary)]/50 focus:ring-1 focus:ring-[var(--color-primary)]/20 transition-all text-sm"
              />
            </div>
          </div>

          {/* Password */}
          <div className="mb-6">
            <label htmlFor="login-password" className="block text-sm font-medium text-[var(--color-text-muted)] mb-2">
              Password
            </label>
            <div className="relative">
              <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-muted)]" />
              <input
                id="login-password"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                required
                minLength={8}
                className="w-full pl-11 pr-11 py-3 rounded-xl bg-white/5 border border-[var(--color-border)] text-[var(--color-text)] placeholder:text-[var(--color-text-muted)]/50 focus:outline-none focus:border-[var(--color-primary)]/50 focus:ring-1 focus:ring-[var(--color-primary)]/20 transition-all text-sm"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3.5 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-3 rounded-xl font-semibold bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-accent)] text-[var(--color-surface)] hover:opacity-90 transition-opacity disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Signing in...
              </>
            ) : (
              'Sign In'
            )}
          </button>

          {/* Register link */}
          <p className="text-center text-sm text-[var(--color-text-muted)] mt-6">
            Don&apos;t have an account?{' '}
            <Link href="/register" className="text-[var(--color-primary)] hover:underline font-medium">
              Create Account
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
