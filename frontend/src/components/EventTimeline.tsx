import { Clock, ChevronRight, Activity, ShieldCheck, Database, HardDrive, Cpu } from 'lucide-react';
import type { SecurityEvent } from '../types';
import { SeverityBadge } from './SeverityBadge';

interface EventTimelineProps {
  events: SecurityEvent[];
  onSelectEvent?: (event: SecurityEvent) => void;
  cameraCount?: { online: number; total: number };
}

export function EventTimeline({
  events,
  onSelectEvent,
  cameraCount = { online: 4, total: 4 },
}: EventTimelineProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
      {/* Left 8 Cols: Real-Time Event Timeline */}
      <div className="lg:col-span-8 rounded-lg bg-[#12151A] border border-[#262B35] p-4 space-y-3.5 shadow-sm">
        <div className="flex items-center justify-between border-b border-[#20252F] pb-2">
          <div className="flex items-center space-x-2 text-sm font-bold text-[#F5F3ED]">
            <Clock className="w-4 h-4 text-[#D6A84A]" />
            <span>Perimeter Operations Activity Timeline</span>
          </div>
          <span className="text-xs text-[#8E8A80] font-medium">Continuous Ingestion</span>
        </div>

        <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
          {events.length === 0 ? (
            <div className="py-6 text-center text-[#8E8A80] text-xs">
              No recent perimeter events recorded in current patrol cycle.
            </div>
          ) : (
            events.slice(0, 6).map((ev) => (
              <div
                key={ev.id}
                onClick={() => onSelectEvent && onSelectEvent(ev)}
                className="p-2.5 rounded-md bg-[#161A21] border border-[#242933] hover:border-[#384152] flex items-center justify-between text-xs cursor-pointer transition"
              >
                <div className="flex items-center space-x-3 truncate pr-2">
                  <SeverityBadge severity={ev.severity} size="sm" />
                  <span className="font-bold text-[#F5F3ED] text-xs truncate">
                    {ev.event_type.replace(/_/g, ' ')}
                  </span>
                  <span className="text-[#A39E93] text-xs truncate hidden sm:inline">
                    {ev.description}
                  </span>
                </div>

                <div className="flex items-center space-x-3 shrink-0">
                  <span className="text-[#8E8A80] text-xs">{ev.camera_name || `Cam #${ev.camera_id}`}</span>
                  <span className="text-[#D6A84A] font-mono-num text-xs font-semibold">
                    {new Date(ev.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                  <ChevronRight className="w-3.5 h-3.5 text-[#8E8A80]" />
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Right 4 Cols: System Infrastructure Health */}
      <div className="lg:col-span-4 rounded-lg bg-[#12151A] border border-[#262B35] p-4 space-y-3.5 shadow-sm">
        <div className="flex items-center justify-between border-b border-[#20252F] pb-2">
          <div className="flex items-center space-x-2 text-sm font-bold text-[#F5F3ED]">
            <ShieldCheck className="w-4 h-4 text-[#5BAF75]" />
            <span>Platform Health & Infrastructure</span>
          </div>
          <span className="text-xs text-[#5BAF75] font-bold">Optimal</span>
        </div>

        <div className="space-y-2 text-xs">
          <div className="flex justify-between items-center p-2 rounded bg-[#161A21] border border-[#242933]">
            <div className="flex items-center space-x-2 text-[#DCD7CB]">
              <Cpu className="w-4 h-4 text-[#D6A84A]" />
              <span>Vision Inference Pipeline</span>
            </div>
            <span className="text-xs text-[#5BAF75] font-bold">Operational (30 FPS)</span>
          </div>

          <div className="flex justify-between items-center p-2 rounded bg-[#161A21] border border-[#242933]">
            <div className="flex items-center space-x-2 text-[#DCD7CB]">
              <Database className="w-4 h-4 text-[#D6A84A]" />
              <span>PostgreSQL 17 Database</span>
            </div>
            <span className="text-xs text-[#5BAF75] font-bold">Connected</span>
          </div>

          <div className="flex justify-between items-center p-2 rounded bg-[#161A21] border border-[#242933]">
            <div className="flex items-center space-x-2 text-[#DCD7CB]">
              <HardDrive className="w-4 h-4 text-[#D6A84A]" />
              <span>Evidence Storage Vault</span>
            </div>
            <span className="text-xs text-[#F5F3ED] font-semibold">68% Available</span>
          </div>

          <div className="flex justify-between items-center p-2 rounded bg-[#161A21] border border-[#242933]">
            <div className="flex items-center space-x-2 text-[#DCD7CB]">
              <Activity className="w-4 h-4 text-[#D6A84A]" />
              <span>Sensor Fleet Availability</span>
            </div>
            <span className="text-xs text-[#5BAF75] font-bold">
              {cameraCount.online}/{cameraCount.total} Online
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
