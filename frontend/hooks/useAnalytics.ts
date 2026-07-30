/**
 * ThreatLens AI — Analytics Hook (Zustand)
 * Analytics data fetching and state management.
 */

import { create } from 'zustand';
import api from '@/lib/api';
import type { OverviewStats, MalwareDistribution, ThreatTrend, RiskDistribution } from '@/types';

interface AnalyticsState {
  overview: OverviewStats | null;
  malwareDistribution: MalwareDistribution | null;
  trends: ThreatTrend[];
  riskDistribution: RiskDistribution | null;
  topThreats: { class: string; count: number }[];
  isLoading: boolean;
  error: string | null;

  fetchOverview: () => Promise<void>;
  fetchMalwareDistribution: () => Promise<void>;
  fetchTrends: (period?: string) => Promise<void>;
  fetchRiskDistribution: () => Promise<void>;
  fetchTopThreats: () => Promise<void>;
  fetchAll: () => Promise<void>;
  clearError: () => void;
}

export const useAnalytics = create<AnalyticsState>((set) => ({
  overview: null,
  malwareDistribution: null,
  trends: [],
  riskDistribution: null,
  topThreats: [],
  isLoading: false,
  error: null,

  fetchOverview: async () => {
    try {
      const response = await api.get<OverviewStats>('/analytics/overview');
      set({ overview: response.data });
    } catch (error: any) {
      set({ error: error.response?.data?.detail || 'Failed to fetch overview' });
    }
  },

  fetchMalwareDistribution: async () => {
    try {
      const response = await api.get<MalwareDistribution>('/analytics/malware-distribution');
      set({ malwareDistribution: response.data });
    } catch {
      // Silent fail
    }
  },

  fetchTrends: async (period = '30d') => {
    try {
      const response = await api.get<ThreatTrend[]>(`/analytics/trends?period=${period}`);
      set({ trends: response.data });
    } catch {
      // Silent fail
    }
  },

  fetchRiskDistribution: async () => {
    try {
      const response = await api.get<RiskDistribution>('/analytics/risk-distribution');
      set({ riskDistribution: response.data });
    } catch {
      // Silent fail
    }
  },

  fetchTopThreats: async () => {
    try {
      const response = await api.get('/analytics/top-threats');
      set({ topThreats: response.data });
    } catch {
      // Silent fail
    }
  },

  fetchAll: async () => {
    set({ isLoading: true, error: null });
    const store = useAnalytics.getState();
    await Promise.allSettled([
      store.fetchOverview(),
      store.fetchMalwareDistribution(),
      store.fetchTrends(),
      store.fetchRiskDistribution(),
      store.fetchTopThreats(),
    ]);
    set({ isLoading: false });
  },

  clearError: () => set({ error: null }),
}));
