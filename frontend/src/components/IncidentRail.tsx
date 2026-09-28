import { ChevronRight, ShieldAlert, Clock, Bell, CheckCircle2 } from 'lucide-react';
import type { Incident, SecurityEvent } from '../types';
import { SeverityBadge } from './SeverityBadge';

interface IncidentRailProps {
  incidents: Incident[];
  events: SecurityEvent[];
  onSelectIncident: (incident: Incident) => void;
  onSelectEvent?: (event: SecurityEvent) => void;
  onNavigateIncidents?: () => void;
  onNavigateEvents?: () => void;
}

export function IncidentRail({
  incidents,
  events,
  onSelectIncident,
  onSelectEvent,
  onNavigateIncidents,
  onNavigateEvents,
}: IncidentRailProps) {
  return (
    <div className="space-y-4">
      {/* Active Incidents Panel */}
      <div className="rounded-lg bg-[#12151A] border border-[#262B35] p-4 space-y-3.5 shadow-sm">
        <div className="flex items-center justify-between border-b border-[#20252F] pb-2.5">
          <div className="flex items-center space-x-2 text-sm font-bold text-[#F5F3ED]">
            <ShieldAlert className="w-4 h-4 text-[#D6A84A]" />
            <span>Active Incidents Queue</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-[#2E2314] border border-[#5E441E] text-[#E5B85C] font-bold">
              {incidents.length}
            </span>
          </div>

          {onNavigateIncidents && (
            <button
              onClick={onNavigateIncidents}
              className="text-xs text-[#D6A84A] hover:text-[#E5B85C] flex items-center space-x-1 font-semibold transition"
            >
              <span>View Dossiers</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {incidents.length === 0 ? (
          <div className="py-8 text-center text-[#8E8A80] text-xs space-y-2 bg-[#0B0D10] rounded-md border border-[#20252F] p-4">
            <CheckCircle2 className="w-8 h-8 mx-auto text-[#5BAF75]" />
            <div className="text-sm font-semibold text-[#DCD7CB]">No Active Breaches</div>
            <p className="text-xs text-[#8E8A80]">All monitored sectors are currently operating normally.</p>
          </div>
        ) : (
          <div className="space-y-2.5">
            {incidents.slice(0, 3).map((inc) => (
              <div
                key={inc.id}
                onClick={() => onSelectIncident(inc)}
                className="p-3.5 rounded-md bg-[#161A21] border border-[#242933] hover:border-[#384152] cursor-pointer transition space-y-2 group"
              >
                <div className="flex items-center justify-between">
                  <span className="text-[#D6A84A] font-bold text-xs">{inc.incident_number}</span>
                  <SeverityBadge severity={inc.severity} size="sm" />
                </div>

                <div className="text-[#F5F3ED] text-sm font-bold line-clamp-1 group-hover:text-[#D6A84A] transition">
                  {inc.title}
                </div>

                <div className="flex items-center justify-between text-xs text-[#A39E93] pt-1 border-t border-[#20252F]">
                  <span className="flex items-center space-x-1.5 font-medium">
                    <Clock className="w-3.5 h-3.5 text-[#8E8A80]" />
                    <span>{new Date(inc.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                  </span>
                  <span className="text-[#DCD7CB] font-bold uppercase tracking-wider text-[11px]">
                    {inc.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Real-Time Live CV Detection Events Stream */}
      <div className="rounded-lg bg-[#12151A] border border-[#262B35] p-4 space-y-3.5 shadow-sm">
        <div className="flex items-center justify-between border-b border-[#20252F] pb-2.5">
          <div className="flex items-center space-x-2 text-sm font-bold text-[#F5F3ED]">
            <Bell className="w-4 h-4 text-[#D6A84A]" />
            <span>Real-Time CV Stream</span>
          </div>

          {onNavigateEvents && (
            <button
              onClick={onNavigateEvents}
              className="text-xs text-[#D6A84A] hover:text-[#E5B85C] flex items-center space-x-1 font-semibold transition"
            >
              <span>Full Audit</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
          {events.length === 0 ? (
            <div className="py-6 text-center text-[#8E8A80] text-xs">
              No recent security events logged.
            </div>
          ) : (
            events.slice(0, 4).map((ev) => (
              <div
                key={ev.id}
                onClick={() => onSelectEvent && onSelectEvent(ev)}
                className="p-2.5 rounded bg-[#161A21] border border-[#242933] hover:border-[#384152] transition text-xs cursor-pointer space-y-1.5"
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-xs text-[#F5F3ED] truncate">
                    {ev.event_type.replace(/_/g, ' ')}
                  </span>
                  <span className="text-xs text-[#5BAF75] font-bold">
                    {Math.round(ev.confidence * 100)}%
                  </span>
                </div>
                <div className="text-[#A39E93] text-xs line-clamp-1">{ev.description}</div>
                <div className="flex items-center justify-between text-[11px] text-[#8E8A80] pt-0.5">
                  <span className="font-medium">{ev.camera_name || `Camera #${ev.camera_id}`}</span>
                  <span className="font-mono-num">{new Date(ev.timestamp).toLocaleTimeString()}</span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
