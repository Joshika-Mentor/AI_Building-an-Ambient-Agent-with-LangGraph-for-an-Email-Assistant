'use client';

import React, { useState, useRef, useCallback } from 'react';
import { Upload, X, FileIcon, AlertCircle } from 'lucide-react';

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  accept?: string;
  maxSizeMB?: number;
  label?: string;
  hint?: string;
  disabled?: boolean;
  className?: string;
}

export default function FileUpload({
  onFileSelect,
  accept = '.exe,.dll,.pdf,.doc,.docx,.xls,.xlsx,.zip,.rar,.js,.ps1,.bat,.cmd,.vbs,.py',
  maxSizeMB = 50,
  label = 'Drop a suspicious file here, or click to browse',
  hint,
  disabled = false,
  className = '',
}: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const validateFile = useCallback(
    (file: File): boolean => {
      setError(null);
      if (file.size > maxSizeMB * 1024 * 1024) {
        setError(`File too large. Maximum: ${maxSizeMB}MB`);
        return false;
      }
      return true;
    },
    [maxSizeMB]
  );

  const handleFile = useCallback(
    (file: File) => {
      if (validateFile(file)) {
        setSelectedFile(file);
        onFileSelect(file);
      }
    },
    [validateFile, onFileSelect]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      if (disabled) return;
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [disabled, handleFile]
  );

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  const clearFile = () => {
    setSelectedFile(null);
    setError(null);
    if (inputRef.current) inputRef.current.value = '';
  };

  const formatSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className={className}>
      <div
        onDragOver={(e) => { e.preventDefault(); if (!disabled) setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => !disabled && inputRef.current?.click()}
        className={`
          relative border-2 border-dashed rounded-2xl p-8 text-center
          transition-all duration-300 cursor-pointer
          ${isDragging
            ? 'border-[var(--color-primary)] bg-[var(--color-primary)]/5 glow-cyan'
            : 'border-[var(--color-border)] hover:border-[var(--color-primary)]/50 hover:bg-white/[0.02]'
          }
          ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
          ${error ? 'border-[var(--color-danger)]/50' : ''}
        `}
      >
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          onChange={handleChange}
          className="hidden"
          disabled={disabled}
        />

        {selectedFile ? (
          <div className="flex items-center justify-center gap-3">
            <FileIcon className="w-8 h-8 text-[var(--color-primary)]" />
            <div className="text-left">
              <p className="text-sm font-medium text-[var(--color-text)]">{selectedFile.name}</p>
              <p className="text-xs text-[var(--color-text-muted)]">{formatSize(selectedFile.size)}</p>
            </div>
            <button
              onClick={(e) => { e.stopPropagation(); clearFile(); }}
              className="ml-2 p-1 rounded-lg hover:bg-white/10 text-[var(--color-text-muted)] hover:text-[var(--color-danger)] transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <>
            <Upload className={`w-10 h-10 mx-auto mb-3 ${isDragging ? 'text-[var(--color-primary)]' : 'text-[var(--color-text-muted)]/50'}`} />
            <p className="text-sm text-[var(--color-text-muted)]">{label}</p>
            {hint && <p className="text-xs text-[var(--color-text-muted)]/60 mt-1">{hint}</p>}
          </>
        )}
      </div>

      {error && (
        <div className="flex items-center gap-2 mt-2 text-xs text-[var(--color-danger)]">
          <AlertCircle className="w-3 h-3" />
          {error}
        </div>
      )}
    </div>
  );
}
