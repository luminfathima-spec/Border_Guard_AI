import { ShieldAlert, Clock, ChevronRight, CheckCircle2, ArrowRight, MapPin } from 'lucide-react';
import type { Incident } from '../types';
import { SeverityBadge } from './SeverityBadge';

interface ActiveIncidentsSectionProps {
  incidents: Incident[];
  onSelectIncident: (incident: Incident) => void;
  onNavigateIncidents?: () => void;
}

export function ActiveIncidentsSection({
  incidents,
  onSelectIncident,
  onNavigateIncidents,
}: ActiveIncidentsSectionProps) {
  return (
    <div className="w-full rounded-2xl bg-white border border-[#E5E1EE] p-6 sm:p-7 space-y-5 shadow-xs">
      {/* Section Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#E5E1EE] pb-4">
        <div className="flex items-center space-x-3.5">
          <div className="w-10 h-10 rounded-xl bg-[#FEE2E2] border border-[#FCA5A5] flex items-center justify-center text-[#D32F2F] shadow-xs">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-3">
              <h2 className="font-extrabold text-xl text-[#211D2B]">Active Incidents & Breach Queue</h2>
              <span className="text-xs px-3 py-0.5 rounded-full bg-[#FEE2E2] border border-[#FCA5A5] text-[#B91C1C] font-bold">
                {incidents.length} Active
              </span>
            </div>
            <p className="text-sm text-[#625D6D] font-medium mt-0.5">
              High-priority security breaches requiring operator investigation and containment
            </p>
          </div>
        </div>

        {onNavigateIncidents && (
          <button
            onClick={onNavigateIncidents}
            className="text-sm text-[#7C5CFC] hover:text-[#6A46F9] font-bold flex items-center space-x-1.5 transition self-start sm:self-auto"
          >
            <span>View All Case Files</span>
            <ChevronRight className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Incidents Grid */}
      {incidents.length === 0 ? (
        <div className="py-12 text-center text-[#625D6D] space-y-3 bg-[#FAF9FD] rounded-xl border border-[#E5E1EE] p-8">
          <CheckCircle2 className="w-12 h-12 mx-auto text-[#16A34A]" />
          <div className="text-lg font-bold text-[#211D2B]">No Active Border Breaches</div>
          <p className="text-sm text-[#625D6D] max-w-md mx-auto">
            All monitored sectors are currently operating normally. No restricted zone entries or virtual tripwire breaches detected.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {incidents.map((inc) => {
            const isCritical = inc.severity === 'CRITICAL' || inc.severity === 'HIGH';
            return (
              <div
                key={inc.id}
                onClick={() => onSelectIncident(inc)}
                className={`p-5 rounded-xl border transition cursor-pointer space-y-4 group shadow-xs ${
                  isCritical
                    ? 'bg-[#FFFFFF] border-[#FCA5A5] hover:border-[#D32F2F] hover:shadow-md'
                    : 'bg-[#FAF9FD] border-[#E5E1EE] hover:border-[#7C5CFC] hover:shadow-md'
                }`}
              >
                {/* Header Row: Severity Badge + Incident ID + Status */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2.5">
                    <SeverityBadge severity={inc.severity} size="md" />
                    <span className="text-sm font-extrabold text-[#7C5CFC] font-mono-num">
                      {inc.incident_number}
                    </span>
                  </div>
                  <span className="text-xs px-3 py-1 rounded-md bg-[#FAF9FD] border border-[#E5E1EE] text-[#4328A8] font-bold uppercase tracking-wider">
                    {inc.status}
                  </span>
                </div>

                {/* Title & Description */}
                <div className="space-y-1.5">
                  <h3 className="text-lg font-bold text-[#211D2B] group-hover:text-[#7C5CFC] transition leading-snug">
                    {inc.title}
                  </h3>
                  <p className="text-sm text-[#625D6D] leading-relaxed line-clamp-2">
                    {inc.description}
                  </p>
                </div>

                {/* Metadata Strip */}
                <div className="flex items-center space-x-3 text-xs text-[#625D6D] bg-[#FAF9FD] p-2.5 rounded-lg border border-[#E5E1EE]">
                  <span className="flex items-center space-x-1 font-semibold text-[#211D2B]">
                    <MapPin className="w-3.5 h-3.5 text-[#7C5CFC]" />
                    <span>Sector 07 Northern Perimeter • Gate A</span>
                  </span>
                  <span className="text-[#D6CFDF]">|</span>
                  <span className="flex items-center space-x-1 font-semibold text-[#625D6D]">
                    <Clock className="w-3.5 h-3.5 text-[#8E8899]" />
                    <span className="font-mono-num">{new Date(inc.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                  </span>
                </div>

                {/* Footer Action */}
                <div className="flex items-center justify-between pt-2 border-t border-[#E5E1EE]">
                  <span className="text-xs text-[#8E8899] font-medium">
                    AI Threat Velocity: <strong className="text-[#D32F2F]">High</strong>
                  </span>
                  <span className="text-sm text-[#7C5CFC] font-bold flex items-center space-x-1.5 group-hover:translate-x-1 transition-transform">
                    <span>Investigate Case Dossier</span>
                    <ArrowRight className="w-4 h-4" />
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
