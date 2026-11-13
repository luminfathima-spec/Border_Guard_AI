import { useState, useEffect } from 'react';
import {
  Shield, Settings, History, Filter, Search, RefreshCw, Save,
  CheckCircle2, Cpu, HardDrive
} from 'lucide-react';
import { auditApi } from '../services/sentinelApi';
import type { AuditLogEntry, SystemSettings } from '../types';

export function AuditSettingsPage() {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [settings, setSettings] = useState<SystemSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionFilter, setActionFilter] = useState('');
  const [resourceFilter, setResourceFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [notification, setNotification] = useState<string | null>(null);

  // Editable settings form
  const [retentionDays, setRetentionDays] = useState<number>(7);
  const [syncBatchSize, setSyncBatchSize] = useState<number>(50);
  const [savingSettings, setSavingSettings] = useState(false);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [logsData, settingsData] = await Promise.all([
        auditApi.getLogs({
          action: actionFilter || undefined,
          resource_type: resourceFilter || undefined,
          limit: 100,
        }),
        auditApi.getSettings(),
      ]);
      setLogs(logsData);
      setSettings(settingsData);
      setRetentionDays(settingsData.edge_buffer_retention_days);
      setSyncBatchSize(settingsData.edge_sync_batch_size || 50);
    } catch (err) {
      console.error('Failed to load audit and settings:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [actionFilter, resourceFilter]);

  const handleSaveSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSavingSettings(true);
      const updated = await auditApi.updateSettings({
        edge_buffer_retention_days: Number(retentionDays),
        edge_sync_batch_size: Number(syncBatchSize),
      });
      setSettings(updated);
      setNotification('Operational settings updated successfully and logged to immutable audit ledger.');
      setTimeout(() => setNotification(null), 5000);
      await fetchData();
    } catch (err: any) {
      alert(`Settings Update Notice: ${err?.response?.data?.detail || err.message}`);
    } finally {
      setSavingSettings(false);
    }
  };

  const filteredLogs = logs.filter((l) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      l.action.toLowerCase().includes(q) ||
      (l.user_email && l.user_email.toLowerCase().includes(q)) ||
      (l.resource_type && l.resource_type.toLowerCase().includes(q)) ||
      (l.resource_id && l.resource_id.toLowerCase().includes(q)) ||
      JSON.stringify(l.details).toLowerCase().includes(q)
    );
  });

  return (
    <div className="w-full space-y-6">
      {/* Top Banner / Notification */}
      {notification && (
        <div className="p-4 rounded-xl bg-[#DCFCE7] border border-[#86EFAC] text-[#166534] text-xs sm:text-sm font-bold flex items-center justify-between shadow-xs animate-fade-in">
          <div className="flex items-center space-x-2.5">
            <CheckCircle2 className="w-5 h-5 text-[#16A34A] shrink-0" />
            <span>{notification}</span>
          </div>
          <button onClick={() => setNotification(null)} className="text-[#15803D] text-xs font-extrabold uppercase">
            Dismiss
          </button>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-[#E5E1EE]">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#211D2B] tracking-tight flex items-center gap-2.5">
            <Shield className="w-7 h-7 text-[#7C5CFC]" />
            Audit History & Platform Configuration
          </h1>
          <p className="text-sm text-[#625D6D] mt-1 font-medium">
            Immutable system audit trails, operator security actions, model parameters, and edge retention limits
          </p>
        </div>

        <button
          onClick={fetchData}
          className="flex items-center space-x-2 px-3.5 py-2 rounded-xl border border-[#E5E1EE] bg-white hover:bg-[#FAF9FD] text-[#625D6D] hover:text-[#211D2B] transition shadow-2xs text-xs font-bold shrink-0"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Register</span>
        </button>
      </div>

      {/* Operational Settings & System Specs Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* System Specifications Card */}
        <div className="bg-white p-5 rounded-2xl border border-[#E5E1EE] shadow-2xs space-y-4">
          <div className="flex items-center space-x-2 pb-2 border-b border-[#E5E1EE]">
            <Cpu className="w-5 h-5 text-[#7C5CFC]" />
            <h3 className="text-base font-extrabold text-[#211D2B]">Environment Specifications</h3>
          </div>

          <div className="space-y-2.5 text-xs">
            <div className="flex justify-between py-1 border-b border-[#FAF9FD]">
              <span className="text-[#8E8899]">Application Name:</span>
              <span className="font-bold text-[#211D2B]">{settings?.app_name || 'SentinelAI'}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#FAF9FD]">
              <span className="text-[#8E8899]">Core Version:</span>
              <span className="font-mono font-bold text-[#4328A8]">{settings?.app_version || '2.0.0'}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#FAF9FD]">
              <span className="text-[#8E8899]">Deployment Tier:</span>
              <span className="font-bold text-[#16A34A] uppercase">{settings?.app_env || 'production'}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#FAF9FD]">
              <span className="text-[#8E8899]">Gemini Model:</span>
              <span className="font-mono font-bold text-[#7C5CFC]">{settings?.gemini_model || 'gemini-2.5-flash'}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#FAF9FD]">
              <span className="text-[#8E8899]">Edge Node ID:</span>
              <span className="font-mono font-bold text-[#211D2B]">{settings?.edge_node_id || 'EDGE-BORDER-01'}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-[#8E8899]">Total Audit Logs:</span>
              <span className="font-bold text-[#211D2B]">{settings?.total_audit_logs_count || logs.length}</span>
            </div>
          </div>
        </div>

        {/* Video & Ingestion Guardrails Card */}
        <div className="bg-white p-5 rounded-2xl border border-[#E5E1EE] shadow-2xs space-y-4">
          <div className="flex items-center space-x-2 pb-2 border-b border-[#E5E1EE]">
            <HardDrive className="w-5 h-5 text-[#4328A8]" />
            <h3 className="text-base font-extrabold text-[#211D2B]">Video & Ingestion Constraints</h3>
          </div>

          <div className="space-y-2.5 text-xs">
            <div className="flex justify-between py-1 border-b border-[#FAF9FD]">
              <span className="text-[#8E8899]">Max Upload File Size:</span>
              <span className="font-bold text-[#211D2B]">{settings?.max_upload_size_mb || 500} MB</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#FAF9FD]">
              <span className="text-[#8E8899]">Max Footage Duration:</span>
              <span className="font-bold text-[#211D2B]">{settings?.max_video_duration_seconds || 1800} seconds (30m)</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#FAF9FD]">
              <span className="text-[#8E8899]">Max Edge Disk Quota:</span>
              <span className="font-bold text-[#211D2B]">{settings?.edge_buffer_max_disk_mb || 500} MB</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#FAF9FD]">
              <span className="text-[#8E8899]">Supported Formats:</span>
              <span className="font-mono text-[#211D2B]">.mp4, .avi, .mov, .mkv</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-[#8E8899]">Integrity Hashing:</span>
              <span className="font-mono font-bold text-[#16A34A]">SHA-256 Mandatory</span>
            </div>
          </div>
        </div>

        {/* Operational Settings Form Card */}
        <div className="bg-white p-5 rounded-2xl border border-[#E5E1EE] shadow-2xs space-y-4">
          <div className="flex items-center space-x-2 pb-2 border-b border-[#E5E1EE]">
            <Settings className="w-5 h-5 text-[#7C5CFC]" />
            <h3 className="text-base font-extrabold text-[#211D2B]">Operator Parameters</h3>
          </div>

          <form onSubmit={handleSaveSettings} className="space-y-3.5 text-xs">
            <div>
              <label className="text-xs font-bold text-[#625D6D] block mb-1">
                Buffer Retention Threshold (Days)
              </label>
              <input
                type="number"
                min={1}
                max={90}
                value={retentionDays}
                onChange={(e) => setRetentionDays(Number(e.target.value))}
                className="w-full px-3 py-2 rounded-xl border border-[#E5E1EE] bg-[#FAF9FD] text-[#211D2B] font-medium focus:border-[#7C5CFC] focus:outline-hidden"
              />
              <span className="text-[10px] text-[#8E8899] mt-0.5 block">
                Older synced events and snapshots purged automatically.
              </span>
            </div>

            <div>
              <label className="text-xs font-bold text-[#625D6D] block mb-1">
                Edge Store-and-Forward Batch Size
              </label>
              <input
                type="number"
                min={5}
                max={500}
                value={syncBatchSize}
                onChange={(e) => setSyncBatchSize(Number(e.target.value))}
                className="w-full px-3 py-2 rounded-xl border border-[#E5E1EE] bg-[#FAF9FD] text-[#211D2B] font-medium focus:border-[#7C5CFC] focus:outline-hidden"
              />
              <span className="text-[10px] text-[#8E8899] mt-0.5 block">
                Max records transferred in a single synchronization frame.
              </span>
            </div>

            <div className="pt-2">
              <button
                type="submit"
                disabled={savingSettings}
                className="w-full flex items-center justify-center space-x-2 py-2.5 rounded-xl bg-[#7C5CFC] hover:bg-[#6846EB] text-white text-xs font-bold shadow-xs transition disabled:opacity-50"
              >
                <Save className="w-4 h-4" />
                <span>{savingSettings ? 'Saving Configuration...' : 'Commit Operational Settings'}</span>
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* Filter and Search Bar for Audit History */}
      <div className="flex flex-col sm:flex-row gap-3 items-center justify-between bg-white p-4 rounded-xl border border-[#E5E1EE] shadow-2xs">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 absolute left-3 top-3 text-[#8E8899]" />
          <input
            type="text"
            placeholder="Search action, user, or resource ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-xs sm:text-sm rounded-lg border border-[#E5E1EE] focus:border-[#7C5CFC] focus:outline-hidden bg-[#FAF9FD]"
          />
        </div>

        <div className="flex items-center space-x-2 w-full sm:w-auto flex-wrap">
          <Filter className="w-4 h-4 text-[#8E8899]" />
          <span className="text-xs font-bold text-[#625D6D]">Filter Action:</span>
          <select
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            className="text-xs px-3 py-1.5 rounded-lg border border-[#E5E1EE] bg-[#FAF9FD] text-[#211D2B] font-medium focus:border-[#7C5CFC] focus:outline-hidden"
          >
            <option value="">All Actions</option>
            <option value="LOGIN">Login</option>
            <option value="REPORT">Report Workflows</option>
            <option value="ESCALATE">Escalations</option>
            <option value="SETTINGS">Settings Changes</option>
            <option value="CAMERA">Camera Actions</option>
          </select>

          <span className="text-xs font-bold text-[#625D6D] ml-2">Resource:</span>
          <select
            value={resourceFilter}
            onChange={(e) => setResourceFilter(e.target.value)}
            className="text-xs px-3 py-1.5 rounded-lg border border-[#E5E1EE] bg-[#FAF9FD] text-[#211D2B] font-medium focus:border-[#7C5CFC] focus:outline-hidden"
          >
            <option value="">All Resources</option>
            <option value="REPORT">Report</option>
            <option value="INCIDENT">Incident</option>
            <option value="CAMERA">Camera</option>
            <option value="USER">User</option>
            <option value="SETTINGS">Settings</option>
          </select>
        </div>
      </div>

      {/* Immutable Audit History Table */}
      <div className="bg-white rounded-2xl border border-[#E5E1EE] shadow-2xs overflow-hidden">
        <div className="p-5 border-b border-[#E5E1EE] flex items-center justify-between">
          <div>
            <h3 className="text-base font-extrabold text-[#211D2B] flex items-center gap-2">
              <History className="w-5 h-5 text-[#7C5CFC]" />
              Immutable System Audit Ledger
            </h3>
            <p className="text-xs text-[#625D6D] mt-0.5">
              Cryptographically timestamped operational trace of all security analyst and system interactions
            </p>
          </div>
          <span className="text-xs font-mono font-bold px-2.5 py-1 rounded-lg bg-[#FAF9FD] border border-[#E5E1EE] text-[#625D6D]">
            {filteredLogs.length} events logged
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#FAF9FD] text-[#625D6D] uppercase text-[10px] font-bold border-b border-[#E5E1EE]">
              <tr>
                <th className="px-5 py-3">Log ID</th>
                <th className="px-5 py-3">Timestamp (UTC)</th>
                <th className="px-5 py-3">Operator / User</th>
                <th className="px-5 py-3">Action</th>
                <th className="px-5 py-3">Resource Target</th>
                <th className="px-5 py-3">Client IP</th>
                <th className="px-5 py-3">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E5E1EE] font-medium text-[#211D2B]">
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-5 py-10 text-center text-xs text-[#8E8899]">
                    Loading audit trail records...
                  </td>
                </tr>
              ) : filteredLogs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-5 py-10 text-center text-xs text-[#8E8899]">
                    No audit records match the selected filters.
                  </td>
                </tr>
              ) : (
                filteredLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-[#FAF9FD] transition">
                    <td className="px-5 py-3 font-mono font-bold text-[#8E8899] text-[11px]">
                      #{log.id}
                    </td>
                    <td className="px-5 py-3 text-[#625D6D] whitespace-nowrap">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                    <td className="px-5 py-3">
                      <span className="font-semibold text-[#211D2B]">
                        {log.user_email || `User #${log.user_id || 'System'}`}
                      </span>
                    </td>
                    <td className="px-5 py-3">
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] uppercase font-bold ${
                          log.action.includes('LOGIN')
                            ? 'bg-[#DCFCE7] text-[#166534]'
                            : log.action.includes('ESCALATE') || log.action.includes('REJECT')
                            ? 'bg-[#FEE2E2] text-[#B91C1C]'
                            : log.action.includes('APPROVE')
                            ? 'bg-[#DCFCE7] text-[#166534]'
                            : 'bg-[#F0EDFD] text-[#4328A8]'
                        }`}
                      >
                        {log.action}
                      </span>
                    </td>
                    <td className="px-5 py-3 font-mono text-[11px] text-[#4328A8]">
                      {log.resource_type ? `${log.resource_type} #${log.resource_id || ''}` : 'SYSTEM'}
                    </td>
                    <td className="px-5 py-3 font-mono text-[#8E8899] text-[11px]">
                      {log.ip_address || '127.0.0.1'}
                    </td>
                    <td className="px-5 py-3 text-[#625D6D] max-w-xs truncate" title={JSON.stringify(log.details)}>
                      {JSON.stringify(log.details)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
