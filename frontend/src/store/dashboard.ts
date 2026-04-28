import { create } from 'zustand';
import type { Device, TrafficRecord, Alert, DNSQuery, AnomalyEvent, NetworkStats, TimeSeriesPoint, TrafficByProtocol, TopDestination } from '@/lib/types';

export type DashboardView = 'overview' | 'devices' | 'traffic' | 'dns' | 'alerts' | 'anomalies' | 'packets' | 'settings';

interface DashboardState {
  // Navigation
  activeView: DashboardView;
  setActiveView: (view: DashboardView) => void;
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;

  // Data
  stats: NetworkStats | null;
  setStats: (stats: NetworkStats) => void;
  devices: Device[];
  setDevices: (devices: Device[]) => void;
  traffic: TrafficRecord[];
  setTraffic: (traffic: TrafficRecord[]) => void;
  alerts: Alert[];
  setAlerts: (alerts: Alert[]) => void;
  dnsQueries: DNSQuery[];
  setDnsQueries: (queries: DNSQuery[]) => void;
  anomalies: AnomalyEvent[];
  setAnomalies: (anomalies: AnomalyEvent[]) => void;
  realtimePackets: TrafficRecord[];
  addRealtimePackets: (packets: TrafficRecord[]) => void;
  clearRealtimePackets: () => void;
  trafficTimeSeries: TimeSeriesPoint[];
  setTrafficTimeSeries: (data: TimeSeriesPoint[]) => void;
  protocolDistribution: TrafficByProtocol[];
  setProtocolDistribution: (data: TrafficByProtocol[]) => void;
  topDestinations: TopDestination[];
  setTopDestinations: (data: TopDestination[]) => void;

  // UI State
  captureActive: boolean;
  setCaptureActive: (active: boolean) => void;
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
  
  // AI Assistant State
  aiProvider: 'openai' | 'gemini' | 'claude';
  setAiProvider: (provider: 'openai' | 'gemini' | 'claude') => void;
  aiApiKey: string;
  setAiApiKey: (key: string) => void;
  isAiChatOpen: boolean;
  setIsAiChatOpen: (open: boolean) => void;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  // Navigation
  activeView: 'overview',
  setActiveView: (view) => set({ activeView: view }),
  sidebarOpen: true,
  setSidebarOpen: (open) => set({ sidebarOpen: open }),

  // Data
  stats: null,
  setStats: (stats) => set({ stats }),
  devices: [],
  setDevices: (devices) => set({ devices }),
  traffic: [],
  setTraffic: (traffic) => set({ traffic }),
  alerts: [],
  setAlerts: (alerts) => set({ alerts }),
  dnsQueries: [],
  setDnsQueries: (queries) => set({ dnsQueries: queries }),
  anomalies: [],
  setAnomalies: (anomalies) => set({ anomalies }),
  realtimePackets: [],
  addRealtimePackets: (packets) =>
    set((state) => {
      const existingIds = new Set(state.realtimePackets.map(p => p.id));
      const now = Date.now();
      const newPackets = packets
        .filter(p => !existingIds.has(p.id))
        .map(p => ({ ...p, _clientTime: now }));
      if (newPackets.length === 0) return state;
      return {
        realtimePackets: [...newPackets, ...state.realtimePackets].slice(0, 500),
      };
    }),
  clearRealtimePackets: () => set({ realtimePackets: [] }),
  trafficTimeSeries: [],
  setTrafficTimeSeries: (data) => set({ trafficTimeSeries: data }),
  protocolDistribution: [],
  setProtocolDistribution: (data) => set({ protocolDistribution: data }),
  topDestinations: [],
  setTopDestinations: (data) => set({ topDestinations: data }),

  // UI State
  captureActive: true,
  setCaptureActive: (active) => set({ captureActive: active }),
  isLoading: false,
  setIsLoading: (loading) => set({ isLoading: loading }),

  // AI Assistant State
  aiProvider: (typeof window !== 'undefined' ? localStorage.getItem('ns_ai_provider') : 'gemini') as any || 'gemini',
  setAiProvider: (provider) => {
    if (typeof window !== 'undefined') localStorage.setItem('ns_ai_provider', provider);
    set({ aiProvider: provider });
  },
  aiApiKey: (typeof window !== 'undefined' ? localStorage.getItem('ns_ai_apikey') : '') || '',
  setAiApiKey: (key) => {
    if (typeof window !== 'undefined') localStorage.setItem('ns_ai_apikey', key);
    set({ aiApiKey: key });
  },
  isAiChatOpen: false,
  setIsAiChatOpen: (open) => set({ isAiChatOpen: open }),
}));
