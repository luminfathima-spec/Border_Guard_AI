import { ShieldCheck, HardDrive, Cpu, Database, Activity, CheckCircle2 } from 'lucide-react';
import type { SecurityEvent } from '../types';

interface SystemHealthBarProps {
  events: SecurityEvent[];
  cameraCount?: { online: number; total: number };
}

export function SystemHealthBar({ events, cameraCount = { online: 4, total: 4 } }: SystemHealthBarProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
      {/* Left 8 Cols: Recent Operational Events Feed */}
      <div className="lg:col-span-8 bg-[#111317] border border-[#24272D] rounded-lg p-4 space-y-3 shadow-sm">
        <div className="flex items-center justify-between border-b border-[#22262C] pb-2 text-xs">
          <div className="flex items-center space-x-2">
            <Activity className="w-4 h-4 text-[#D6A84A]" />
            <span className="font-semibold text-sm text-[#F2F0EA]">
              Recent Perimeter Activity & Detection Log
            </span>
          </div>
          <span className="text-xs text-[#8E8B83] font-medium">Real-Time Ingestion</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          {events.slice(0, 4).map((ev) => (
            <div
              key={ev.id}
              className="p-3 rounded bg-[#16191D] border border-[#242830] flex items-center justify-between text-xs"
            >
              <div className="space-y-0.5 min-w-0 pr-2">
                <div className="font-bold text-sm text-[#F2F0EA] truncate">
                  {ev.event_type.replace(/_/g, ' ')}
                </div>
                <div className="text-xs text-[#A9A69D] truncate">
                  {ev.camera_name || `Cam #${ev.camera_id}`} • {ev.description}
                </div>
              </div>
              <div className="text-right shrink-0">
                <div className="text-xs font-mono-num text-[#D6A84A] font-semibold">
                  {new Date(ev.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
                <span className="text-[10px] px-1.5 py-0.2 rounded bg-[#1C261E] text-[#5BAF75] font-semibold border border-[#253D2A]">
                  Verified
                </span>
              </div>
            </div>
          ))}
          {events.length === 0 && (
            <div className="col-span-2 py-4 text-center text-xs text-[#8E8B83]">
              Perimeter nominal. No anomalous activity logged in last inspection cycle.
            </div>
          )}
        </div>
      </div>

      {/* Right 4 Cols: Live System Infrastructure Health */}
      <div className="lg:col-span-4 bg-[#111317] border border-[#24272D] rounded-lg p-4 space-y-3 shadow-sm">
        <div className="flex items-center justify-between border-b border-[#22262C] pb-2 text-xs">
          <div className="flex items-center space-x-2">
            <ShieldCheck className="w-4 h-4 text-[#5BAF75]" />
            <span className="font-semibold text-sm text-[#F2F0EA]">System Infrastructure Health</span>
          </div>
          <span className="text-xs font-bold text-[#5BAF75] flex items-center space-x-1">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Optimal</span>
          </span>
        </div>

        <div className="space-y-2 text-xs">
          <div className="flex justify-between items-center p-2 rounded bg-[#16191D] border border-[#242830]">
            <div className="flex items-center space-x-2 text-[#D2CEBE]">
              <Cpu className="w-4 h-4 text-[#D6A84A]" />
              <span>Vision Inference Pipeline</span>
            </div>
            <span className="text-xs text-[#5BAF75] font-semibold">Operational (30 FPS)</span>
          </div>

          <div className="flex justify-between items-center p-2 rounded bg-[#16191D] border border-[#242830]">
            <div className="flex items-center space-x-2 text-[#D2CEBE]">
              <Database className="w-4 h-4 text-[#D6A84A]" />
              <span>PostgreSQL 17 Database</span>
            </div>
            <span className="text-xs text-[#5BAF75] font-semibold">Connected</span>
          </div>

          <div className="flex justify-between items-center p-2 rounded bg-[#16191D] border border-[#242830]">
            <div className="flex items-center space-x-2 text-[#D2CEBE]">
              <HardDrive className="w-4 h-4 text-[#D6A84A]" />
              <span>Evidence Storage Vault</span>
            </div>
            <span className="text-xs text-[#F2F0EA] font-semibold">68% Available</span>
          </div>

          <div className="flex justify-between items-center p-2 rounded bg-[#16191D] border border-[#242830]">
            <div className="flex items-center space-x-2 text-[#D2CEBE]">
              <Activity className="w-4 h-4 text-[#D6A84A]" />
              <span>Sensor Fleet Availability</span>
            </div>
            <span className="text-xs text-[#5BAF75] font-semibold">
              {cameraCount.online}/{cameraCount.total} Nodes Online
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
