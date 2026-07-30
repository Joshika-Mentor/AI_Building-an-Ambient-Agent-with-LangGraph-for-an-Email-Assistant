'use client';

import React, { useState } from 'react';
import { Mail, Lock, User, Eye, EyeOff, Shield, UserCog } from 'lucide-react';
import Input from '@/components/ui/Input';
import Select from '@/components/ui/Select';
import Button from '@/components/ui/Button';
import { useAuth } from '@/hooks/useAuth';
import { useRouter } from 'next/navigation';
import type { UserRole } from '@/types';

const roleOptions = [
  { value: 'security_analyst', label: 'Security Analyst' },
  { value: 'soc_member', label: 'SOC Team Member' },
  { value: 'administrator', label: 'Administrator' },
  { value: 'researcher', label: 'Researcher' },
];

export default function RegisterForm() {
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    full_name: '',
    role: 'security_analyst' as UserRole,
  });
  const [showPassword, setShowPassword] = useState(false);
  const { register, isLoading, error, clearError } = useAuth();
  const router = useRouter();

  const handleChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    try {
      await register(formData);
      router.push('/dashboard');
    } catch {
      // Error is set in store
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="text-center mb-6">
        <div className="inline-flex p-3 rounded-2xl bg-[var(--color-accent)]/10 mb-4">
          <Shield className="w-8 h-8 text-[var(--color-accent)]" />
        </div>
        <h1 className="text-2xl font-bold text-[var(--color-text)]">Create Account</h1>
        <p className="text-sm text-[var(--color-text-muted)] mt-1">Join the ThreatLens AI platform</p>
      </div>

      {error && (
        <div className="bg-[var(--color-danger)]/10 border border-[var(--color-danger)]/30 rounded-xl px-4 py-3 text-sm text-[var(--color-danger)]">
          {error}
        </div>
      )}

      <Input
        label="Full Name"
        value={formData.full_name}
        onChange={(e) => handleChange('full_name', e.target.value)}
        placeholder="Jane Doe"
        icon={<User className="w-4 h-4" />}
        required
      />

      <Input
        label="Username"
        value={formData.username}
        onChange={(e) => handleChange('username', e.target.value)}
        placeholder="jdoe"
        icon={<UserCog className="w-4 h-4" />}
        required
      />

      <Input
        label="Email"
        type="email"
        value={formData.email}
        onChange={(e) => handleChange('email', e.target.value)}
        placeholder="analyst@threatlens.ai"
        icon={<Mail className="w-4 h-4" />}
        required
      />

      <Input
        label="Password"
        type={showPassword ? 'text' : 'password'}
        value={formData.password}
        onChange={(e) => handleChange('password', e.target.value)}
        placeholder="Minimum 8 characters"
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
        minLength={8}
      />

      <Select
        label="Role"
        options={roleOptions}
        value={formData.role}
        onChange={(e) => handleChange('role', e.target.value)}
        placeholder=""
      />

      <Button type="submit" fullWidth isLoading={isLoading}>
        Create Account
      </Button>
    </form>
  );
}
