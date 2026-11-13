import { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { DashboardLayout } from './layouts/DashboardLayout';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { MonitoringPage } from './pages/MonitoringPage';
import { CamerasPage } from './pages/CamerasPage';
import { BorderZonesPage } from './pages/BorderZonesPage';
import { EventsPage } from './pages/EventsPage';
import { AlertsPage } from './pages/AlertsPage';
import { IncidentsPage } from './pages/IncidentsPage';
import { EvidencePage } from './pages/EvidencePage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { VideoManagementPage } from './pages/VideoManagementPage';
import { ReportsPage } from './pages/ReportsPage';
import { CopilotPage } from './pages/CopilotPage';
import { OfflineSyncPage } from './pages/OfflineSyncPage';
import { AuditSettingsPage } from './pages/AuditSettingsPage';
import { alertApi, incidentApi, cameraApi } from './services/sentinelApi';

function AppContent() {
  const { user, loading } = useAuth();
  const [activeTab, setActiveTab] = useState<string>('overview');
  const [alertCount, setAlertCount] = useState(0);
  const [incidentCount, setIncidentCount] = useState(0);
  const [cameraCount, setCameraCount] = useState({ online: 4, total: 4 });

  useEffect(() => {
    if (user) {
      const loadCounts = async () => {
        try {
          const [alerts, incidents, cameras] = await Promise.all([
            alertApi.list({ status: 'NEW' }),
            incidentApi.list(),
            cameraApi.list(),
          ]);
          setAlertCount(alerts.length);
          setIncidentCount(incidents.length);
          const online = cameras.filter((c) => c.status === 'ONLINE').length;
          setCameraCount({ online, total: cameras.length });
        } catch (e) {
          // Keep default counts if offline
        }
      };
      loadCounts();
      const interval = setInterval(loadCounts, 15000);
      return () => clearInterval(interval);
    }
  }, [user]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F6F5FA] flex flex-col items-center justify-center space-y-3 text-sm font-semibold text-[#625D6D]">
        <div className="w-9 h-9 rounded-full border-3 border-[#7C5CFC] border-t-transparent animate-spin"></div>
        <span className="tracking-wide">INITIALIZING SENTINEL BORDER INTELLIGENCE ENVIRONMENT...</span>
      </div>
    );
  }

  if (!user) {
    return <LoginPage />;
  }

  const renderActiveTab = () => {
    switch (activeTab) {
      case 'overview':
      case 'dashboard':
        return <DashboardPage onNavigate={setActiveTab} />;
      case 'cameras':
        return <CamerasPage />;
      case 'monitoring':
      case 'live-surveillance':
        return <MonitoringPage />;
      case 'events':
        return <EventsPage />;
      case 'incidents':
        return <IncidentsPage />;
      case 'reports':
        return <ReportsPage />;
      case 'copilot':
      case 'ai-analyst':
      case 'ai-assistant':
        return <CopilotPage />;
      case 'offline-sync':
      case 'edge-sync':
        return <OfflineSyncPage />;
      case 'audit-settings':
      case 'settings':
        return <AuditSettingsPage />;
      case 'videos':
        return <VideoManagementPage />;
      case 'border-zones':
        return <BorderZonesPage />;
      case 'alerts':
        return <AlertsPage />;
      case 'evidence':
        return <EvidencePage />;
      case 'analytics':
        return <AnalyticsPage />;
      default:
        return <DashboardPage onNavigate={setActiveTab} />;
    }
  };

  return (
    <DashboardLayout
      activeTab={activeTab}
      setActiveTab={setActiveTab}
      alertCount={alertCount}
      incidentCount={incidentCount}
      cameraCount={cameraCount}
    >
      {renderActiveTab()}
    </DashboardLayout>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
