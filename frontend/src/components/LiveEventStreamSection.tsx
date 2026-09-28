import { Bell, ChevronRight, Activity, ShieldCheck, Database, HardDrive, Cpu, CheckCircle2 } from 'lucide-react';
import type { SecurityEvent } from '../types';
import { SeverityBadge } from './SeverityBadge';

interface LiveEventStreamSectionProps {
  events: SecurityEvent[];
  onSelectEvent?: (event: SecurityEvent) => void;
  onNavigateEvents?: () => void;
  cameraCount?: { online: number; total: number };
}

export function LiveEventStreamSection({
  events,
  onSelectEvent,
  onNavigateEvents,
  cameraCount = { online: 4, total: 4 },
}: LiveEventStreamSectionProps) {
  return (
    <div className="space-y-6 w-full">
      {/* SECTION 4: Live Event Stream */}
      <div className="w-full rounded-2xl bg-white border border-[#E5E1EE] p-6 sm:p-7 space-y-5 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#E5E1EE] pb-4">
          <div className="flex items-center space-x-3.5">
            <div className="w-10 h-10 rounded-xl bg-[#F0EDFD] border border-[#DCD4FB] flex items-center justify-center text-[#7C5CFC] shadow-xs">
              <Bell className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-3">
                <h2 className="font-extrabold text-xl text-[#211D2B]">Real-Time Security Event Stream</h2>
                <span className="text-xs px-3 py-0.5 rounded-full bg-[#F0EDFD] border border-[#DCD4FB] text-[#7C5CFC] font-bold">
                  {events.length} Events Logged
                </span>
              </div>
              <p className="text-sm text-[#625D6D] font-medium mt-0.5">
                Continuous chronological audit trail of AI perimeter detections, line crossings, and spatial triggers
              </p>
            </div>
          </div>

          {onNavigateEvents && (
            <button
              onClick={onNavigateEvents}
              className="text-sm text-[#7C5CFC] hover:text-[#6A46F9] font-bold flex items-center space-x-1.5 transition self-start sm:self-auto"
            >
              <span>Full Audit Ledger</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Events Timeline / List */}
        <div className="divide-y divide-[#E5E1EE]">
          {events.length === 0 ? (
            <div className="py-10 text-center text-[#625D6D] text-sm">
              No recent security events recorded in the current observation cycle.
            </div>
          ) : (
            events.slice(0, 6).map((ev) => (
              <div
                key={ev.id}
                onClick={() => onSelectEvent && onSelectEvent(ev)}
                className="py-4 px-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-[#FAF9FD] rounded-xl cursor-pointer transition"
              >
                <div className="flex items-center space-x-4 min-w-0">
                  <SeverityBadge severity={ev.severity} size="md" />
                  <div>
                    <span className="font-bold text-base text-[#211D2B] block">
                      {ev.event_type.replace(/_/g, ' ')}
                    </span>
                    <span className="text-sm text-[#625D6D] truncate max-w-xl block mt-0.5">
                      {ev.description}
                    </span>
                  </div>
                </div>

                <div className="flex items-center space-x-4 shrink-0 text-sm">
                  <span className="px-3 py-1 rounded-md bg-[#FAF9FD] border border-[#E5E1EE] text-[#4328A8] font-bold text-xs font-mono-num">
                    {ev.camera_name || `Camera #${ev.camera_id}`}
                  </span>
                  <span className="font-extrabold text-[#16A34A] text-sm">{Math.round(ev.confidence * 100)}% Conf</span>
                  <span className="font-mono-num text-[#8E8899] font-semibold text-xs">
                    {new Date(ev.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                  </span>
                  <ChevronRight className="w-4 h-4 text-[#8E8899]" />
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* SECTION 5 & 6: Recent Perimeter Activity & System Infrastructure Health */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 w-full">
        {/* SECTION 5: Recent Perimeter Activity */}
        <div className="lg:col-span-7 rounded-2xl bg-white border border-[#E5E1EE] p-6 sm:p-7 space-y-5 shadow-xs">
          <div className="flex items-center justify-between border-b border-[#E5E1EE] pb-4">
            <div className="flex items-center space-x-3.5">
              <div className="w-10 h-10 rounded-xl bg-[#FAF9FD] border border-[#E5E1EE] flex items-center justify-center text-[#7C5CFC]">
                <Activity className="w-6 h-6" />
              </div>
              <div>
                <h3 className="font-extrabold text-lg text-[#211D2B]">Recent Perimeter Activity</h3>
                <p className="text-xs text-[#625D6D] mt-0.5">Verified spatial zone triggers and sector movement vectors</p>
              </div>
            </div>
            <span className="text-xs px-3 py-1 rounded-full bg-[#DCFCE7] text-[#15803D] font-bold">
              Real-Time Feed
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {events.slice(0, 4).map((ev) => (
              <div
                key={ev.id}
                className="p-4 rounded-xl bg-[#FAF9FD] border border-[#E5E1EE] space-y-2 hover:border-[#7C5CFC] transition"
              >
                <div className="flex justify-between items-center">
                  <span className="font-bold text-sm text-[#211D2B] truncate">{ev.event_type.replace(/_/g, ' ')}</span>
                  <span className="text-xs text-[#7C5CFC] font-mono-num font-bold">
                    {new Date(ev.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
                <div className="text-xs text-[#625D6D] truncate">{ev.camera_name || `Cam #${ev.camera_id}`} • {ev.description}</div>
                <div className="pt-2 flex items-center justify-between text-xs border-t border-[#E5E1EE]">
                  <span className="text-[#16A34A] font-bold">Verified AI Match</span>
                  <span className="text-[#8E8899] font-medium">Sector 07 North</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* SECTION 6: System Infrastructure Health */}
        <div className="lg:col-span-5 rounded-2xl bg-white border border-[#E5E1EE] p-6 sm:p-7 space-y-5 shadow-xs">
          <div className="flex items-center justify-between border-b border-[#E5E1EE] pb-4">
            <div className="flex items-center space-x-3.5">
              <div className="w-10 h-10 rounded-xl bg-[#DCFCE7] border border-[#86EFAC] flex items-center justify-center text-[#15803D]">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <div>
                <h3 className="font-extrabold text-lg text-[#211D2B]">System Infrastructure Health</h3>
                <p className="text-xs text-[#625D6D] mt-0.5">Edge AI computer vision & storage health</p>
              </div>
            </div>
            <span className="text-xs px-3 py-1 rounded-full bg-[#DCFCE7] text-[#15803D] font-bold flex items-center space-x-1.5">
              <CheckCircle2 className="w-4 h-4" />
              <span>Optimal</span>
            </span>
          </div>

          <div className="space-y-3 text-sm">
            <div className="flex justify-between items-center p-3.5 rounded-xl bg-[#FAF9FD] border border-[#E5E1EE]">
              <div className="flex items-center space-x-3 text-[#211D2B] font-semibold">
                <Cpu className="w-4 h-4 text-[#7C5CFC]" />
                <span>YOLOv8 Edge Inference</span>
              </div>
              <span className="text-xs font-bold text-[#16A34A] bg-[#DCFCE7] px-2.5 py-0.5 rounded">30.0 FPS</span>
            </div>

            <div className="flex justify-between items-center p-3.5 rounded-xl bg-[#FAF9FD] border border-[#E5E1EE]">
              <div className="flex items-center space-x-3 text-[#211D2B] font-semibold">
                <Database className="w-4 h-4 text-[#7C5CFC]" />
                <span>Telemetry Database</span>
              </div>
              <span className="text-xs font-bold text-[#16A34A] bg-[#DCFCE7] px-2.5 py-0.5 rounded">Connected</span>
            </div>

            <div className="flex justify-between items-center p-3.5 rounded-xl bg-[#FAF9FD] border border-[#E5E1EE]">
              <div className="flex items-center space-x-3 text-[#211D2B] font-semibold">
                <HardDrive className="w-4 h-4 text-[#7C5CFC]" />
                <span>Forensic Evidence Vault</span>
              </div>
              <span className="text-xs font-bold text-[#211D2B] font-mono-num">68% Available</span>
            </div>

            <div className="flex justify-between items-center p-3.5 rounded-xl bg-[#FAF9FD] border border-[#E5E1EE]">
              <div className="flex items-center space-x-3 text-[#211D2B] font-semibold">
                <Activity className="w-4 h-4 text-[#7C5CFC]" />
                <span>Sensor Fleet Nodes</span>
              </div>
              <span className="text-xs font-bold text-[#16A34A] bg-[#DCFCE7] px-2.5 py-0.5 rounded font-mono-num">
                {cameraCount.online}/{cameraCount.total} Online
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
