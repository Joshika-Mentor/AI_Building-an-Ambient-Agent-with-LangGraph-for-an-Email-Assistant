/**
 * ThreatLens AI — Files Hook (Zustand)
 * File upload, analysis listing, and management state.
 */

import { create } from 'zustand';
import api from '@/lib/api';
import type { FileAnalysis, FileListResponse } from '@/types';

interface FilesState {
  files: FileAnalysis[];
  total: number;
  page: number;
  pageSize: number;
  isLoading: boolean;
  isUploading: boolean;
  uploadProgress: number;
  error: string | null;

  fetchFiles: (page?: number, filters?: Record<string, string>) => Promise<void>;
  uploadFile: (file: File) => Promise<FileAnalysis | null>;
  getAnalysis: (id: number) => Promise<FileAnalysis | null>;
  clearError: () => void;
}

export const useFiles = create<FilesState>((set, get) => ({
  files: [],
  total: 0,
  page: 1,
  pageSize: 20,
  isLoading: false,
  isUploading: false,
  uploadProgress: 0,
  error: null,

  fetchFiles: async (page = 1, filters = {}) => {
    set({ isLoading: true, error: null });
    try {
      const params = new URLSearchParams({ page: String(page), page_size: '20', ...filters });
      const response = await api.get<FileListResponse>(`/files/?${params}`);
      set({
        files: response.data.files,
        total: response.data.total,
        page: response.data.page,
        pageSize: response.data.page_size,
        isLoading: false,
      });
    } catch (error: any) {
      set({ error: error.response?.data?.detail || 'Failed to fetch files', isLoading: false });
    }
  },

  uploadFile: async (file: File) => {
    set({ isUploading: true, uploadProgress: 0, error: null });
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await api.post('/files/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          const progress = progressEvent.total
            ? Math.round((progressEvent.loaded * 100) / progressEvent.total)
            : 0;
          set({ uploadProgress: progress });
        },
      });

      set({ isUploading: false, uploadProgress: 100 });

      // Refresh list
      get().fetchFiles();

      return response.data;
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'Upload failed',
        isUploading: false,
        uploadProgress: 0,
      });
      return null;
    }
  },

  getAnalysis: async (id: number) => {
    try {
      const response = await api.get<FileAnalysis>(`/files/${id}`);
      return response.data;
    } catch {
      return null;
    }
  },

  clearError: () => set({ error: null }),
}));
