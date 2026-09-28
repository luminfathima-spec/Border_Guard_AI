import { useState, useEffect } from 'react';
import { RefreshCw, Search } from 'lucide-react';
import { alertApi } from '../services/sentinelApi';
import type { Alert } from '../types';
import { SeverityBadge } from '../components/SeverityBadge';

export function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [selectedSeverity, setSelectedSeverity] = useState<string>('');
  const [loading, setLoading] = useState(true);

  const loadAlerts = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (selectedStatus) params.status = selectedStatus;
      if (selectedSeverity) params.severity = selectedSeverity;
      const data = await alertApi.list(params);
      setAlerts(data);
    } catch (e) {
      console.error('Failed to load alerts:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();
  }, [selectedStatus, selectedSeverity]);

  const handleUpdateStatus = async (alertId: number, newStatus: string) => {
    try {
      await alertApi.updateStatus(alertId, newStatus);
      loadAlerts();
    } catch (e) {
      console.error('Failed to update alert status:', e);
    }
  };

  return (
    <div className="w-full space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-[#E5E1EE]">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#211D2B] tracking-tight flex items-center space-x-3">
            <span>Tactical Alerts Triage Console</span>
            <span className="text-xs px-3 py-1 rounded-full bg-[#FEF3C7] border border-[#FCD34D] text-[#B45309] font-bold">
              {alerts.length} Active
            </span>
          </h1>
          <p className="text-sm text-[#625D6D] mt-1 font-medium">
            Real-time alert dispatch, verification queue, and automated operator escalation
          </p>
        </div>

        <button
          onClick={loadAlerts}
          className="p-2.5 rounded-lg bg-white hover:bg-[#FAF9FD] border border-[#E5E1EE] text-[#625D6D] hover:text-[#211D2B] transition shadow-xs self-start sm:self-auto"
          title="Refresh Alerts"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-[#7C5CFC]' : ''}`} />
        </button>
      </div>

      {/* Filter Bar */}
      <div className="p-4 rounded-xl bg-white border border-[#E5E1EE] flex flex-wrap items-center gap-3.5 text-xs shadow-xs">
        <div className="flex items-center space-x-2 text-[#8E8899] font-bold uppercase tracking-wider">
          <Search className="w-4 h-4 text-[#7C5CFC]" />
          <span>TRIAGE FILTERS:</span>
        </div>

        <select
          value={selectedStatus}
          onChange={(e) => setSelectedStatus(e.target.value)}
          className="px-3.5 py-2 bg-[#FAF9FD] border border-[#E5E1EE] rounded-lg text-[#211D2B] text-xs font-semibold focus:outline-none focus:border-[#7C5CFC]"
        >
          <option value="">All Alert Statuses</option>
          <option value="NEW">New (Unacknowledged)</option>
          <option value="ACKNOWLEDGED">Acknowledged</option>
          <option value="INVESTIGATING">Investigating</option>
          <option value="RESOLVED">Resolved</option>
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
      </div>

      {/* Alerts Table */}
      <div className="rounded-xl bg-white border border-[#E5E1EE] overflow-hidden shadow-xs">
        <table className="w-full text-left text-sm">
          <thead className="bg-[#FAF9FD] border-b border-[#E5E1EE] text-xs text-[#8E8899] uppercase tracking-wider">
            <tr>
              <th className="py-3.5 px-5">Severity</th>
              <th className="py-3.5 px-5">Alert Title</th>
              <th className="py-3.5 px-5">Sensor Source</th>
              <th className="py-3.5 px-5">Message</th>
              <th className="py-3.5 px-5">Status</th>
              <th className="py-3.5 px-5">Timestamp</th>
              <th className="py-3.5 px-5 text-right">Triage Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#E5E1EE]">
            {alerts.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-12 text-center text-[#625D6D] text-sm">
                  No active alerts matching filter criteria.
                </td>
              </tr>
            ) : (
              alerts.map((al) => (
                <tr key={al.id} className="hover:bg-[#FAF9FD] transition">
                  <td className="py-4 px-5">
                    <SeverityBadge severity={al.severity} size="sm" />
                  </td>

                  <td className="py-4 px-5 font-bold text-[#211D2B]">
                    {al.title}
                  </td>

                  <td className="py-4 px-5 text-[#7C5CFC] font-bold font-mono-num">
                    CAM-0{al.camera_id}
                  </td>

                  <td className="py-4 px-5 text-[#625D6D] max-w-sm truncate">
                    {al.message}
                  </td>

                  <td className="py-4 px-5">
                    <span className="text-xs px-2.5 py-1 rounded-md font-bold uppercase bg-[#F0EDFD] text-[#4328A8] border border-[#DCD4FB]">
                      {al.status}
                    </span>
                  </td>

                  <td className="py-4 px-5 text-[#8E8899] font-mono-num text-xs">
                    {new Date(al.created_at).toLocaleTimeString()}
                  </td>

                  <td className="py-4 px-5 text-right space-x-2">
                    {al.status === 'NEW' && (
                      <button
                        onClick={() => handleUpdateStatus(al.id, 'ACKNOWLEDGED')}
                        className="px-3 py-1.5 rounded-lg bg-[#FAF9FD] hover:bg-[#F0EDFD] border border-[#E5E1EE] text-[#4328A8] text-xs font-bold transition"
                      >
                        Acknowledge
                      </button>
                    )}
                    {al.status !== 'RESOLVED' && (
                      <button
                        onClick={() => handleUpdateStatus(al.id, 'RESOLVED')}
                        className="px-3 py-1.5 rounded-lg bg-[#DCFCE7] hover:bg-[#BBF7D0] text-[#15803D] text-xs font-bold transition"
                      >
                        Resolve
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
