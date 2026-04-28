'use client';

import React from 'react';
import { useDashboardStore, type DashboardView } from '@/store/dashboard';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  LayoutDashboard, Monitor, Globe, ShieldAlert, Brain, Radio,
  Activity, ChevronLeft, ChevronRight, Shield, Menu, X, Settings, Bot
} from 'lucide-react';
import OverviewPanel from '@/components/dashboard/overview-panel';
import DevicesPanel from '@/components/dashboard/devices-panel';
import TrafficPanel from '@/components/dashboard/traffic-panel';
import DNSPanel from '@/components/dashboard/dns-panel';
import AlertsPanel from '@/components/dashboard/alerts-panel';
import AnomaliesPanel from '@/components/dashboard/anomalies-panel';
import PacketsPanel from '@/components/dashboard/packets-panel';
import SettingsPanel from '@/components/dashboard/settings-panel';
import AiChatSidebar from '@/components/dashboard/ai-chat-sidebar';
import { API_BASE, authFetch } from '@/lib/api-config';

const navItems: Array<{
  id: DashboardView;
  label: string;
  icon: React.ReactNode;
  description: string;
}> = [
  { id: 'overview', label: 'Dashboard', icon: <LayoutDashboard className="h-4 w-4" />, description: 'System overview' },
  { id: 'packets', label: 'Live Capture', icon: <Radio className="h-4 w-4" />, description: 'Real-time packets' },
  { id: 'devices', label: 'Devices', icon: <Monitor className="h-4 w-4" />, description: 'Connected devices' },
  { id: 'traffic', label: 'Traffic', icon: <Activity className="h-4 w-4" />, description: 'Traffic analysis' },
  { id: 'dns', label: 'DNS', icon: <Globe className="h-4 w-4" />, description: 'DNS queries' },
  { id: 'alerts', label: 'Alerts', icon: <ShieldAlert className="h-4 w-4" />, description: 'Security alerts' },
  { id: 'anomalies', label: 'Anomaly Detection', icon: <Brain className="h-4 w-4" />, description: 'ML anomalies' },
  { id: 'settings', label: 'Settings', icon: <Settings className="h-4 w-4" />, description: 'Configuration' },
];

function SidebarContent({ collapsed }: { collapsed: boolean }) {
  const { activeView, setActiveView, stats } = useDashboardStore();

  return (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className={cn("p-4 border-b border-border", collapsed ? "px-3" : "")}>
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-gradient-to-br from-emerald-500 to-cyan-500 flex-shrink-0">
            <Shield className="h-5 w-5 text-white" />
          </div>
          {!collapsed && (
            <div className="min-w-0">
              <div className="font-bold text-sm truncate">Data Leak Monitor</div>
              <div className="text-[10px] text-muted-foreground">Home Network Privacy</div>
            </div>
          )}
        </div>
      </div>

      {/* Status */}
      {!collapsed && stats && (
        <div className="px-4 py-3 border-b border-border">
          <div className="flex items-center gap-2 px-2 py-1.5 rounded-lg bg-emerald-500/5 border border-emerald-500/15">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse flex-shrink-0" />
            <span className="text-xs text-emerald-600 dark:text-emerald-400">
              Monitoring Active · {stats.onlineDevices} devices
            </span>
          </div>
          {stats.unresolvedAlerts > 0 && (
            <div className="flex items-center gap-2 px-2 py-1.5 mt-1.5 rounded-lg bg-red-500/5 border border-red-500/15">
              <ShieldAlert className="h-3 w-3 text-red-500 flex-shrink-0" />
              <span className="text-xs text-red-600 dark:text-red-400">
                {stats.unresolvedAlerts} unresolved alerts
              </span>
            </div>
          )}
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        {!collapsed && (
          <div className="text-[10px] uppercase tracking-wider text-muted-foreground px-3 mb-2 font-medium">Navigation</div>
        )}
        {navItems.map((item) => {
          const isActive = activeView === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveView(item.id)}
              className={cn(
                "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all text-left group",
                collapsed ? "justify-center px-2" : "",
                isActive
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground hover:bg-muted/70"
              )}
              title={collapsed ? item.label : undefined}
            >
              <span className={cn("flex-shrink-0", isActive ? "text-primary-foreground" : "")}>
                {item.icon}
              </span>
              {!collapsed && (
                <div className="min-w-0">
                  <div className="text-sm font-medium">{item.label}</div>
                  <div className={cn(
                    "text-[10px]",
                    isActive ? "text-primary-foreground/70" : "text-muted-foreground"
                  )}>
                    {item.description}
                  </div>
                </div>
              )}
            </button>
          );
        })}
      </nav>

      {/* Footer */}
      {!collapsed && (
        <div className="p-4 border-t border-border">
          <div className="text-[10px] text-muted-foreground text-center">
            Privacy-Safe · No Payload Storage
          </div>
        </div>
      )}
    </div>
  );
}

