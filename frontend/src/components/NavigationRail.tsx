import {
  Compass, Eye, Camera, ShieldAlert,
  Bell, AlertTriangle, FileText, FolderArchive,
  Bot, BarChart3, ChevronLeft, ChevronRight
} from 'lucide-react';
import { useState } from 'react';

interface NavigationRailProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  alertCount?: number;
  incidentCount?: number;
}

export function NavigationRail({
  activeTab,
  setActiveTab,
  alertCount = 0,
  incidentCount = 0,
}: NavigationRailProps) {
  const [collapsed, setCollapsed] = useState(false);

  const navItems = [
    { id: 'overview', label: 'Overview', icon: Compass },
    { id: 'live-surveillance', label: 'Live Surveillance', icon: Eye },
    { id: 'border-zones', label: 'Border Zones', icon: ShieldAlert },
    { id: 'cameras', label: 'Cameras', icon: Camera },
    { id: 'events', label: 'Events', icon: Bell },
    { id: 'alerts', label: 'Alerts', icon: AlertTriangle, badge: alertCount },
    { id: 'incidents', label: 'Incidents', icon: FileText, badge: incidentCount },
    { id: 'evidence', label: 'Evidence', icon: FolderArchive },
    { id: 'ai-analyst', label: 'AI Analyst', icon: Bot },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
  ];

  return (
    <aside
      className={`bg-white border-r border-[#E5E1EE] flex flex-col justify-between transition-all duration-200 select-none z-20 shrink-0 ${
        collapsed ? 'w-16' : 'w-60'
      }`}
    >
      <div className="py-3 space-y-1">
        <div className="px-5 pb-3 pt-1 flex items-center justify-between text-xs font-bold text-[#8E8899] uppercase tracking-wider">
          {!collapsed && <span>Command Modules</span>}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="p-1.5 rounded-md hover:bg-[#F0EDFD] text-[#8E8899] hover:text-[#7C5CFC] transition ml-auto"
            title={collapsed ? 'Expand navigation' : 'Collapse navigation'}
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive =
            activeTab === item.id ||
            (activeTab === 'dashboard' && item.id === 'overview') ||
            (activeTab === 'monitoring' && item.id === 'live-surveillance') ||
            (activeTab === 'ai-assistant' && item.id === 'ai-analyst');

          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              title={collapsed ? item.label : undefined}
              className={`w-full flex items-center px-5 py-3 text-sm transition-colors relative ${
                isActive
                  ? 'bg-[#F0EDFD] text-[#4328A8] font-bold border-l-4 border-[#7C5CFC]'
                  : 'text-[#625D6D] font-medium hover:text-[#211D2B] hover:bg-[#FAF9FD]'
              }`}
            >
              <Icon
                className={`w-5 h-5 shrink-0 ${
                  isActive ? 'text-[#7C5CFC]' : 'text-[#8E8899]'
                }`}
              />
              {!collapsed && (
                <span className="ml-3.5 truncate text-[14px]">
                  {item.label}
                </span>
              )}

              {item.badge !== undefined && item.badge > 0 && (
                <span
                  className={`ml-auto text-xs font-bold px-2 py-0.5 rounded-full ${
                    item.id === 'incidents'
                      ? 'bg-[#FEE2E2] text-[#B91C1C] border border-[#FCA5A5]'
                      : 'bg-[#FEF3C7] text-[#B45309] border border-[#FCD34D]'
                  } ${collapsed ? 'absolute top-2 right-2 text-[10px] px-1' : ''}`}
                >
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Bottom Telemetry Info Card */}
      {!collapsed && (
        <div className="p-4 m-3.5 rounded-xl bg-[#FAF9FD] border border-[#E5E1EE] text-xs text-[#625D6D] space-y-2 shadow-2xs">
          <div className="flex justify-between items-center text-xs">
            <span className="text-[#8E8899] font-medium">Surveillance:</span>
            <span className="text-[#16A34A] font-bold">Active (30 FPS)</span>
          </div>
          <div className="flex justify-between items-center text-xs">
            <span className="text-[#8E8899] font-medium">Vision Engine:</span>
            <span className="text-[#211D2B] font-bold">YOLOv8 Edge</span>
          </div>
          <div className="flex justify-between items-center text-xs">
            <span className="text-[#8E8899] font-medium">Intelligence:</span>
            <span className="text-[#7C5CFC] font-bold">Gemini 2.5 Flash</span>
          </div>
        </div>
      )}
    </aside>
  );
}
