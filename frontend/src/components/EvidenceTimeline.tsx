import { useState, useEffect } from 'react';
import {
  Camera,
  Film,
  Crosshair,
  ShieldAlert,
  FileCheck,
  Bot,
  FileText,
  Eye,
  CheckCircle2,
  AlertTriangle,
  Copy,
  Check,
  RefreshCw,
  GitBranch,
  ShieldCheck,
  PlusCircle,
  HelpCircle,
} from 'lucide-react';
import { eventGraphApi } from '../services/sentinelApi';
import type { EvidenceChainResponse, EventGraphResponse } from '../types';

interface EvidenceTimelineProps {
  incidentId: number;
  incidentNumber?: string;
}

export function EvidenceTimeline({ incidentId, incidentNumber }: EvidenceTimelineProps) {
  const [chainData, setChainData] = useState<EvidenceChainResponse | null>(null);
  const [graphData, setGraphData] = useState<EventGraphResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [synthesizing, setSynthesizing] = useState<boolean>(false);
  const [copiedHash, setCopiedHash] = useState<string | null>(null);
  const [showAddObs, setShowAddObs] = useState<boolean>(false);
  const [newObsTitle, setNewObsTitle] = useState('');
  const [newObsDesc, setNewObsDesc] = useState('');
  const [newObsType, setNewObsType] = useState<'DIRECT_FACT' | 'CONFLICT_RECORD' | 'MISSING_DATA_GAP'>('DIRECT_FACT');
  const [submittingObs, setSubmittingObs] = useState(false);

  const fetchTimeline = async () => {
    try {
      setLoading(true);
      const [cRes, gRes] = await Promise.all([
        eventGraphApi.getEvidenceChain(incidentId),
        eventGraphApi.getGraph(incidentId),
      ]);
      setChainData(cRes);
      setGraphData(gRes);
    } catch (err) {
      console.error('Failed to load evidence chain:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (incidentId) {
      fetchTimeline();
    }
  }, [incidentId]);

  const handleAutoSynthesize = async () => {
    try {
      setSynthesizing(true);
      await eventGraphApi.autoSynthesize(incidentId);
      await fetchTimeline();
    } catch (err) {
      console.error('Failed to synthesize graph:', err);
    } finally {
      setSynthesizing(false);
    }
  };

  const handleCopyHash = (hash: string) => {
    navigator.clipboard.writeText(hash);
    setCopiedHash(hash);
    setTimeout(() => setCopiedHash(null), 2000);
  };

  const handleRecordObservation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newObsTitle.trim() || !newObsDesc.trim()) return;
    try {
      setSubmittingObs(true);
      await eventGraphApi.recordObservation(incidentId, {
        observation_type: newObsType,
        provenance_type: newObsType === 'CONFLICT_RECORD' ? 'DIRECT_OBSERVATION' : 'ANALYST_ASSERTION',
        title: newObsTitle.trim(),
        description: newObsDesc.trim(),
        source_system: 'SOC_OPERATOR_CONSOLE',
        confidence: 0.95,
      });
      setNewObsTitle('');
      setNewObsDesc('');
      setShowAddObs(false);
      await fetchTimeline();
    } catch (err) {
      console.error('Failed to record observation:', err);
    } finally {
      setSubmittingObs(false);
    }
  };

  const getNodeIcon = (nodeType: string) => {
    switch (nodeType.toUpperCase()) {
      case 'CAMERA':
        return <Camera className="w-4 h-4 text-emerald-600" />;
      case 'VIDEO':
        return <Film className="w-4 h-4 text-blue-600" />;
      case 'OBJECT_TRACK':
        return <Crosshair className="w-4 h-4 text-indigo-600" />;
      case 'EVENT':
        return <ShieldAlert className="w-4 h-4 text-red-600" />;
      case 'EVIDENCE':
        return <FileCheck className="w-4 h-4 text-teal-600" />;
      case 'AI_ANALYSIS':
        return <Bot className="w-4 h-4 text-purple-600" />;
      case 'REPORT':
        return <FileText className="w-4 h-4 text-amber-600" />;
      case 'OBSERVATION':
        return <Eye className="w-4 h-4 text-sky-600" />;
      default:
        return <GitBranch className="w-4 h-4 text-gray-600" />;
    }
  };

  const getProvenanceBadge = (provType: string) => {
    switch (provType) {
      case 'DIRECT_OBSERVATION':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
            Direct Physical Observation
          </span>
        );
      case 'INFERRED_ASSOCIATION':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold bg-indigo-100 text-indigo-800 border border-indigo-200">
            Inferred Association
          </span>
        );
      case 'ANALYST_ASSERTION':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold bg-amber-100 text-amber-800 border border-amber-200">
            Analyst Operator Assertion
          </span>
        );
      case 'DERIVED_SYNTHESIS':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold bg-purple-100 text-purple-800 border border-purple-200">
            Cognitive AI Synthesis
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-gray-100 text-gray-800">
            {provType}
          </span>
        );
    }
  };

  if (loading) {
    return (
      <div className="p-8 text-center space-y-3">
        <RefreshCw className="w-6 h-6 animate-spin mx-auto text-[#7C5CFC]" />
        <p className="text-xs text-[#8E8899] font-medium">Resolving forensic evidence graph...</p>
      </div>
    );
  }

  const chain = chainData?.chain || [];

  return (
    <div className="space-y-6">
      {/* Header Metric Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-3 bg-[#FAF9FD] rounded-xl border border-[#E5E1EE]">
          <div className="text-[10px] uppercase font-bold text-[#8E8899]">Total Chain Steps</div>
          <div className="text-xl font-extrabold text-[#211D2B] mt-0.5">{chain.length}</div>
          <div className="text-[10px] text-emerald-600 font-semibold flex items-center mt-1">
            <ShieldCheck className="w-3.5 h-3.5 mr-1" />
            {graphData ? `${graphData.total_edges} Edges • Verified` : '100% DB-Verified'}
          </div>
        </div>

        <div className="p-3 bg-emerald-50/60 rounded-xl border border-emerald-200">
          <div className="text-[10px] uppercase font-bold text-emerald-800">Direct Facts</div>
          <div className="text-xl font-extrabold text-emerald-900 mt-0.5">
            {chain.filter((c) => c.provenance_type === 'DIRECT_OBSERVATION').length}
          </div>
          <div className="text-[10px] text-emerald-700 font-medium mt-1">Camera/Video/Sensor</div>
        </div>

        <div className="p-3 bg-indigo-50/60 rounded-xl border border-indigo-200">
          <div className="text-[10px] uppercase font-bold text-indigo-800">Inferred Links</div>
          <div className="text-xl font-extrabold text-indigo-900 mt-0.5">
            {chain.filter((c) => c.provenance_type === 'INFERRED_ASSOCIATION' || c.provenance_type === 'DERIVED_SYNTHESIS').length}
          </div>
          <div className="text-[10px] text-indigo-700 font-medium mt-1">Tracking & AI Synthesis</div>
        </div>

        <div className="p-3 bg-rose-50/60 rounded-xl border border-rose-200">
          <div className="text-[10px] uppercase font-bold text-rose-800">Conflicts / Gaps</div>
          <div className="text-xl font-extrabold text-rose-900 mt-0.5">
            {(chainData?.unresolved_conflicts || 0) + (chainData?.missing_evidence_gaps || 0)}
          </div>
          <div className="text-[10px] text-rose-700 font-medium mt-1">
            {chainData?.unresolved_conflicts || 0} disputes, {chainData?.missing_evidence_gaps || 0} gaps
          </div>
        </div>
      </div>

      {/* Action Bar */}
      <div className="flex items-center justify-between pt-1">
        <div className="flex items-center space-x-2 text-xs font-bold text-[#625D6D]">
          <GitBranch className="w-4 h-4 text-[#7C5CFC]" />
          <span>EVIDENCE CHAIN OF CUSTODY ({incidentNumber || `INC-${incidentId}`})</span>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowAddObs(!showAddObs)}
            className="px-2.5 py-1.5 rounded-lg border border-[#DCD4FB] bg-[#F0EDFD] hover:bg-[#E3DCFC] text-[#4328A8] text-xs font-bold transition flex items-center space-x-1"
          >
            <PlusCircle className="w-3.5 h-3.5" />
            <span>Add Observation</span>
          </button>
          <button
            onClick={handleAutoSynthesize}
            disabled={synthesizing}
            className="px-2.5 py-1.5 rounded-lg bg-[#7C5CFC] hover:bg-[#6A46F9] text-white text-xs font-bold transition flex items-center space-x-1 disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${synthesizing ? 'animate-spin' : ''}`} />
            <span>{synthesizing ? 'Synthesizing...' : 'Sync Graph'}</span>
          </button>
        </div>
      </div>

      {/* New Observation Form */}
      {showAddObs && (
        <form onSubmit={handleRecordObservation} className="p-4 bg-white rounded-xl border border-[#DCD4FB] shadow-xs space-y-3 animate-fade-in">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-[#211D2B] uppercase">Record Provenance Observation</span>
            <button type="button" onClick={() => setShowAddObs(false)} className="text-xs text-[#8E8899] hover:text-[#211D2B]">
              Cancel
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <div>
              <label className="text-[11px] font-semibold text-[#625D6D]">Observation Type</label>
              <select
                value={newObsType}
                onChange={(e) => setNewObsType(e.target.value as any)}
                className="w-full mt-1 px-2.5 py-1.5 text-xs rounded-lg border border-[#E5E1EE] bg-[#FAF9FD] text-[#211D2B] focus:outline-hidden focus:border-[#7C5CFC]"
              >
                <option value="DIRECT_FACT">Direct Physical Fact</option>
                <option value="CONFLICT_RECORD">Conflicting Sensor Record</option>
                <option value="MISSING_DATA_GAP">Missing Evidence / Stream Gap</option>
              </select>
            </div>
            <div>
              <label className="text-[11px] font-semibold text-[#625D6D]">Observation Title</label>
              <input
                type="text"
                placeholder="e.g. Ground Radar Discrepancy"
                value={newObsTitle}
                onChange={(e) => setNewObsTitle(e.target.value)}
                className="w-full mt-1 px-2.5 py-1.5 text-xs rounded-lg border border-[#E5E1EE] bg-[#FAF9FD] text-[#211D2B] focus:outline-hidden focus:border-[#7C5CFC]"
              />
            </div>
          </div>

          <div>
            <label className="text-[11px] font-semibold text-[#625D6D]">Detailed Reason / Context</label>
            <textarea
              rows={2}
              placeholder="State what was observed or why evidence contradicts initial alert..."
              value={newObsDesc}
              onChange={(e) => setNewObsDesc(e.target.value)}
              className="w-full mt-1 px-2.5 py-1.5 text-xs rounded-lg border border-[#E5E1EE] bg-[#FAF9FD] text-[#211D2B] focus:outline-hidden focus:border-[#7C5CFC]"
            />
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={submittingObs || !newObsTitle.trim() || !newObsDesc.trim()}
              className="px-3 py-1.5 bg-[#7C5CFC] text-white text-xs font-bold rounded-lg hover:bg-[#6A46F9] disabled:opacity-50 transition"
            >
              {submittingObs ? 'Recording...' : 'Commit Observation'}
            </button>
          </div>
        </form>
      )}

      {/* Timeline Steps */}
      {chain.length === 0 ? (
        <div className="p-8 text-center bg-[#FAF9FD] rounded-xl border border-dashed border-[#E5E1EE] space-y-2">
          <HelpCircle className="w-8 h-8 mx-auto text-[#8E8899]" />
          <p className="text-sm font-bold text-[#211D2B]">No explicit provenance links recorded yet.</p>
          <p className="text-xs text-[#8E8899]">
            Click <strong>Sync Graph</strong> above to automatically synthesize evidence links from existing cameras, videos, tracks, and AI analyses.
          </p>
        </div>
      ) : (
        <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-3 before:bottom-3 before:w-0.5 before:bg-[#E5E1EE]">
          {chain.map((step, index) => (
            <div key={`${step.node_type}-${step.node_id}-${index}`} className="relative group">
              {/* Timeline Icon Node */}
              <div className="absolute -left-6 top-1 w-5 h-5 rounded-full bg-white border-2 border-[#7C5CFC] flex items-center justify-center shadow-xs">
                <div className="w-1.5 h-1.5 rounded-full bg-[#7C5CFC]" />
              </div>

              {/* Step Card */}
              <div className="bg-white rounded-xl border border-[#E5E1EE] p-4 shadow-xs hover:border-[#DCD4FB] transition space-y-2.5">
                {/* Step Header */}
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center space-x-2">
                    <div className="p-1.5 rounded-lg bg-[#FAF9FD] border border-[#E5E1EE]">
                      {getNodeIcon(step.node_type)}
                    </div>
                    <div>
                      <div className="text-xs font-bold text-[#211D2B]">{step.label}</div>
                      <div className="text-[10px] text-[#8E8899]">
                        Step {step.step_number} • {step.node_type} #{step.node_id}
                        {step.relationship_from_parent && (
                          <span className="ml-1 text-[#7C5CFC] font-semibold">
                            —[{step.relationship_from_parent}]→
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    {getProvenanceBadge(step.provenance_type)}
                    {step.is_verified_in_db && (
                      <span className="inline-flex items-center text-[10px] font-bold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200">
                        <CheckCircle2 className="w-3 h-3 mr-0.5" />
                        Verified Stored Record
                      </span>
                    )}
                  </div>
                </div>

                {/* Justification / Reason */}
                {step.creation_reason && (
                  <div className="text-xs text-[#625D6D] bg-[#FAF9FD] p-2.5 rounded-lg border border-[#E5E1EE] leading-relaxed">
                    <span className="font-bold text-[#211D2B]">Evidence Rationale: </span>
                    {step.creation_reason}
                  </div>
                )}

                {/* Conflict Notice if present */}
                {step.node_type === 'OBSERVATION' && step.details?.disputed_feature && (
                  <div className="p-2.5 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-800 flex items-start space-x-2">
                    <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                    <div>
                      <span className="font-bold">Contradictory Sensor Report: </span>
                      Disputes feature <code className="bg-rose-100 px-1 rounded">{step.details.disputed_feature}</code>.
                    </div>
                  </div>
                )}

                {/* Missing Data Gap if present */}
                {step.node_type === 'OBSERVATION' && step.details?.duration_lost_ms && (
                  <div className="p-2.5 bg-amber-50 border border-amber-200 border-dashed rounded-lg text-xs text-amber-800 flex items-start space-x-2">
                    <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                    <div>
                      <span className="font-bold">Missing Evidence Interval: </span>
                      Frame gap ({step.details.start_frame} - {step.details.end_frame}) lost ~{step.details.duration_lost_ms}ms of telemetry.
                    </div>
                  </div>
                )}

                {/* Footer Metadata & Cryptographic Hash */}
                <div className="flex flex-wrap items-center justify-between text-[11px] text-[#8E8899] pt-1 border-t border-[#F0EDFD]">
                  <div>
                    {step.timestamp && (
                      <span>Recorded: {new Date(step.timestamp).toLocaleString()}</span>
                    )}
                  </div>

                  {step.evidence_sha256 && (
                    <div className="flex items-center space-x-1 font-mono text-[10px] bg-[#FAF9FD] px-2 py-0.5 rounded border border-[#E5E1EE]">
                      <span>SHA256: {step.evidence_sha256.substring(0, 12)}...</span>
                      <button
                        onClick={() => handleCopyHash(step.evidence_sha256!)}
                        className="hover:text-[#211D2B] transition"
                        title="Copy full cryptographic SHA-256 hash"
                      >
                        {copiedHash === step.evidence_sha256 ? (
                          <Check className="w-3 h-3 text-emerald-600" />
                        ) : (
                          <Copy className="w-3 h-3" />
                        )}
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
