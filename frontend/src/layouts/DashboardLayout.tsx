import type { ReactNode } from 'react';
import { CommandBar } from '../components/CommandBar';
import { NavigationRail } from '../components/NavigationRail';
import { EdgeSyncBanner } from '../components/EdgeSyncBanner';

interface DashboardLayoutProps {
  children: ReactNode;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  alertCount?: number;
  incidentCount?: number;
  cameraCount?: { online: number; total: number };
}

export function DashboardLayout({
  children,
  activeTab,
  setActiveTab,
  alertCount = 0,
  incidentCount = 0,
  cameraCount = { online: 4, total: 4 },
}: DashboardLayoutProps) {
  return (
    <div className="min-h-screen w-full bg-[#F6F5FA] text-[#211D2B] flex flex-col overflow-x-hidden font-sans select-none">
      {/* Top Header Command Bar */}
      <CommandBar
        onNavigateAlerts={() => setActiveTab('alerts')}
        activeAlertCount={alertCount}
        incidentCount={incidentCount}
        cameraCount={cameraCount}
      />

      {/* Main Center Area: Navigation Rail + Workstation Content */}
      <div className="flex-1 flex overflow-x-hidden">
        <NavigationRail
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          alertCount={alertCount}
          incidentCount={incidentCount}
        />

        {/* Scrollable Main Operations Workstation Area */}
        <main className="flex-1 min-w-0 overflow-y-auto p-4 sm:p-6 bg-[#F6F5FA]">
          <div className="w-full max-w-[1920px] mx-auto space-y-6">
            <EdgeSyncBanner />
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
