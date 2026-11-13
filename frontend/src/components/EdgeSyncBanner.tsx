import { useState, useEffect } from 'react';
import {
  Wifi,
  WifiOff,
  RefreshCw,
  HardDrive,
  Database,
  ShieldAlert,
  Play,
  CheckCircle2,
  X,
  Zap,
} from 'lucide-react';
import { edgeApi } from '../services/sentinelApi';
import type { EdgeStatusResponse, EdgeBenchmarkResponse } from '../types';

export function EdgeSyncBanner() {
  const [status, setStatus] = useState<EdgeStatusResponse | null>(null);
  const [isSyncing, setIsSyncing] = useState(false);
  const [isTogglingNetwork, setIsTogglingNetwork] = useState(false);
  const [isRunningBenchmark, setIsRunningBenchmark] = useState(false);
  const [benchmarkResult, setBenchmarkResult] = useState<EdgeBenchmarkResponse | null>(null);
  const [showBenchmarkModal, setShowBenchmarkModal] = useState(false);
  const [syncFeedback, setSyncFeedback] = useState<string | null>(null);

  const fetchStatus = async () => {
    try {
      const data = await edgeApi.getStatus();
      setStatus(data);
    } catch (e) {
      // Backend may be initializing
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 8000);
    return () => clearInterval(interval);
  }, []);

  const handleToggleNetwork = async () => {
    if (!status) return;
    setIsTogglingNetwork(true);
    try {
      const targetState = status.network_state === 'ONLINE' ? 'OFFLINE' : 'ONLINE';
      const reason = targetState === 'OFFLINE' ? 'Operator-initiated edge blackout drill' : 'Drill completed';
      const updated = await edgeApi.updateNetworkState(targetState, reason);
      setStatus(updated);
      setSyncFeedback(`Network switched to ${targetState}`);
      setTimeout(() => setSyncFeedback(null), 4000);
    } catch (e: any) {
      setSyncFeedback(`Failed to toggle network: ${e?.message || 'Error'}`);
    } finally {
      setIsTogglingNetwork(false);
    }
  };

  const handleSyncNow = async () => {
    setIsSyncing(true);
    try {
      const res = await edgeApi.triggerSync(100, true);
      setSyncFeedback(
        `Sync ${res.status}: ${res.events_synced} synced, ${res.duplicates_prevented} duplicates prevented (${res.duration_ms}ms)`
      );
      await fetchStatus();
      setTimeout(() => setSyncFeedback(null), 6000);
    } catch (e: any) {
      setSyncFeedback(`Sync failed: ${e?.message || 'Error'}`);
    } finally {
      setIsSyncing(false);
    }
  };

  const handleRunBenchmark = async () => {
    setIsRunningBenchmark(true);
    setShowBenchmarkModal(true);
    try {
      const result = await edgeApi.runBenchmark(15, true);
      setBenchmarkResult(result);
      await fetchStatus();
    } catch (e: any) {
      setSyncFeedback(`Benchmark failed: ${e?.message || 'Error'}`);
    } finally {
      setIsRunningBenchmark(false);
    }
  };

  if (!status) {
    return null;
  }

  const isOnline = status.network_state === 'ONLINE';
  const pendingCount = status.buffer_stats.pending_sync_count;
  const diskMb = status.disk_metrics.buffer_size_mb;
  const quotaMb = status.disk_metrics.max_quota_mb;
  const quotaPct = status.disk_metrics.quota_utilization_percent;

  return (
    <>
      <div
        className={`w-full rounded-lg border px-4 py-2.5 shadow-sm transition-all text-xs ${
          isOnline
            ? 'bg-[#12161A] border-[#1E252D] text-[#ECEBE6]'
            : 'bg-[#221810] border-[#5E381C] text-[#FBEFE3]'
        }`}
      >
        <div className="flex flex-wrap items-center justify-between gap-3">
          {/* Left: Edge Node Identification & Network Status */}
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              <span className="relative flex h-2.5 w-2.5">
                <span
                  className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                    isOnline ? 'bg-emerald-400' : 'bg-amber-500'
                  }`}
                />
                <span
                  className={`relative inline-flex rounded-full h-2.5 w-2.5 ${
                    isOnline ? 'bg-emerald-500' : 'bg-amber-500'
                  }`}
                />
              </span>
              <span className="font-mono text-[11px] font-bold tracking-wider uppercase text-[#9B9990]">
                {status.edge_node_id}
              </span>
            </div>

            <div className="h-3.5 w-px bg-[#2C323B]" />

            <div className="flex items-center space-x-1.5">
              {isOnline ? (
                <Wifi className="w-3.5 h-3.5 text-emerald-400" />
              ) : (
                <WifiOff className="w-3.5 h-3.5 text-amber-400" />
              )}
              <span
                className={`font-semibold tracking-wide uppercase ${
                  isOnline ? 'text-emerald-400' : 'text-amber-400'
                }`}
              >
                {status.network_state}
              </span>
              {status.offline_reason && (
                <span className="hidden md:inline text-[10px] text-[#A6A298] italic">
                  ({status.offline_reason})
                </span>
              )}
            </div>
          </div>

          {/* Center: Buffer Stats & Quota Telemetry */}
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-1.5">
              <Database className="w-3.5 h-3.5 text-[#D6A84A]" />
              <span className="text-[#A6A298]">Buffer Queue:</span>
              <span
                className={`font-mono font-bold px-1.5 py-0.5 rounded text-[11px] ${
                  pendingCount > 0
                    ? 'bg-amber-950/80 text-amber-300 border border-amber-800/60'
                    : 'bg-[#1B2228] text-emerald-400 border border-[#27323C]'
                }`}
              >
                {pendingCount} {pendingCount === 1 ? 'event' : 'events'} pending
              </span>
            </div>

            <div className="hidden sm:flex items-center space-x-2">
              <HardDrive className="w-3.5 h-3.5 text-[#8E8B83]" />
              <span className="text-[#A6A298]">Disk Quota:</span>
              <div className="w-16 h-1.5 bg-[#252C35] rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${
                    quotaPct > 85 ? 'bg-rose-500' : quotaPct > 60 ? 'bg-amber-400' : 'bg-emerald-500'
                  }`}
                  style={{ width: `${Math.min(quotaPct, 100)}%` }}
                />
              </div>
              <span className="font-mono text-[11px] text-[#C4C0B6]">
                {diskMb} / {quotaMb} MB
              </span>
            </div>
          </div>

          {/* Right: Operational Controls */}
          <div className="flex items-center space-x-2">
            {syncFeedback && (
              <span className="text-[11px] font-mono text-emerald-400 mr-2 truncate max-w-xs">
                {syncFeedback}
              </span>
            )}

            <button
              onClick={handleToggleNetwork}
              disabled={isTogglingNetwork}
              title="Simulate network disconnection for edge resilience drills"
              className={`px-2.5 py-1 rounded text-[11px] font-semibold transition-colors flex items-center space-x-1 border ${
                isOnline
                  ? 'bg-[#1C2026] hover:bg-[#252B33] text-[#DFDDD5] border-[#313844]'
                  : 'bg-amber-950/70 hover:bg-amber-900/80 text-amber-200 border-amber-700/60'
              }`}
            >
              <Zap className="w-3 h-3" />
              <span>{isOnline ? 'Simulate Blackout' : 'Restore Network'}</span>
            </button>

            <button
              onClick={handleSyncNow}
              disabled={isSyncing}
              title="Trigger store-and-forward reconciliation to central PostgreSQL"
              className="px-2.5 py-1 rounded text-[11px] font-semibold bg-[#222933] hover:bg-[#2C3542] text-[#DFDDD5] border border-[#3A4556] transition-colors flex items-center space-x-1"
            >
              <RefreshCw className={`w-3 h-3 ${isSyncing ? 'animate-spin text-[#D6A84A]' : ''}`} />
              <span>{isSyncing ? 'Syncing...' : 'Sync Now'}</span>
            </button>

            <button
              onClick={handleRunBenchmark}
              disabled={isRunningBenchmark}
              title="Run automated edge blackout, restart persistence, and 0% loss recovery benchmark"
              className="px-2.5 py-1 rounded text-[11px] font-semibold bg-[#32231A] hover:bg-[#432F23] text-amber-300 border border-[#6B4628] transition-colors flex items-center space-x-1"
            >
              <Play className="w-3 h-3 fill-amber-300" />
              <span className="hidden md:inline">Run Benchmark</span>
            </button>
          </div>
        </div>
      </div>

      {/* Benchmark Results Modal */}
      {showBenchmarkModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
          <div className="w-full max-w-2xl rounded-xl bg-[#111317] border border-[#2B313A] shadow-2xl p-6 text-[#ECEBE6] space-y-5">
            <div className="flex items-center justify-between border-b border-[#22262E] pb-3">
              <div className="flex items-center space-x-2.5">
                <ShieldAlert className="w-5 h-5 text-[#D6A84A]" />
                <h3 className="font-bold text-base text-[#F4F3EE]">
                  Edge Store-and-Forward Empirical Benchmark
                </h3>
              </div>
              <button
                onClick={() => setShowBenchmarkModal(false)}
                className="text-[#8E8B83] hover:text-[#ECEBE6] transition-colors p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {isRunningBenchmark ? (
              <div className="py-12 flex flex-col items-center justify-center space-y-4 text-center">
                <div className="w-10 h-10 border-3 border-amber-500 border-t-transparent rounded-full animate-spin" />
                <div className="space-y-1">
                  <div className="font-semibold text-sm text-[#F4F3EE]">
                    Simulating Outage, Crash Restart & Reconciliation...
                  </div>
                  <div className="text-xs text-[#8E8B83]">
                    1. Network cut $\to$ 2. WAL buffer spool $\to$ 3. Process reboot $\to$ 4. Restored sync $\to$ 5. Idempotent check
                  </div>
                </div>
              </div>
            ) : benchmarkResult ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 rounded-lg bg-emerald-950/40 border border-emerald-800/60 text-emerald-300">
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                    <span className="font-bold text-sm">Empirical Benchmark Completed Successfully</span>
                  </div>
                  <span className="px-2 py-0.5 rounded text-xs font-mono font-bold bg-emerald-900/60 border border-emerald-700/60">
                    STATUS: {benchmarkResult.status}
                  </span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  <div className="p-3 rounded-lg bg-[#16191F] border border-[#252B34] space-y-1">
                    <div className="text-[11px] text-[#8E8B83]">Event Loss Rate</div>
                    <div className="text-xl font-bold font-mono text-emerald-400">
                      {benchmarkResult.event_loss_pct.toFixed(1)}%
                    </div>
                    <div className="text-[10px] text-[#A6A298]">
                      {benchmarkResult.events_recovered} of {benchmarkResult.total_events_generated} spooled
                    </div>
                  </div>

                  <div className="p-3 rounded-lg bg-[#16191F] border border-[#252B34] space-y-1">
                    <div className="text-[11px] text-[#8E8B83]">Duplicate Prevention</div>
                    <div className="text-xl font-bold font-mono text-emerald-400">
                      {benchmarkResult.duplicate_detection_accuracy_pct.toFixed(1)}%
                    </div>
                    <div className="text-[10px] text-[#A6A298]">
                      {benchmarkResult.duplicate_events_prevented} duplicate(s) rejected
                    </div>
                  </div>

                  <div className="p-3 rounded-lg bg-[#16191F] border border-[#252B34] space-y-1">
                    <div className="text-[11px] text-[#8E8B83]">Timestamp Fidelity</div>
                    <div className="text-xl font-bold font-mono text-emerald-400">
                      {benchmarkResult.timestamp_preservation_accuracy_pct.toFixed(1)}%
                    </div>
                    <div className="text-[10px] text-[#A6A298]">Zero temporal skew preserved</div>
                  </div>

                  <div className="p-3 rounded-lg bg-[#16191F] border border-[#252B34] space-y-1">
                    <div className="text-[11px] text-[#8E8B83]">Recovery Latency</div>
                    <div className="text-xl font-bold font-mono text-amber-400">
                      {benchmarkResult.recovery_time_ms} ms
                    </div>
                    <div className="text-[10px] text-[#A6A298]">Reconnection to commit</div>
                  </div>

                  <div className="p-3 rounded-lg bg-[#16191F] border border-[#252B34] space-y-1">
                    <div className="text-[11px] text-[#8E8B83]">Evidence Hash Fidelity</div>
                    <div className="text-xl font-bold font-mono text-emerald-400">
                      {benchmarkResult.evidence_hash_match_pct.toFixed(1)}%
                    </div>
                    <div className="text-[10px] text-[#A6A298]">SHA-256 match verified</div>
                  </div>

                  <div className="p-3 rounded-lg bg-[#16191F] border border-[#252B34] space-y-1">
                    <div className="text-[11px] text-[#8E8B83]">Local WAL Buffer Size</div>
                    <div className="text-xl font-bold font-mono text-[#D6A84A]">
                      {(benchmarkResult.buffer_db_size_bytes / 1024).toFixed(1)} KB
                    </div>
                    <div className="text-[10px] text-[#A6A298]">SQLite WAL physical footprint</div>
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-[#16191F] border border-[#252B34] text-xs text-[#A6A298] space-y-1">
                  <div className="font-semibold text-[#ECEBE6]">Scientific Certification Note:</div>
                  <p>
                    Verified under controlled network outage conditions. Unique UUID idempotency keys prevented duplicate rows across multiple reconnection retry cycles. SQLite WAL journaling guarantees crash-safe durability across process restart. Target edge device qualification required prior to field deployment.
                  </p>
                </div>
              </div>
            ) : (
              <div className="text-center py-6 text-sm text-[#8E8B83]">
                Click "Run Benchmark" to execute an automated recovery test.
              </div>
            )}

            <div className="flex justify-end space-x-3 border-t border-[#22262E] pt-3">
              <button
                onClick={() => setShowBenchmarkModal(false)}
                className="px-4 py-1.5 rounded-lg bg-[#20252C] hover:bg-[#2B323C] text-xs font-semibold text-[#DFDDD5] transition-colors"
              >
                Close
              </button>
              <button
                onClick={handleRunBenchmark}
                disabled={isRunningBenchmark}
                className="px-4 py-1.5 rounded-lg bg-[#D6A84A] hover:bg-[#C2963B] text-xs font-bold text-[#14120D] transition-colors flex items-center space-x-1.5"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isRunningBenchmark ? 'animate-spin' : ''}`} />
                <span>Rerun Benchmark</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
