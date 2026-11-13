import { useState, useEffect } from 'react';
import {
  FileText, Download, CheckCircle2, RefreshCw,
  Search, Plus, Clock, Sparkles, Filter
} from 'lucide-react';
import { reportApi, incidentApi } from '../services/sentinelApi';
import type { ReportResponse, Incident } from '../types';
import { EvidenceGroundedReportViewer } from '../components/EvidenceGroundedReportViewer';

export function ReportsPage() {
  const [reports, setReports] = useState<ReportResponse[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [selectedReport, setSelectedReport] = useState<ReportResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  // Generation Modal State
  const [generateModalOpen, setGenerateModalOpen] = useState(false);
  const [selectedIncidentId, setSelectedIncidentId] = useState<number | null>(null);
  const [customInstructions, setCustomInstructions] = useState('');
  const [forceMock, setForceMock] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [notification, setNotification] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      const incList = await incidentApi.list();
      setIncidents(incList);

      // Fetch reports for all incidents
      const reportPromises = incList.map(async (inc) => {
        try {
          return await reportApi.getByIncident(inc.id);
        } catch {
          return [];
        }
      });
      const reportsNested = await Promise.all(reportPromises);
      const allReports = reportsNested.flat();
      
      // Sort by creation date descending
      allReports.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
      setReports(allReports);
    } catch (err) {
      console.error('Failed to load reports:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleGenerateReport = async () => {
    if (!selectedIncidentId) return;
    try {
      setGenerating(true);
      const newRep = await reportApi.generate(selectedIncidentId, {
        customInstructions: customInstructions.trim() || undefined,
        forceMock,
      });
      setNotification(`Investigation Report #${newRep.report_number} generated successfully.`);
      setTimeout(() => setNotification(null), 6000);
      setGenerateModalOpen(false);
      setCustomInstructions('');
      await fetchData();
      setSelectedReport(newRep);
    } catch (err: any) {
      alert(`Report Generation Notice: ${err?.response?.data?.detail || err.message}`);
    } finally {
      setGenerating(false);
    }
  };

  const filteredReports = reports.filter((r) => {
    const matchesSearch =
      r.report_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (r.model_name && r.model_name.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesStatus =
      statusFilter === 'ALL' || r.review_status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="w-full space-y-6">
      {/* Top Banner / Notification */}
      {notification && (
        <div className="p-4 rounded-xl bg-[#DCFCE7] border border-[#86EFAC] text-[#166534] text-xs sm:text-sm font-bold flex items-center justify-between shadow-xs">
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
            <FileText className="w-7 h-7 text-[#7C5CFC]" />
            Evidence-Grounded Incident Dossiers
          </h1>
          <p className="text-sm text-[#625D6D] mt-1 font-medium">
            AI-generated forensic reports with strict database citation corroboration, 4-tier epistemic taxonomy, and human review sign-offs
          </p>
        </div>

        <div className="flex items-center space-x-3 shrink-0">
          <button
            onClick={fetchData}
            className="p-2.5 rounded-xl border border-[#E5E1EE] bg-white hover:bg-[#FAF9FD] text-[#625D6D] hover:text-[#211D2B] transition shadow-2xs"
            title="Refresh reports register"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>

          <button
            onClick={() => {
              if (incidents.length > 0) {
                setSelectedIncidentId(incidents[0].id);
              }
              setGenerateModalOpen(true);
            }}
            className="flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-[#7C5CFC] hover:bg-[#6846EB] text-white text-xs sm:text-sm font-bold shadow-xs transition"
          >
            <Plus className="w-4 h-4" />
            <span>Generate New Dossier</span>
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3 items-center justify-between bg-white p-4 rounded-xl border border-[#E5E1EE] shadow-2xs">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 absolute left-3 top-3 text-[#8E8899]" />
          <input
            type="text"
            placeholder="Search report #, title, or model..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-xs sm:text-sm rounded-lg border border-[#E5E1EE] focus:border-[#7C5CFC] focus:outline-hidden bg-[#FAF9FD]"
          />
        </div>

        <div className="flex items-center space-x-2 w-full sm:w-auto">
          <Filter className="w-4 h-4 text-[#8E8899]" />
          <span className="text-xs font-bold text-[#625D6D]">Review Status:</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs sm:text-sm px-3 py-1.5 rounded-lg border border-[#E5E1EE] bg-[#FAF9FD] text-[#211D2B] font-medium focus:border-[#7C5CFC] focus:outline-hidden"
          >
            <option value="ALL">All Statuses</option>
            <option value="APPROVED">Approved</option>
            <option value="PENDING_REVIEW">Pending Review</option>
            <option value="DRAFT">Draft</option>
            <option value="REJECTED">Rejected</option>
          </select>
        </div>
      </div>

      {/* Reports Grid */}
      {loading ? (
        <div className="py-20 text-center text-sm font-semibold text-[#8E8899] bg-white rounded-xl border border-[#E5E1EE]">
          <div className="w-8 h-8 mx-auto mb-3 rounded-full border-3 border-[#7C5CFC] border-t-transparent animate-spin"></div>
          Loading forensic dossiers...
        </div>
      ) : filteredReports.length === 0 ? (
        <div className="py-16 text-center bg-white rounded-xl border border-[#E5E1EE] p-8 space-y-3">
          <FileText className="w-12 h-12 text-[#DCD4FB] mx-auto" />
          <h3 className="text-base font-bold text-[#211D2B]">No Incident Dossiers Found</h3>
          <p className="text-xs text-[#625D6D] max-w-md mx-auto">
            No reports match the current filter. Select an incident and click "Generate New Dossier" to create an evidence-grounded report.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredReports.map((rep) => {
            const validPct = Math.round((rep.valid_citation_rate || 1.0) * 100);
            const isApproved = rep.review_status === 'APPROVED';
            const isPending = rep.review_status === 'PENDING_REVIEW';
            const isRejected = rep.review_status === 'REJECTED';

            return (
              <div
                key={rep.id}
                className="bg-white rounded-xl border border-[#E5E1EE] hover:border-[#7C5CFC] hover:shadow-md transition flex flex-col justify-between overflow-hidden group"
              >
                <div className="p-5 space-y-3.5">
                  <div className="flex items-start justify-between gap-2">
                    <span className="text-xs font-mono font-bold px-2 py-0.5 rounded-md bg-[#F0EDFD] text-[#4328A8]">
                      {rep.report_number}
                    </span>
                    <span
                      className={`text-xs font-extrabold px-2.5 py-0.5 rounded-full uppercase tracking-wider ${
                        isApproved
                          ? 'bg-[#DCFCE7] text-[#166534]'
                          : isPending
                          ? 'bg-[#FEF3C7] text-[#B45309]'
                          : isRejected
                          ? 'bg-[#FEE2E2] text-[#B91C1C]'
                          : 'bg-[#F3F4F6] text-[#4B5563]'
                      }`}
                    >
                      {rep.review_status.replace('_', ' ')}
                    </span>
                  </div>

                  <div>
                    <h3 className="text-base font-bold text-[#211D2B] group-hover:text-[#7C5CFC] transition line-clamp-1">
                      {rep.title}
                    </h3>
                    <p className="text-xs text-[#625D6D] mt-1 line-clamp-2">
                      {rep.sections?.executive_summary || 'Evidence-grounded border security incident dossier.'}
                    </p>
                  </div>

                  {/* Metrics Badges */}
                  <div className="grid grid-cols-2 gap-2 pt-2 border-t border-[#F0EDFD] text-xs">
                    <div className="p-2 rounded-lg bg-[#FAF9FD] border border-[#F0EDFD]">
                      <span className="text-[10px] uppercase font-bold text-[#8E8899] block">Database Citations</span>
                      <span className={`text-sm font-black ${validPct >= 90 ? 'text-[#16A34A]' : 'text-[#DC2626]'}`}>
                        {validPct}% Verified
                      </span>
                    </div>
                    <div className="p-2 rounded-lg bg-[#FAF9FD] border border-[#F0EDFD]">
                      <span className="text-[10px] uppercase font-bold text-[#8E8899] block">Evidence Files</span>
                      <span className="text-sm font-black text-[#211D2B]">
                        {rep.sections?.evidence_used?.length || 0} Corroborated
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-[#8E8899]">
                    <span className="flex items-center gap-1 font-mono">
                      <Sparkles className="w-3 h-3 text-[#7C5CFC]" />
                      {rep.model_name}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {new Date(rep.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>

                {/* Card Actions */}
                <div className="px-5 py-3 bg-[#FAF9FD] border-t border-[#E5E1EE] flex items-center justify-between">
                  <button
                    onClick={() => setSelectedReport(rep)}
                    className="text-xs font-bold text-[#7C5CFC] hover:text-[#5B3BC4] flex items-center gap-1.5 transition"
                  >
                    <FileText className="w-3.5 h-3.5" />
                    Inspect Dossier
                  </button>

                  <a
                    href={reportApi.getPdfDownloadUrl(rep.id)}
                    target="_blank"
                    rel="noreferrer"
                    className="p-1.5 rounded-lg border border-[#E5E1EE] hover:border-[#7C5CFC] bg-white text-[#625D6D] hover:text-[#7C5CFC] transition"
                    title="Export PDF Dossier"
                  >
                    <Download className="w-4 h-4" />
                  </a>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Generation Modal */}
      {generateModalOpen && (
        <div className="fixed inset-0 z-50 bg-[#211D2B]/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl border border-[#E5E1EE] space-y-4 animate-scale-in">
            <div className="flex items-center justify-between pb-3 border-b border-[#E5E1EE]">
              <div className="flex items-center space-x-2">
                <Sparkles className="w-5 h-5 text-[#7C5CFC]" />
                <h3 className="text-lg font-extrabold text-[#211D2B]">Generate Grounded Dossier</h3>
              </div>
              <button
                onClick={() => setGenerateModalOpen(false)}
                className="text-[#8E8899] hover:text-[#211D2B] text-lg font-bold"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="text-xs font-bold text-[#625D6D] block mb-1.5">Target Security Incident</label>
                <select
                  value={selectedIncidentId || ''}
                  onChange={(e) => setSelectedIncidentId(Number(e.target.value))}
                  className="w-full text-xs sm:text-sm p-2.5 rounded-xl border border-[#E5E1EE] bg-[#FAF9FD] text-[#211D2B] font-medium focus:border-[#7C5CFC] focus:outline-hidden"
                >
                  {incidents.map((inc) => (
                    <option key={inc.id} value={inc.id}>
                      {inc.incident_number} — {inc.title} ({inc.severity})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs font-bold text-[#625D6D] block mb-1.5">
                  Analyst Custom Directives (Optional)
                </label>
                <textarea
                  rows={3}
                  placeholder="e.g., Emphasize tripwire crossing timing and corroborate thermal sensor signatures..."
                  value={customInstructions}
                  onChange={(e) => setCustomInstructions(e.target.value)}
                  className="w-full text-xs sm:text-sm p-3 rounded-xl border border-[#E5E1EE] bg-[#FAF9FD] text-[#211D2B] placeholder-[#8E8899] focus:border-[#7C5CFC] focus:outline-hidden"
                />
              </div>

              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="forceMock"
                  checked={forceMock}
                  onChange={(e) => setForceMock(e.target.checked)}
                  className="w-4 h-4 rounded text-[#7C5CFC] focus:ring-[#7C5CFC] border-[#E5E1EE]"
                />
                <label htmlFor="forceMock" className="text-xs font-semibold text-[#625D6D]">
                  Use Mock Structured Synthesis (Local deterministic validation)
                </label>
              </div>
            </div>

            <div className="flex items-center justify-end space-x-3 pt-4 border-t border-[#E5E1EE]">
              <button
                onClick={() => setGenerateModalOpen(false)}
                className="px-4 py-2 rounded-xl text-xs font-bold text-[#625D6D] hover:bg-[#FAF9FD] transition"
              >
                Cancel
              </button>
              <button
                onClick={handleGenerateReport}
                disabled={generating || !selectedIncidentId}
                className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-[#7C5CFC] hover:bg-[#6846EB] text-white text-xs sm:text-sm font-bold shadow-xs transition disabled:opacity-50"
              >
                {generating ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Synthesizing Dossier...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    <span>Generate Dossier</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Detailed Modal Viewer */}
      {selectedReport && (
        <EvidenceGroundedReportViewer
          initialReport={selectedReport}
          onClose={() => setSelectedReport(null)}
          onReportUpdated={(updated) => {
            setSelectedReport(updated);
            fetchData();
          }}
        />
      )}
    </div>
  );
}
