/**
 * ThreatLens AI — Alerts Hook (Zustand)
 * Alert state management: listing, acknowledging, resolving.
 */

import { create } from 'zustand';
import api from '@/lib/api';
import type { Alert, AlertListResponse, AlertStats } from '@/types';

interface AlertsState {
  alerts: Alert[];
  total: number;
  page: number;
  unreadCount: number;
  stats: AlertStats | null;
  isLoading: boolean;
  error: string | null;

  fetchAlerts: (page?: number, filters?: Record<string, string>) => Promise<void>;
  fetchStats: () => Promise<void>;
  acknowledgeAlert: (id: number) => Promise<void>;
  resolveAlert: (id: number) => Promise<void>;
  clearError: () => void;
}

export const useAlerts = create<AlertsState>((set, get) => ({
  alerts: [],
  total: 0,
  page: 1,
  unreadCount: 0,
  stats: null,
  isLoading: false,
  error: null,

  fetchAlerts: async (page = 1, filters = {}) => {
    set({ isLoading: true, error: null });
    try {
      const params = new URLSearchParams({ page: String(page), page_size: '20', ...filters });
      const response = await api.get<AlertListResponse>(`/alerts/?${params}`);
      set({
        alerts: response.data.alerts,
        total: response.data.total,
        page: response.data.page,
        unreadCount: response.data.unread_count,
        isLoading: false,
      });
    } catch (error: any) {
      set({ error: error.response?.data?.detail || 'Failed to fetch alerts', isLoading: false });
    }
  },

  fetchStats: async () => {
    try {
      const response = await api.get<AlertStats>('/alerts/stats');
      set({ stats: response.data });
    } catch {
      // Silent fail for stats
    }
  },

  acknowledgeAlert: async (id: number) => {
    try {
      await api.put(`/alerts/${id}/acknowledge`);
      // Refresh
      get().fetchAlerts(get().page);
      get().fetchStats();
    } catch (error: any) {
      set({ error: error.response?.data?.detail || 'Failed to acknowledge alert' });
    }
  },

  resolveAlert: async (id: number) => {
    try {
      await api.put(`/alerts/${id}/resolve`);
      get().fetchAlerts(get().page);
      get().fetchStats();
    } catch (error: any) {
      set({ error: error.response?.data?.detail || 'Failed to resolve alert' });
    }
  },

  clearError: () => set({ error: null }),
}));
