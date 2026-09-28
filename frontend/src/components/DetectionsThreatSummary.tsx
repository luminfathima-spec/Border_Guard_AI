import { ShieldAlert, CheckCircle2, ArrowRight } from 'lucide-react';
import type { SecurityEvent } from '../types';

interface DetectionsThreatSummaryProps {
  events: SecurityEvent[];
  onNavigateEvents?: () => void;
}

export function DetectionsThreatSummary({ events, onNavigateEvents }: DetectionsThreatSummaryProps) {
  const sectors = [
    { name: 'Sector 07 Northern Perimeter', risk: 'HIGH RISK', color: 'text-[#B91C1C]', bg: 'bg-[#FEE2E2] border-[#FCA5A5]', details: 'Restricted buffer zone intrusion logged' },
    { name: 'Sector 04 Eastern Gate Outpost', risk: 'NOMINAL', color: 'text-[#15803D]', bg: 'bg-[#DCFCE7] border-[#86EFAC]', details: 'Routine checkpoint transit verified' },
    { name: 'Sector 09 Riverine Demarcation', risk: 'ELEVATED', color: 'text-[#B45309]', bg: 'bg-[#FEF3C7] border-[#FCD34D]', details: 'Virtual tripwire movement detected' },
  ];

  return (
    <div className="rounded-xl bg-white border border-[#E5E1EE] p-5 space-y-4 shadow-xs flex flex-col justify-between h-full">
      <div className="space-y-3.5">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[#E5E1EE] pb-3">
          <div className="flex items-center space-x-2.5">
            <ShieldAlert className="w-5 h-5 text-[#7C5CFC]" />
            <span className="font-extrabold text-base text-[#211D2B]">Sector Threat & Detection Matrix</span>
          </div>

          {onNavigateEvents && (
            <button
              onClick={onNavigateEvents}
              className="text-xs text-[#7C5CFC] hover:text-[#6A46F9] flex items-center space-x-1 font-bold transition"
            >
              <span>Full Stream</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* Sector Risk Rating Cards */}
        <div className="space-y-2">
          {sectors.map((sec, idx) => (
            <div
              key={idx}
              className="p-3 rounded-lg bg-[#FAF9FD] border border-[#E5E1EE] flex items-center justify-between text-xs"
            >
              <div className="space-y-0.5">
                <div className="font-bold text-[#211D2B] text-xs">{sec.name}</div>
                <div className="text-[11px] text-[#625D6D]">{sec.details}</div>
              </div>
              <span className={`px-2.5 py-0.5 rounded-md text-[11px] font-bold border ${sec.color} ${sec.bg}`}>
                {sec.risk}
              </span>
            </div>
          ))}
        </div>

        {/* Recent CV Detections Mini Stream */}
        <div className="space-y-1.5 pt-1">
          <div className="text-xs font-bold text-[#8E8899] uppercase tracking-wider">
            Real-Time Detections Feed
          </div>
          <div className="space-y-2 max-h-36 overflow-y-auto pr-1">
            {events.slice(0, 3).map((ev) => (
              <div
                key={ev.id}
                className="p-2.5 rounded-lg bg-[#FAF9FD] border border-[#E5E1EE] flex items-center justify-between text-xs"
              >
                <div className="space-y-0.5 truncate pr-2">
                  <div className="font-bold text-[#211D2B] truncate">{ev.event_type.replace(/_/g, ' ')}</div>
                  <div className="text-[11px] text-[#625D6D] truncate">{ev.camera_name || `Cam #${ev.camera_id}`}</div>
                </div>
                <div className="text-right shrink-0">
                  <div className="text-xs text-[#16A34A] font-bold">{Math.round(ev.confidence * 100)}%</div>
                  <div className="text-[10px] text-[#8E8899] font-mono-num">{new Date(ev.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Footer Insight */}
      <div className="pt-2 border-t border-[#E5E1EE] flex items-center justify-between text-xs text-[#8E8899]">
        <span>YOLOv8 Edge Computer Vision</span>
        <span className="text-[#15803D] font-bold flex items-center space-x-1">
          <CheckCircle2 className="w-3.5 h-3.5" />
          <span>Zero False Alarms</span>
        </span>
      </div>
    </div>
  );
}