const viewComponents: Record<DashboardView, React.ComponentType> = {
  overview: OverviewPanel,
  devices: DevicesPanel,
  traffic: TrafficPanel,
  dns: DNSPanel,
  alerts: AlertsPanel,
  anomalies: AnomaliesPanel,
  packets: PacketsPanel,
  settings: SettingsPanel,
};

export default function Home() {
  const { activeView, sidebarOpen, setSidebarOpen, stats, setStats } = useDashboardStore();
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);

  // Fetch initial stats
  const fetchAll = React.useCallback(() => {
    authFetch(`${API_BASE}/api/stats`)
      .then(r => r.json())
      .then(setStats)
      .catch(() => {});
  }, [setStats]);

  React.useEffect(() => {
    fetchAll();
    
    // WebSocket for live updates
    let ws: WebSocket;
    let retryTimeout: NodeJS.Timeout;
    
    const connectWS = () => {
      const wsUrl = API_BASE.replace(/^http/, 'ws') + '/ws/stream';
      ws = new WebSocket(wsUrl);
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'update') {
            fetchAll(); // Refresh stats globally when new data arrives
          }
        } catch (e) {}
      };
      
      ws.onclose = () => {
        retryTimeout = setTimeout(connectWS, 5000);
      };
    };
    
    connectWS();
    
    return () => {
      clearTimeout(retryTimeout);
      if (ws) ws.close();
    };
  }, [fetchAll]);

  const ActivePanel = viewComponents[activeView];

  const currentNav = navItems.find(n => n.id === activeView);

  return (
    <div className="min-h-screen flex bg-background">
      {/* Desktop Sidebar */}
      <aside
        className={cn(
          "hidden md:flex flex-col border-r border-border bg-card transition-all duration-300 flex-shrink-0",
          sidebarOpen ? "w-[260px]" : "w-[68px]"
        )}
      >
        <SidebarContent collapsed={!sidebarOpen} />
      </aside>

      {/* Mobile Overlay */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div className="absolute inset-0 bg-black/50" onClick={() => setMobileMenuOpen(false)} />
          <aside className="absolute left-0 top-0 bottom-0 w-[280px] bg-card border-r border-border shadow-xl z-10">
            <div className="flex items-center justify-between p-3 border-b border-border">
              <span className="text-sm font-medium">Menu</span>
              <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => setMobileMenuOpen(false)}>
                <X className="h-4 w-4" />
              </Button>
            </div>
            <SidebarContent collapsed={false} />
          </aside>
        </div>
      )}

      {/* Main Content */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Top Bar */}
        <header className="h-14 border-b border-border bg-card/50 backdrop-blur-sm flex items-center justify-between px-4 sticky top-0 z-40">
          <div className="flex items-center gap-3">
            {/* Mobile menu button */}
            <Button variant="ghost" size="icon" className="md:hidden h-9 w-9" onClick={() => setMobileMenuOpen(true)}>
              <Menu className="h-4 w-4" />
            </Button>
            {/* Desktop collapse button */}
            <Button
              variant="ghost"
              size="icon"
              className="hidden md:flex h-9 w-9"
              onClick={() => setSidebarOpen(!sidebarOpen)}
            >
              {sidebarOpen ? <ChevronLeft className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
            </Button>
            <div>
              <h1 className="text-sm font-semibold flex items-center gap-2">
                {currentNav?.icon}
                {currentNav?.label}
              </h1>
              <p className="text-[10px] text-muted-foreground hidden sm:block">{currentNav?.description}</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Button 
              variant="outline" 
              size="sm" 
              className="hidden sm:flex gap-2 text-indigo-500 border-indigo-500/30 hover:bg-indigo-500/10"
              onClick={() => useDashboardStore.getState().setIsAiChatOpen(!useDashboardStore.getState().isAiChatOpen)}
            >
              <Bot className="h-4 w-4" /> AI Assistant
            </Button>
            {stats && (
              <>
                <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20">
                  <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  <span className="text-[11px] text-emerald-600 dark:text-emerald-400">Live</span>
                </div>
                <div className="hidden md:flex items-center gap-1.5 text-xs text-muted-foreground">
                  <Monitor className="h-3 w-3" />
                  <span>{stats.onlineDevices} devices</span>
                </div>
                {stats.unresolvedAlerts > 0 && (
                  <div className="flex items-center gap-1.5 text-xs">
                    <Badge variant="destructive" className="text-[10px] h-5 px-1.5">
                      {stats.unresolvedAlerts}
                    </Badge>
                  </div>
                )}
              </>
            )}
          </div>
        </header>

        {/* Page Content */}
        <div className="flex-1 p-4 md:p-6 overflow-y-auto">
          <ActivePanel />
        </div>
      </main>

      {/* AI Chat Sidebar */}
      <AiChatSidebar />
    </div>
  );
}
