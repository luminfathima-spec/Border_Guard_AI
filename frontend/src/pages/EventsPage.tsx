import { useState, useEffect } from 'react';
import { Filter, RefreshCw } from 'lucide-react';
import { eventApi, cameraApi } from '../services/sentinelApi';
import type { SecurityEvent, Camera, Evidence } from '../types';
import { EvidencePlayerModal } from '../components/EvidencePlayerModal';
import { SeverityBadge } from '../components/SeverityBadge';

export function EventsPage() {
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [selectedEventType, setSelectedEventType] = useState<string>('');
  const [selectedSeverity, setSelectedSeverity] = useState<string>('');
  const [selectedCameraId, setSelectedCameraId] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [previewEvidence, setPreviewEvidence] = useState<Evidence | null>(null);

  const loadEvents = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (selectedEventType) params.event_type = selectedEventType;
      if (selectedSeverity) params.severity = selectedSeverity;
      if (selectedCameraId) params.camera_id = Number(selectedCameraId);

      const [eventsData, camsData] = await Promise.all([
        eventApi.list(params),
        cameraApi.list(),
      ]);
      setEvents(eventsData);
      setCameras(camsData);
    } catch (e) {
      console.error('Failed to load events:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEvents();
  }, [selectedEventType, selectedSeverity, selectedCameraId]);

  return (
    <div className="w-full space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-[#E5E1EE]">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#211D2B] tracking-tight flex items-center space-x-3">
            <span>Security Events Audit Ledger</span>
            <span className="text-xs px-3 py-1 rounded-full bg-[#F0EDFD] border border-[#DCD4FB] text-[#7C5CFC] font-bold">
              {events.length} Events Logged
            </span>
          </h1>
          <p className="text-sm text-[#625D6D] mt-1 font-medium">
            Cryptographically timestamped audit trail of computer vision perimeter detections
          </p>
        </div>

        <button
          onClick={loadEvents}
          className="p-2.5 rounded-lg bg-white hover:bg-[#FAF9FD] border border-[#E5E1EE] text-[#625D6D] hover:text-[#211D2B] transition shadow-xs self-start sm:self-auto"
          title="Refresh Events"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-[#7C5CFC]' : ''}`} />
        </button>
      </div>

      {/* Filter Bar */}
      <div className="p-4 rounded-xl bg-white border border-[#E5E1EE] flex flex-wrap items-center gap-3.5 text-xs shadow-xs">
        <div className="flex items-center space-x-2 text-[#8E8899] font-bold uppercase tracking-wider">
          <Filter className="w-4 h-4 text-[#7C5CFC]" />
          <span>FILTER LEDGER:</span>
        </div>

        <select
          value={selectedEventType}
          onChange={(e) => setSelectedEventType(e.target.value)}
          className="px-3.5 py-2 bg-[#FAF9FD] border border-[#E5E1EE] rounded-lg text-[#211D2B] text-xs font-semibold focus:outline-none focus:border-[#7C5CFC]"
        >
          <option value="">All Classifications</option>
          <option value="RESTRICTED_ZONE_ENTRY">Restricted Zone Entry</option>
          <option value="LINE_CROSSING">Virtual Line Crossing</option>
          <option value="LOITERING">Loitering Detection</option>
          <option value="PERSON_DETECTED">Person Detected</option>
          <option value="VEHICLE_DETECTED">Vehicle Detected</option>
        </select>

        <select
          value={selectedSeverity}
          onChange={(e) => setSelectedSeverity(e.target.value)}
          className="px-3.5 py-2 bg-[#FAF9FD] border border-[#E5E1EE] rounded-lg text-[#211D2B] text-xs font-semibold focus:outline-none focus:border-[#7C5CFC]"
        >
          <option value="">All Severities</option>
          <option value="CRITICAL">Critical</option>
          <option value="HIGH">High</option>
          <option value="MEDIUM">Medium</option>
          <option value="LOW">Low</option>
        </select>

        <select
          value={selectedCameraId}
          onChange={(e) => setSelectedCameraId(e.target.value)}
          className="px-3.5 py-2 bg-[#FAF9FD] border border-[#E5E1EE] rounded-lg text-[#211D2B] text-xs font-semibold focus:outline-none focus:border-[#7C5CFC]"
        >
          <option value="">All Sensor Nodes</option>
          {cameras.map((c) => (
            <option key={c.id} value={c.id}>
              {c.camera_identifier} ({c.name})
            </option>
          ))}
        </select>
      </div>

      {/* Events Table View */}
      <div className="rounded-xl bg-white border border-[#E5E1EE] overflow-hidden shadow-xs">
        <table className="w-full text-left text-sm">
          <thead className="bg-[#FAF9FD] border-b border-[#E5E1EE] text-xs text-[#8E8899] uppercase tracking-wider">
            <tr>
              <th className="py-3.5 px-5">Evidence</th>
              <th className="py-3.5 px-5">Time (UTC)</th>
              <th className="py-3.5 px-5">Severity</th>
              <th className="py-3.5 px-5">Event Classification</th>
              <th className="py-3.5 px-5">Sensor Node</th>
              <th className="py-3.5 px-5">Description</th>
              <th className="py-3.5 px-5">Confidence</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#E5E1EE]">
            {events.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-12 text-center text-[#625D6D] text-sm">
                  No security events matching filter criteria.
                </td>
              </tr>
            ) : (
              events.map((ev) => (
                <tr key={ev.id} className="hover:bg-[#FAF9FD] transition">
                  <td className="py-3.5 px-5">
                    {ev.snapshot_path ? (
                      <div
                        onClick={() => {
                          setPreviewEvidence({
                            id: ev.id,
                            event_id: ev.id,
                            evidence_type: 'SNAPSHOT',
                            file_path: ev.snapshot_path!,
                            file_url: `/static/snapshots/${ev.snapshot_path!.split('/').pop()}`,
                            timestamp: ev.timestamp,
                            created_at: ev.created_at,
                          });
                        }}
                        className="w-16 h-10 rounded-lg bg-black border border-[#E5E1EE] overflow-hidden cursor-pointer hover:border-[#7C5CFC] transition flex items-center justify-center shadow-xs"
                      >
                        <img
                          src={`http://localhost:8000/static/snapshots/${ev.snapshot_path.split('/').pop()}`}
                          alt="Thumbnail"
                          className="w-full h-full object-cover"
                          onError={(e) => {
                            (e.target as HTMLElement).style.display = 'none';
                          }}
                        />
                      </div>
                    ) : (
                      <span className="text-[#8E8899] text-xs">No Snapshot</span>
                    )}
                  </td>

                  <td className="py-3.5 px-5 text-[#211D2B] font-mono-num font-semibold">
                    {new Date(ev.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                  </td>

                  <td className="py-3.5 px-5">
                    <SeverityBadge severity={ev.severity} size="sm" />
                  </td>

                  <td className="py-3.5 px-5 font-bold text-[#211D2B]">
                    {ev.event_type.replace(/_/g, ' ')}
                  </td>

                  <td className="py-3.5 px-5 text-[#625D6D] font-medium">
                    {ev.camera_name || `Camera #${ev.camera_id}`}
                  </td>

                  <td className="py-3.5 px-5 text-[#625D6D] truncate max-w-sm">
                    {ev.description}
                  </td>

                  <td className="py-3.5 px-5 text-[#16A34A] font-bold">
                    {Math.round(ev.confidence * 100)}%
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {previewEvidence && (
        <EvidencePlayerModal
          evidence={previewEvidence}
          onClose={() => setPreviewEvidence(null)}
        />
      )}
    </div>
  );
}
