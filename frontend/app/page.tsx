'use client';

import Link from 'next/link';
import { Shield, Scan, Brain, Bell, BarChart3, Upload, ChevronRight, Lock } from 'lucide-react';

const features = [
  { icon: Upload, title: 'File Analysis', desc: 'Upload suspicious files for comprehensive static analysis, PE parsing, and YARA rule matching.', color: 'text-[var(--color-primary)]' },
  { icon: Brain, title: 'AI Classification', desc: 'Machine learning-powered malware classification identifies threat families with confidence scoring.', color: 'text-[var(--color-accent)]' },
  { icon: Scan, title: 'Threat Monitoring', desc: 'Real-time threat monitoring with detection logs, incident tracking, and automated alerts.', color: 'text-[var(--color-warning)]' },
  { icon: BarChart3, title: 'Analytics Dashboard', desc: 'Interactive dashboards with malware distribution, trend analysis, and risk scoring.', color: 'text-[var(--color-purple)]' },
  { icon: Bell, title: 'Smart Alerts', desc: 'Automated alert generation for high-risk detections with severity-based prioritization.', color: 'text-[var(--color-danger)]' },
  { icon: Lock, title: 'Role-Based Access', desc: 'Fine-grained RBAC with dedicated roles for analysts, SOC teams, admins, and researchers.', color: 'text-[var(--color-primary)]' },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[var(--color-surface)] grid-bg">
      {/* Navigation */}
      <nav className="glass-strong fixed top-0 left-0 right-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)] flex items-center justify-center">
              <Shield className="w-5 h-5 text-[var(--color-surface)]" />
            </div>
            <span className="text-lg font-bold text-[var(--color-text)]">ThreatLens AI</span>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/login" className="px-4 py-2 text-sm text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors">
              Sign In
            </Link>
            <Link href="/register" className="px-5 py-2 text-sm font-medium rounded-lg bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-accent)] text-[var(--color-surface)] hover:opacity-90 transition-opacity">
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 px-6 scan-line-bg">
        <div className="max-w-5xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass mb-8 animate-slide-up">
            <span className="w-2 h-2 rounded-full bg-[var(--color-accent)] animate-pulse-glow" />
            <span className="text-xs text-[var(--color-text-muted)]">AI-Powered Malware Detection Platform</span>
          </div>

          <h1 className="text-5xl md:text-7xl font-bold mb-6 animate-slide-up stagger-1" style={{ opacity: 0 }}>
            <span className="text-[var(--color-text)]">Detect Threats</span>
            <br />
            <span className="text-gradient">Before They Strike</span>
          </h1>

          <p className="text-lg text-[var(--color-text-muted)] max-w-2xl mx-auto mb-10 animate-slide-up stagger-2" style={{ opacity: 0 }}>
            ThreatLens AI analyzes suspicious files, classifies malware using machine learning,
            and provides real-time threat intelligence for your security operations.
          </p>

          <div className="flex items-center justify-center gap-4 animate-slide-up stagger-3" style={{ opacity: 0 }}>
            <Link
              href="/register"
              className="group px-8 py-3.5 rounded-xl font-semibold bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-accent)] text-[var(--color-surface)] hover:opacity-90 transition-all flex items-center gap-2"
            >
              Start Analyzing
              <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link
              href="/login"
              className="px-8 py-3.5 rounded-xl font-semibold glass hover:bg-white/10 transition-all text-[var(--color-text)]"
            >
              Sign In
            </Link>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-6 max-w-lg mx-auto mt-16 animate-slide-up stagger-4" style={{ opacity: 0 }}>
            {[
              { value: '99.2%', label: 'Detection Rate' },
              { value: '<5s', label: 'Analysis Time' },
              { value: '7+', label: 'Malware Classes' },
            ].map((stat) => (
              <div key={stat.label} className="text-center">
                <div className="text-2xl font-bold text-gradient">{stat.value}</div>
                <div className="text-xs text-[var(--color-text-muted)] mt-1">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-20 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-14">
            <h2 className="text-3xl font-bold text-[var(--color-text)] mb-3">Comprehensive Threat Detection</h2>
            <p className="text-[var(--color-text-muted)]">Everything you need to identify, classify, and respond to cyber threats.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {features.map((feature, i) => (
              <div
                key={feature.title}
                className={`group glass rounded-2xl p-6 hover:bg-white/5 transition-all duration-300 cursor-default animate-slide-up stagger-${i + 1}`}
                style={{ opacity: 0 }}
              >
                <div className={`w-11 h-11 rounded-xl bg-white/5 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform ${feature.color}`}>
                  <feature.icon className="w-5 h-5" />
                </div>
                <h3 className="text-lg font-semibold text-[var(--color-text)] mb-2">{feature.title}</h3>
                <p className="text-sm text-[var(--color-text-muted)] leading-relaxed">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-6">
        <div className="max-w-3xl mx-auto text-center glass rounded-3xl p-12 glow-cyan">
          <h2 className="text-3xl font-bold text-[var(--color-text)] mb-4">Ready to Secure Your Organization?</h2>
          <p className="text-[var(--color-text-muted)] mb-8">Start analyzing files and detecting threats with AI-powered classification.</p>
          <Link
            href="/register"
            className="inline-flex items-center gap-2 px-8 py-3.5 rounded-xl font-semibold bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-accent)] text-[var(--color-surface)]"
          >
            Get Started Free
            <ChevronRight className="w-4 h-4" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-[var(--color-border)] py-8 px-6">
        <div className="max-w-7xl mx-auto flex items-center justify-between text-sm text-[var(--color-text-muted)]">
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-[var(--color-primary)]" />
            <span>ThreatLens AI</span>
          </div>
          <span>© 2025 ThreatLens AI. Cybersecurity Intelligence Platform.</span>
        </div>
      </footer>
    </div>
  );
}
