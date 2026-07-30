'use client';

import { useState, useCallback } from 'react';
import { Upload, FileWarning, Shield, Hash, AlertTriangle, CheckCircle2, XCircle, Loader2, ChevronDown, ChevronUp } from 'lucide-react';
import api from '@/lib/api';
import toast from 'react-hot-toast';
import type { FileAnalysis } from '@/types';

export default function UploadPage() {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [result, setResult] = useState<FileAnalysis | null>(null);
  const [showDetails, setShowDetails] = useState(false);

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) await uploadFile(file);
  }, []);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) await uploadFile(file);
  };

  const uploadFile = async (file: File) => {
    setIsUploading(true);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const uploadRes = await api.post('/files/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      // Fetch full analysis
      const analysisRes = await api.get(`/files/${uploadRes.data.id}`);
      setResult(analysisRes.data);
      toast.success('Analysis complete!');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const riskColor = (level: string | null) => {
    switch (level) {
      case 'Critical': return 'text-[var(--color-danger)]';
      case 'High': return 'text-orange-400';
      case 'Medium': return 'text-[var(--color-warning)]';
      case 'Low': return 'text-[var(--color-primary)]';
      default: return 'text-[var(--color-accent)]';
    }
  };

  const riskBg = (level: string | null) => {
    switch (level) {
      case 'Critical': return 'bg-risk-critical border';
      case 'High': return 'bg-risk-high border';
      case 'Medium': return 'bg-risk-medium border';
      case 'Low': return 'bg-risk-low border';
      default: return 'bg-risk-clean border';
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold text-[var(--color-text)]">Upload & Analyze</h1>
        <p className="text-sm text-[var(--color-text-muted)] mt-1">Upload suspicious files for comprehensive static analysis and malware classification.</p>
      </div>

      {/* Upload Zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={`relative glass rounded-2xl p-12 text-center transition-all cursor-pointer ${
          isDragging ? 'border-[var(--color-primary)] bg-[var(--color-primary)]/5 glow-cyan' : 'hover:bg-white/3'
        } ${isUploading ? 'pointer-events-none opacity-60' : ''}`}
      >
        <input
          type="file"
          onChange={handleFileSelect}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          disabled={isUploading}
          accept=".exe,.dll,.pdf,.doc,.docx,.xls,.xlsx,.zip,.rar,.js,.ps1,.bat,.cmd,.vbs,.py"
        />

        {isUploading ? (
          <div className="space-y-4">
            <Loader2 className="w-12 h-12 text-[var(--color-primary)] mx-auto animate-spin" />
            <p className="text-[var(--color-text)]">Analyzing file...</p>
            <p className="text-xs text-[var(--color-text-muted)]">Running static analysis, YARA scanning, and risk assessment</p>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="w-16 h-16 rounded-2xl bg-[var(--color-primary)]/10 flex items-center justify-center mx-auto">
              <Upload className="w-7 h-7 text-[var(--color-primary)]" />
            </div>
            <div>
              <p className="text-lg font-medium text-[var(--color-text)]">Drop file here or click to upload</p>
              <p className="text-sm text-[var(--color-text-muted)] mt-1">Supports: EXE, DLL, PDF, DOC, ZIP, scripts — Max 50MB</p>
            </div>
          </div>
        )}
      </div>

      {/* Results */}
      {result && (
        <div className="space-y-4 animate-slide-up">
          {/* Risk Score Banner */}
          <div className={`rounded-2xl p-6 ${riskBg(result.risk_level)}`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                {result.risk_level === 'Clean' ? (
                  <CheckCircle2 className="w-10 h-10 text-[var(--color-accent)]" />
                ) : (
                  <AlertTriangle className={`w-10 h-10 ${riskColor(result.risk_level)}`} />
                )}
                <div>
                  <h3 className="text-lg font-bold text-[var(--color-text)]">{result.original_name}</h3>
                  <p className="text-sm text-[var(--color-text-muted)]">
                    {result.file_type} • {(result.file_size / 1024).toFixed(1)} KB
                  </p>
                </div>
              </div>
              <div className="text-right">
                <div className={`text-4xl font-bold ${riskColor(result.risk_level)}`}>
                  {result.risk_score?.toFixed(0)}
                </div>
                <div className={`text-sm font-medium ${riskColor(result.risk_level)}`}>
                  {result.risk_level} Risk
                </div>
              </div>
            </div>
          </div>

          {/* Hash Info */}
          <div className="glass rounded-2xl p-5">
            <h3 className="text-sm font-semibold text-[var(--color-text)] mb-3 flex items-center gap-2">
              <Hash className="w-4 h-4 text-[var(--color-primary)]" /> File Hashes
            </h3>
            <div className="space-y-2 font-mono text-xs">
              <div className="flex items-center gap-2">
                <span className="text-[var(--color-text-muted)] w-16">MD5</span>
                <span className="text-[var(--color-text)] bg-white/5 px-3 py-1.5 rounded-lg flex-1 break-all">{result.md5_hash}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[var(--color-text-muted)] w-16">SHA-256</span>
                <span className="text-[var(--color-text)] bg-white/5 px-3 py-1.5 rounded-lg flex-1 break-all">{result.sha256_hash}</span>
              </div>
            </div>
          </div>

          {/* YARA Matches */}
          {result.analysis?.yara_matches && result.analysis.yara_matches.length > 0 && (
            <div className="glass rounded-2xl p-5">
              <h3 className="text-sm font-semibold text-[var(--color-text)] mb-3 flex items-center gap-2">
                <Shield className="w-4 h-4 text-[var(--color-warning)]" /> YARA Rule Matches ({result.analysis.yara_matches.length})
              </h3>
              <div className="space-y-2">
                {result.analysis.yara_matches.map((match, i) => (
                  <div key={i} className="flex items-center justify-between bg-white/3 rounded-xl p-3">
                    <div>
                      <span className="text-sm font-medium text-[var(--color-text)]">{match.rule_name}</span>
                      <p className="text-xs text-[var(--color-text-muted)]">{match.description}</p>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded-lg font-medium ${
                      match.severity === 'critical' ? 'bg-[var(--color-danger)]/15 text-[var(--color-danger)]' :
                      match.severity === 'high' ? 'bg-orange-500/15 text-orange-400' :
                      'bg-[var(--color-warning)]/15 text-[var(--color-warning)]'
                    }`}>{match.severity}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Behavioral Indicators */}
          {result.analysis?.behavioral_indicators && result.analysis.behavioral_indicators.length > 0 && (
            <div className="glass rounded-2xl p-5">
              <h3 className="text-sm font-semibold text-[var(--color-text)] mb-3 flex items-center gap-2">
                <FileWarning className="w-4 h-4 text-[var(--color-danger)]" /> Behavioral Indicators
              </h3>
              <div className="flex flex-wrap gap-2">
                {result.analysis.behavioral_indicators.map((indicator, i) => (
                  <span key={i} className="text-xs bg-[var(--color-danger)]/10 text-[var(--color-danger)] px-3 py-1.5 rounded-lg">
                    {indicator}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Expandable Details */}
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="w-full glass rounded-xl p-3 flex items-center justify-center gap-2 text-sm text-[var(--color-text-muted)] hover:bg-white/5 transition-colors"
          >
            {showDetails ? 'Hide' : 'Show'} Full Analysis Details
            {showDetails ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>

          {showDetails && result.analysis && (
            <div className="space-y-4 animate-fade-in">
              {/* Suspicious APIs */}
              {result.analysis.suspicious_apis && result.analysis.suspicious_apis.length > 0 && (
                <div className="glass rounded-2xl p-5">
                  <h3 className="text-sm font-semibold text-[var(--color-text)] mb-3">Suspicious API Imports ({result.analysis.suspicious_apis.length})</h3>
                  <div className="space-y-1">
                    {result.analysis.suspicious_apis.map((api, i) => (
                      <div key={i} className="flex items-center gap-3 text-xs py-1.5">
                        <span className="font-mono text-[var(--color-warning)] w-40 flex-shrink-0">{api.function}</span>
                        <span className="text-[var(--color-text-muted)]">{api.description}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Suspicious URLs */}
              {result.analysis.suspicious_urls && result.analysis.suspicious_urls.length > 0 && (
                <div className="glass rounded-2xl p-5">
                  <h3 className="text-sm font-semibold text-[var(--color-text)] mb-3">Embedded URLs/IPs ({result.analysis.suspicious_urls.length})</h3>
                  <div className="space-y-1">
                    {result.analysis.suspicious_urls.map((url, i) => (
                      <div key={i} className="text-xs font-mono text-[var(--color-primary)] bg-white/3 rounded-lg px-3 py-2 break-all">{url}</div>
                    ))}
                  </div>
                </div>
              )}

              {/* Suspicious Strings */}
              {result.analysis.suspicious_strings && result.analysis.suspicious_strings.length > 0 && (
                <div className="glass rounded-2xl p-5">
                  <h3 className="text-sm font-semibold text-[var(--color-text)] mb-3">Suspicious Strings ({result.analysis.suspicious_strings.length})</h3>
                  <div className="max-h-48 overflow-y-auto space-y-1">
                    {result.analysis.suspicious_strings.slice(0, 20).map((str, i) => (
                      <div key={i} className="text-xs font-mono text-[var(--color-text-muted)] bg-white/3 rounded px-2 py-1 break-all">{str}</div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
