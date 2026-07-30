'use client';

import React, { useState } from 'react';
import { Mail, Lock, Eye, EyeOff, Shield } from 'lucide-react';
import Input from '@/components/ui/Input';
import Button from '@/components/ui/Button';
import { useAuth } from '@/hooks/useAuth';
import { useRouter } from 'next/navigation';

export default function LoginForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const { login, isLoading, error, clearError } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    try {
      await login({ email, password });
      router.push('/dashboard');
    } catch {
      // Error is set in store
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div className="text-center mb-8">
        <div className="inline-flex p-3 rounded-2xl bg-[var(--color-primary)]/10 mb-4">
          <Shield className="w-8 h-8 text-[var(--color-primary)]" />
        </div>
        <h1 className="text-2xl font-bold text-[var(--color-text)]">Welcome Back</h1>
        <p className="text-sm text-[var(--color-text-muted)] mt-1">Sign in to ThreatLens AI</p>
      </div>

      {error && (
        <div className="bg-[var(--color-danger)]/10 border border-[var(--color-danger)]/30 rounded-xl px-4 py-3 text-sm text-[var(--color-danger)]">
          {error}
        </div>
      )}

      <Input
        label="Email"
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="analyst@threatlens.ai"
        icon={<Mail className="w-4 h-4" />}
        required
        autoComplete="email"
      />

      <Input
        label="Password"
        type={showPassword ? 'text' : 'password'}
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="••••••••"
        icon={<Lock className="w-4 h-4" />}
        iconRight={
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="hover:text-[var(--color-text)] transition-colors"
          >
            {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </button>
        }
        required
        autoComplete="current-password"
      />

      <Button type="submit" fullWidth isLoading={isLoading}>
        Sign In
      </Button>
    </form>
  );
}
