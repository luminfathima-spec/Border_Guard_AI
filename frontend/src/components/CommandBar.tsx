import { useState, useEffect } from 'react';
import { Shield, Radio, LogOut, User as UserIcon, Bell, ChevronDown } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { StatusIndicator } from './StatusIndicator';

interface CommandBarProps {
  onNavigateAlerts?: () => void;
  activeAlertCount?: number;
  incidentCount?: number;
  cameraCount?: { online: number; total: number };
}

export function CommandBar({
  onNavigateAlerts,
  activeAlertCount = 0,
  incidentCount = 0,
  cameraCount = { online: 4, total: 4 },
}: CommandBarProps) {
  const { user, logout } = useAuth();
  const [timeStr, setTimeStr] = useState<string>('');
  const [sector, setSector] = useState<string>('Sector 07 — Northern Perimeter');
  const [sectorMenuOpen, setSectorMenuOpen] = useState(false);

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const utc = now.toISOString().replace('T', ' ').substring(0, 19) + ' UTC';
      setTimeStr(utc);
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const sectors = [
    'Sector 07 — Northern Perimeter',
    'Sector 04 — Eastern Gate Outpost',
    'Sector 09 — Riverine Sector',
    'All Border Sectors (Unified)',
  ];

  return (
    <header className="h-16 bg-white border-b border-[#E5E1EE] px-4 md:px-6 flex items-center justify-between z-30 select-none shadow-xs">
      {/* Left: Brand Identity */}
      <div className="flex items-center space-x-3.5 shrink-0">
        <div className="w-10 h-10 rounded-lg bg-[#F0EDFD] border border-[#DCD4FB] flex items-center justify-center text-[#7C5CFC] shadow-xs">
          <Shield className="w-5 h-5" />
        </div>
        <div>
          <div className="flex items-center space-x-2.5">
            <span className="font-extrabold text-lg tracking-tight text-[#211D2B]">
              SENTINEL
            </span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-[#F0EDFD] border border-[#DCD4FB] text-[#7C5CFC] font-bold">
              SIH 2026
            </span>
          </div>
          <p className="text-xs text-[#625D6D] font-medium">
            Intelligent Video Analytics Platform for Border Surveillance
          </p>
        </div>
      </div>

      {/* Center: Sector & Clear Status Indicators */}
      <div className="hidden lg:flex items-center space-x-4">
        {/* Sector Dropdown */}
        <div className="relative">
          <button
            onClick={() => setSectorMenuOpen(!sectorMenuOpen)}
            className="flex items-center space-x-2 px-3.5 py-1.5 rounded-lg bg-[#FAF9FD] border border-[#E5E1EE] hover:border-[#C4BAE0] text-[#211D2B] transition"
          >
            <Radio className="w-4 h-4 text-[#16A34A] animate-pulse" />
            <span className="text-[#8E8899] text-xs font-bold uppercase tracking-wider">Sector:</span>
            <span className="font-bold text-sm text-[#211D2B]">{sector}</span>
            <ChevronDown className="w-4 h-4 text-[#8E8899] ml-1" />
          </button>

          {sectorMenuOpen && (
            <div className="absolute top-full mt-1.5 left-0 w-72 bg-white border border-[#E5E1EE] rounded-lg shadow-xl py-1 z-50 animate-fade-in">
              {sectors.map((s) => (
                <div
                  key={s}
                  onClick={() => {
                    setSector(s);
                    setSectorMenuOpen(false);
                  }}
                  className="px-4 py-2.5 hover:bg-[#F0EDFD] text-[#211D2B] hover:text-[#7C5CFC] cursor-pointer text-sm font-semibold transition"
                >
                  {s}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Status Badges */}
        <div className="flex items-center space-x-3 px-3.5 py-1.5 rounded-lg bg-[#FAF9FD] border border-[#E5E1EE] text-sm">
          <div className="flex items-center space-x-1.5">
            <span className="text-[#8E8899] font-medium text-xs">CAMERAS:</span>
            <span className="text-[#16A34A] font-bold font-mono-num">{cameraCount.online}/{cameraCount.total} Online</span>
          </div>
          <span className="text-[#E5E1EE]">|</span>
          <div className="flex items-center space-x-1.5">
            <span className="text-[#8E8899] font-medium text-xs">ALERTS:</span>
            <span className={activeAlertCount > 0 ? 'text-[#B45309] font-bold font-mono-num' : 'text-[#625D6D] font-mono-num'}>
              {activeAlertCount} Active
            </span>
          </div>
          <span className="text-[#E5E1EE]">|</span>
          <div className="flex items-center space-x-1.5">
            <span className="text-[#8E8899] font-medium text-xs">CASES:</span>
            <span className={incidentCount > 0 ? 'text-[#7C5CFC] font-bold font-mono-num' : 'text-[#625D6D] font-mono-num'}>
              {incidentCount} Open
            </span>
          </div>
          <span className="text-[#E5E1EE]">|</span>
          <div className="flex items-center space-x-1.5">
            <StatusIndicator status="ONLINE" pulse={true} size="sm" />
            <span className="text-[#16A34A] font-bold text-xs uppercase tracking-wide">Surveillance Active</span>
          </div>
        </div>
      </div>

      {/* Right: UTC Time, User Info & Logout */}
      <div className="flex items-center space-x-3">
        <div className="hidden xl:block text-[#625D6D] font-mono-num bg-[#FAF9FD] px-3.5 py-1.5 rounded-lg border border-[#E5E1EE] text-xs font-semibold">
          {timeStr}
        </div>

        {activeAlertCount > 0 && onNavigateAlerts && (
          <button
            onClick={onNavigateAlerts}
            className="p-2 rounded-lg bg-[#FEF3C7] border border-[#FCD34D] text-[#B45309] hover:bg-[#FDE68A] transition relative shadow-xs"
            title="View Active Alerts"
          >
            <Bell className="w-4 h-4" />
            <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-[#D97706] animate-ping" />
            <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-[#D97706]" />
          </button>
        )}

        <div className="flex items-center space-x-2.5 pl-2.5 border-l border-[#E5E1EE]">
          <div className="w-8 h-8 rounded-lg bg-[#F0EDFD] border border-[#DCD4FB] flex items-center justify-center text-[#7C5CFC]">
            <UserIcon className="w-4 h-4" />
          </div>
          <div className="hidden sm:block text-left">
            <div className="text-sm font-bold text-[#211D2B]">
              {user?.name?.split(' ')[0] || 'Commander'}
            </div>
            <div className="text-xs text-[#8E8899] capitalize font-medium">
              {user?.role?.toLowerCase()?.replace('_', ' ') || 'Security Commander'}
            </div>
          </div>

          <button
            onClick={logout}
            title="Sign out of Workstation"
            className="p-2 rounded-lg bg-[#FAF9FD] hover:bg-[#FEE2E2] border border-[#E5E1EE] text-[#625D6D] hover:text-[#B91C1C] transition ml-1"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
}
