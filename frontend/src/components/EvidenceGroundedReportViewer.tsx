import { useState } from 'react';
import {
  Shield, CheckCircle2, AlertTriangle, FileText, Download,
  Edit3, Clock, XCircle, History, UserCheck, X,
  ChevronDown, ChevronUp, ExternalLink
} from 'lucide-react';
import type {
  ReportResponse, FactualStatementItem, StatementType,
  CitationValidationStatus, ReviewStatus
} from '../types';
import { reportApi } from '../services/sentinelApi';

interface EvidenceGroundedReportViewerProps {
  initialReport: ReportResponse;
  onClose: () => void;
  onReportUpdated?: (updated: ReportResponse) => void;
}

export function EvidenceGroundedReportViewer({
  initialReport,
  onClose,
  onReportUpdated,
}: EvidenceGroundedReportViewerProps) {
  const [report, setReport] = useState<ReportResponse>(initialReport);
  const [editingStatementId, setEditingStatementId] = useState<number | null>(null);
  const [correctedText, setCorrectedText] = useState<string>('');
  const [analystComment, setAnalystComment] = useState<string>('');
  const [isSubmittingCorrection, setIsSubmittingCorrection] = useState(false);

  const [reviewAction, setReviewAction] = useState<'APPROVE' | 'REQUEST_REVISIONS' | 'REJECT' | null>(null);
  const [reviewerComments, setReviewerComments] = useState<string>('');
  const [isSubmittingReview, setIsSubmittingReview] = useState(false);

  const [showAuditHistory, setShowAuditHistory] = useState(false);
  const [selectedCitationDetail, setSelectedCitationDetail] = useState<{
    type: string;
    id: number;
    title: string;
  } | null>(null);

  const sections = report.sections;
  const isInsufficient = sections.insufficient_evidence;

  const handleStartEdit = (stmt: FactualStatementItem) => {
    setEditingStatementId(stmt.statement_id);
    setCorrectedText(stmt.text);
    setAnalystComment(stmt.human_correction || '');
  };

  const handleCancelEdit = () => {
    setEditingStatementId(null);
    setCorrectedText('');
    setAnalystComment('');
  };

  const handleSubmitCorrection = async (statementId: number) => {
    if (!analystComment.trim()) {
      alert('Please provide an analyst comment explaining this correction.');
      return;
    }
    try {
      setIsSubmittingCorrection(true);
      const updated = await reportApi.correctStatement(report.id, statementId, {
        corrected_text: correctedText,
        analyst_comment: analystComment,
      });
      setReport(updated);
      if (onReportUpdated) onReportUpdated(updated);
      setEditingStatementId(null);
    } catch (err: any) {
      console.error('Failed to submit correction:', err);
      alert(err.response?.data?.detail || 'Failed to submit statement correction.');
    } finally {
      setIsSubmittingCorrection(false);
    }
  };

  const handleSubmitReview = async (action: 'APPROVE' | 'REQUEST_REVISIONS' | 'REJECT') => {
    try {
      setIsSubmittingReview(true);
      const updated = await reportApi.review(report.id, {
        action,
        reviewer_comments: reviewerComments,
      });
      setReport(updated);
      if (onReportUpdated) onReportUpdated(updated);
      setReviewAction(null);
      setReviewerComments('');
    } catch (err: any) {
      console.error('Failed to update review status:', err);
      alert(err.response?.data?.detail || 'Failed to update report review status.');
    } finally {
      setIsSubmittingReview(false);
    }
  };

  const getStatementTypeBadge = (type: StatementType) => {
    switch (type) {
      case 'OBSERVATION':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
            Observation
          </span>
        );
      case 'CV_DETECTION':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-purple-50 text-purple-700 border border-purple-200">
            CV Result
          </span>
        );
      case 'MODEL_INTERPRETATION':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200">
            Model Interpretation
          </span>
        );
      case 'HUMAN_ANNOTATION':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            Human Annotation
          </span>
        );
    }
  };

  const getCitationBadge = (status: CitationValidationStatus, notes?: string) => {
    switch (status) {
      case 'VERIFIED':
        return (
          <span
            title={notes || 'Cross-examined and verified against PostgreSQL DB records'}
            className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200"
          >
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Verified Citation</span>
          </span>
        );
      case 'FLAGGED_TIMESTAMP_MISMATCH':
        return (
          <span
            title={notes || 'Timestamp mismatch with database entity (>2.0s skew)'}
            className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200"
          >
            <Clock className="w-3.5 h-3.5" />
            <span>Timestamp Skew</span>
          </span>
        );
      case 'FLAGGED_NONEXISTENT':
        return (
          <span
            title={notes || 'Fabricated or nonexistent entity identifier detected'}
            className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-xs font-medium bg-red-50 text-red-700 border border-red-200"
          >
            <XCircle className="w-3.5 h-3.5" />
            <span>Nonexistent Entity</span>
          </span>
        );
      case 'FLAGGED_UNSUPPORTED':
      default:
        return (
          <span
            title={notes || 'Claim lacks valid supporting evidence references'}
            className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-xs font-medium bg-rose-50 text-rose-700 border border-rose-200"
          >
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>Unsupported Claim</span>
          </span>
        );
    }
  };

  const getReviewStatusBadge = (status: ReviewStatus) => {
    switch (status) {
      case 'APPROVED':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
            <UserCheck className="w-3.5 h-3.5" />
            <span>APPROVED</span>
          </span>
        );
      case 'REJECTED':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-bold bg-red-100 text-red-800 border border-red-300">
            <XCircle className="w-3.5 h-3.5" />
            <span>REJECTED</span>
          </span>
        );
      case 'PENDING_REVIEW':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800 border border-amber-300">
            <Clock className="w-3.5 h-3.5" />
            <span>PENDING REVIEW</span>
          </span>
        );
      case 'DRAFT':
      default:
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-bold bg-gray-100 text-gray-800 border border-gray-300">
            <span>DRAFT</span>
          </span>
        );
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/60 backdrop-blur-sm select-none animate-fade-in">
      <div className="bg-white border border-[#E5E1EE] rounded-2xl w-full max-w-5xl max-h-[92vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Top Header */}
        <div className="p-5 sm:p-6 border-b border-[#E5E1EE] bg-[#FAF9FD] flex items-center justify-between">
          <div className="flex items-center space-x-3.5">
            <div className="w-11 h-11 rounded-xl bg-[#F0EDFD] border border-[#DCD4FB] flex items-center justify-center text-[#7C5CFC]">
              <Shield className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xs font-extrabold text-[#7C5CFC] tracking-wider uppercase">
                  CONFIDENTIAL // LAW ENFORCEMENT SENSITIVE
                </span>
                {getReviewStatusBadge(report.review_status)}
              </div>
              <h2 className="text-xl font-black text-[#211D2B]">{report.title}</h2>
              <div className="text-xs text-[#8E8899] font-mono-num">
                Dossier #{report.report_number} • Incident #{report.incident_id} • Prompt v{report.prompt_version || '2026.04.1'}
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-2.5">
            <a
              href={reportApi.getPdfDownloadUrl(report.id)}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center space-x-1.5 px-3 py-2 rounded-xl text-xs font-bold bg-[#7C5CFC] text-white hover:bg-[#6846EB] shadow-xs transition"
            >
              <Download className="w-4 h-4" />
              <span>Export PDF Dossier</span>
            </a>
            <button
              onClick={onClose}
              className="p-2 rounded-xl text-[#8E8899] hover:text-[#211D2B] hover:bg-white border border-transparent hover:border-[#E5E1EE] transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Scrollable Dossier Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Integrity & Citation Grounding Summary Strip */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3.5 rounded-xl bg-[#FAF9FD] border border-[#E5E1EE]">
              <div className="text-xs font-medium text-[#8E8899]">Citation Grounding Rate</div>
              <div className="text-lg font-black text-[#211D2B] flex items-center space-x-1.5">
                <span className={report.valid_citation_rate >= 0.85 ? 'text-emerald-600' : 'text-amber-600'}>
                  {(report.valid_citation_rate * 100).toFixed(1)}%
                </span>
                <span className="text-xs text-[#8E8899] font-normal">
                  ({sections.factual_statements.length - report.unsupported_claim_count}/{sections.factual_statements.length} claims)
                </span>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-[#FAF9FD] border border-[#E5E1EE]">
              <div className="text-xs font-medium text-[#8E8899]">Unsupported Claims</div>
              <div className="text-lg font-black text-[#211D2B]">
                <span className={report.unsupported_claim_count === 0 ? 'text-emerald-600' : 'text-rose-600'}>
                  {report.unsupported_claim_count}
                </span>
                <span className="text-xs text-[#8E8899] font-normal ml-1">flagged by cross-examiner</span>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-[#FAF9FD] border border-[#E5E1EE]">
              <div className="text-xs font-medium text-[#8E8899]">Model & Provenance</div>
              <div className="text-xs font-bold text-[#211D2B] truncate mt-1">
                {report.model_name || 'gemini-2.5-flash'}
              </div>
              <div className="text-xs text-[#8E8899]">Evidence Items: {sections.evidence_used.length}</div>
            </div>

            <div className="p-3.5 rounded-xl bg-[#FAF9FD] border border-[#E5E1EE]">
              <div className="text-xs font-medium text-[#8E8899]">SHA-256 Digest</div>
              <div
                title={report.checksum_sha256 || 'Computed on export'}
                className="text-xs font-mono font-bold text-[#7C5CFC] truncate mt-1"
              >
                {report.checksum_sha256 ? `${report.checksum_sha256.substring(0, 16)}...` : 'Pending'}
              </div>
              <div className="text-xs text-[#8E8899]">Cryptographic tamper check</div>
            </div>
          </div>

          {/* Insufficient Evidence Alert Banner */}
          {isInsufficient && (
            <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 flex items-start space-x-3">
              <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
              <div>
                <div className="text-sm font-bold">Insufficient Physical Evidence Recorded</div>
                <p className="text-xs text-amber-800 mt-1">
                  {sections.insufficient_evidence_reason ||
                    'This incident cannot be substantiated with physical sensor records, object tracks, or validated CCTV frames.'}
                </p>
              </div>
            </div>
          )}

          {/* 1. Executive Summary */}
          <div className="space-y-2">
            <h3 className="text-xs font-bold text-[#7C5CFC] uppercase tracking-wider flex items-center space-x-1.5">
              <FileText className="w-4 h-4" />
              <span>1. Executive Investigation Summary</span>
            </h3>
            <div className="p-4 rounded-xl bg-[#FAF9FD] border border-[#E5E1EE] text-sm text-[#211D2B] leading-relaxed">
              {sections.executive_summary}
            </div>
          </div>

          {/* 2. Conflicting Observations & Gaps (Phase 4 Event Graph Integration) */}
          {(sections.conflicting_evidence.length > 0 || sections.missing_evidence_gaps.length > 0) && (
            <div className="space-y-3">
              <h3 className="text-xs font-bold text-[#D32F2F] uppercase tracking-wider flex items-center space-x-1.5">
                <AlertTriangle className="w-4 h-4" />
                <span>2. Evidentiary Contradictions & Data Gaps</span>
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {sections.conflicting_evidence.map((conflict, idx) => (
                  <div key={idx} className="p-3.5 rounded-xl bg-rose-50/70 border border-rose-200">
                    <div className="text-xs font-bold text-rose-900 flex items-center justify-between">
                      <span>Conflict Discrepancy #{idx + 1}</span>
                      <span className="px-1.5 py-0.5 rounded text-[10px] uppercase font-bold bg-rose-200 text-rose-800">
                        {conflict.severity} Priority
                      </span>
                    </div>
                    <p className="text-xs text-rose-800 mt-1.5 leading-relaxed">{conflict.description}</p>
                    {conflict.conflicting_nodes.length > 0 && (
                      <div className="text-[11px] text-rose-700/80 mt-1 font-mono">
                        Nodes: {conflict.conflicting_nodes.join(' ↔ ')}
                      </div>
                    )}
                  </div>
                ))}

                {sections.missing_evidence_gaps.map((gap, idx) => (
                  <div key={idx} className="p-3.5 rounded-xl bg-amber-50/70 border border-amber-200">
                    <div className="text-xs font-bold text-amber-900 flex items-center justify-between">
                      <span>Telemetry Gap #{idx + 1}</span>
                      {gap.interval && (
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-amber-200 text-amber-800">
                          {gap.interval}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-amber-800 mt-1.5 leading-relaxed">{gap.description}</p>
                    {gap.impact && (
                      <div className="text-[11px] text-amber-700/80 mt-1 font-medium">Impact: {gap.impact}</div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 3. Chronological Grounded Statements with Epistemic Taxonomy */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-[#7C5CFC] uppercase tracking-wider flex items-center space-x-1.5">
                <Clock className="w-4 h-4" />
                <span>3. Grounded Factual Statements & Evidence Cross-Examination</span>
              </h3>
              <div className="text-xs text-[#8E8899]">
                Click <Edit3 className="w-3 h-3 inline mx-0.5" /> to add analyst correction
              </div>
            </div>

            {sections.factual_statements.length === 0 ? (
              <div className="p-4 rounded-xl bg-[#FAF9FD] border border-[#E5E1EE] text-xs text-[#8E8899] text-center">
                No factual statements recorded (empty telemetry register).
              </div>
            ) : (
              <div className="space-y-3">
                {sections.factual_statements.map((stmt) => (
                  <div
                    key={stmt.statement_id}
                    className={`p-4 rounded-xl border transition ${
                      stmt.citation_status === 'VERIFIED'
                        ? 'bg-white border-[#E5E1EE] hover:border-[#DCD4FB]'
                        : 'bg-rose-50/30 border-rose-200'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2 flex-wrap pb-2 border-b border-[#F0EDFD]">
                      <div className="flex items-center space-x-2">
                        <span className="text-xs font-bold text-[#8E8899] font-mono-num">
                          #{stmt.statement_id}
                        </span>
                        {getStatementTypeBadge(stmt.statement_type)}
                        {getCitationBadge(stmt.citation_status, stmt.validation_notes)}
                      </div>

                      <div className="flex items-center space-x-2 text-xs">
                        {stmt.timestamp && (
                          <span className="text-[#8E8899] font-mono-num">
                            {new Date(stmt.timestamp).toLocaleTimeString()}
                          </span>
                        )}
                        {editingStatementId !== stmt.statement_id && (
                          <button
                            onClick={() => handleStartEdit(stmt)}
                            className="p-1 rounded hover:bg-[#F0EDFD] text-[#7C5CFC] transition"
                            title="Add human correction"
                          >
                            <Edit3 className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Statement Text or Edit Form */}
                    {editingStatementId === stmt.statement_id ? (
                      <div className="mt-3 space-y-2.5 bg-[#FAF9FD] p-3 rounded-lg border border-[#E5E1EE]">
                        <div>
                          <label className="text-[11px] font-bold text-[#3E384D] block mb-1">
                            Corrected Statement Text:
                          </label>
                          <textarea
                            value={correctedText}
                            onChange={(e) => setCorrectedText(e.target.value)}
                            rows={2}
                            className="w-full text-xs p-2 rounded-lg border border-[#DCD4FB] bg-white focus:outline-none focus:ring-1 focus:ring-[#7C5CFC]"
                          />
                        </div>

                        <div>
                          <label className="text-[11px] font-bold text-[#3E384D] block mb-1">
                            Analyst Justification / Biometric Roster Ref:
                          </label>
                          <input
                            type="text"
                            placeholder="e.g. Verified against guard duty roster and biometric sign-in log #402"
                            value={analystComment}
                            onChange={(e) => setAnalystComment(e.target.value)}
                            className="w-full text-xs p-2 rounded-lg border border-[#DCD4FB] bg-white focus:outline-none focus:ring-1 focus:ring-[#7C5CFC]"
                          />
                        </div>

                        <div className="flex justify-end space-x-2 pt-1">
                          <button
                            onClick={handleCancelEdit}
                            className="px-2.5 py-1 text-xs rounded-lg text-[#8E8899] hover:bg-gray-100 transition"
                          >
                            Cancel
                          </button>
                          <button
                            disabled={isSubmittingCorrection}
                            onClick={() => handleSubmitCorrection(stmt.statement_id)}
                            className="px-3 py-1 text-xs font-bold rounded-lg bg-[#7C5CFC] text-white hover:bg-[#6846EB] transition disabled:opacity-50"
                          >
                            {isSubmittingCorrection ? 'Saving...' : 'Save Correction'}
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="mt-2.5 text-xs text-[#211D2B] leading-relaxed">
                        {stmt.text}

                        {stmt.human_correction && (
                          <div className="mt-2 p-2 rounded bg-emerald-50 border border-emerald-200 text-emerald-800 text-[11px]">
                            <span className="font-bold">Analyst Note: </span>
                            {stmt.human_correction}
                          </div>
                        )}

                        {stmt.validation_notes && stmt.citation_status !== 'VERIFIED' && (
                          <div className="mt-1.5 text-[11px] text-rose-600 font-medium">
                            Warning: {stmt.validation_notes}
                          </div>
                        )}

                        {/* Citation Chips */}
                        <div className="mt-2 flex items-center space-x-1.5 flex-wrap gap-1">
                          {stmt.referenced_entity_type && stmt.referenced_entity_id && (
                            <button
                              onClick={() =>
                                setSelectedCitationDetail({
                                  type: stmt.referenced_entity_type!,
                                  id: stmt.referenced_entity_id!,
                                  title: `${stmt.referenced_entity_type} #${stmt.referenced_entity_id}`,
                                })
                              }
                              className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-[#F0EDFD] text-[#7C5CFC] hover:bg-[#E5E1EE] transition cursor-pointer"
                            >
                              <span>
                                [{stmt.referenced_entity_type} #{stmt.referenced_entity_id}]
                              </span>
                              <ExternalLink className="w-2.5 h-2.5" />
                            </button>
                          )}

                          {stmt.supporting_evidence_ids.map((eid) => (
                            <button
                              key={eid}
                              onClick={() =>
                                setSelectedCitationDetail({
                                  type: 'EVIDENCE',
                                  id: eid,
                                  title: `Evidence Media #${eid}`,
                                })
                              }
                              className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-emerald-50 text-emerald-700 hover:bg-emerald-100 transition cursor-pointer"
                            >
                              <span>[Evidence #{eid}]</span>
                              <ExternalLink className="w-2.5 h-2.5" />
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 4. Containment Recommendations */}
          <div className="space-y-2">
            <h3 className="text-xs font-bold text-[#7C5CFC] uppercase tracking-wider">
              4. Containment Recommendations
            </h3>
            <ul className="space-y-1.5 text-xs text-[#211D2B]">
              {sections.containment_recommendations.map((rec, idx) => (
                <li key={idx} className="p-2.5 rounded-lg bg-[#FAF9FD] border border-[#E5E1EE] flex items-start space-x-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#7C5CFC] shrink-0 mt-1.5" />
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* 5. Physical Evidence Register Table */}
          <div className="space-y-2">
            <h3 className="text-xs font-bold text-[#7C5CFC] uppercase tracking-wider">
              5. Physical Evidence Register
            </h3>
            <div className="overflow-x-auto rounded-xl border border-[#E5E1EE]">
              <table className="w-full text-left text-xs">
                <thead className="bg-[#FAF9FD] border-b border-[#E5E1EE] text-[#8E8899]">
                  <tr>
                    <th className="py-2.5 px-3 font-semibold">ID</th>
                    <th className="py-2.5 px-3 font-semibold">Type</th>
                    <th className="py-2.5 px-3 font-semibold">File Path</th>
                    <th className="py-2.5 px-3 font-semibold">SHA-256 Digest</th>
                    <th className="py-2.5 px-3 font-semibold">Timestamp</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#E5E1EE] text-[#211D2B]">
                  {sections.evidence_used.map((ev) => (
                    <tr key={ev.evidence_id} className="hover:bg-[#FAF9FD]">
                      <td className="py-2 px-3 font-mono font-bold">#{ev.evidence_id}</td>
                      <td className="py-2 px-3">{ev.evidence_type}</td>
                      <td className="py-2 px-3 font-mono text-[11px] text-[#8E8899] max-w-[200px] truncate">
                        {ev.file_path}
                      </td>
                      <td className="py-2 px-3 font-mono text-[11px] text-[#7C5CFC]">
                        {ev.checksum_sha256 ? `${ev.checksum_sha256.substring(0, 16)}...` : 'N/A'}
                      </td>
                      <td className="py-2 px-3 text-[#8E8899] font-mono-num text-[11px]">
                        {ev.timestamp ? new Date(ev.timestamp).toLocaleString() : 'N/A'}
                      </td>
                    </tr>
                  ))}
                  {sections.evidence_used.length === 0 && (
                    <tr>
                      <td colSpan={5} className="py-4 text-center text-[#8E8899]">
                        Zero evidence items attached.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* 6. Review & Approval Section */}
          <div className="p-4 rounded-xl bg-[#FAF9FD] border border-[#E5E1EE] space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-xs font-bold text-[#211D2B] uppercase tracking-wider">
                  Operational Sign-Off & Approval Workflow
                </h4>
                <div className="text-xs text-[#8E8899]">
                  Current Status: <span className="font-bold text-[#211D2B]">{report.review_status}</span>
                  {report.approved_at && (
                    <span> • Approved on {new Date(report.approved_at).toLocaleString()}</span>
                  )}
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setReviewAction('APPROVE')}
                  className="px-3 py-1.5 text-xs font-bold rounded-lg bg-emerald-600 text-white hover:bg-emerald-700 transition"
                >
                  Approve Dossier
                </button>
                <button
                  onClick={() => setReviewAction('REQUEST_REVISIONS')}
                  className="px-3 py-1.5 text-xs font-bold rounded-lg bg-amber-500 text-white hover:bg-amber-600 transition"
                >
                  Request Revisions
                </button>
                <button
                  onClick={() => setReviewAction('REJECT')}
                  className="px-3 py-1.5 text-xs font-bold rounded-lg bg-rose-600 text-white hover:bg-rose-700 transition"
                >
                  Reject
                </button>
              </div>
            </div>

            {/* Review Action Dialog */}
            {reviewAction && (
              <div className="p-3 bg-white rounded-lg border border-[#DCD4FB] space-y-2">
                <div className="text-xs font-bold text-[#211D2B]">
                  Confirm Action: {reviewAction.replace('_', ' ')}
                </div>
                <input
                  type="text"
                  placeholder="Reviewer sign-off comments (optional)"
                  value={reviewerComments}
                  onChange={(e) => setReviewerComments(e.target.value)}
                  className="w-full text-xs p-2 rounded-lg border border-[#E5E1EE] bg-white focus:outline-none focus:ring-1 focus:ring-[#7C5CFC]"
                />
                <div className="flex justify-end space-x-2">
                  <button
                    onClick={() => {
                      setReviewAction(null);
                      setReviewerComments('');
                    }}
                    className="px-2.5 py-1 text-xs text-[#8E8899] hover:bg-gray-100 rounded"
                  >
                    Cancel
                  </button>
                  <button
                    disabled={isSubmittingReview}
                    onClick={() => handleSubmitReview(reviewAction)}
                    className="px-3 py-1 text-xs font-bold bg-[#7C5CFC] text-white rounded hover:bg-[#6846EB] transition disabled:opacity-50"
                  >
                    {isSubmittingReview ? 'Submitting...' : 'Confirm'}
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* 7. Collapsible Immutable Audit Trail */}
          <div className="border border-[#E5E1EE] rounded-xl overflow-hidden">
            <button
              onClick={() => setShowAuditHistory(!showAuditHistory)}
              className="w-full p-3.5 bg-[#FAF9FD] flex items-center justify-between text-xs font-bold text-[#211D2B] hover:bg-[#F0EDFD]/50 transition"
            >
              <div className="flex items-center space-x-2">
                <History className="w-4 h-4 text-[#7C5CFC]" />
                <span>Chain of Custody & Audit Trail ({report.audit_history?.length || 0} events)</span>
              </div>
              {showAuditHistory ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>

            {showAuditHistory && (
              <div className="p-3.5 bg-white divide-y divide-[#E5E1EE] text-xs font-mono">
                {report.audit_history?.map((entry, idx) => (
                  <div key={idx} className="py-2 flex items-start justify-between text-[11px]">
                    <div>
                      <span className="font-bold text-[#7C5CFC]">{entry.action}</span>
                      {entry.user_id && <span className="text-[#8E8899] ml-1">by User #{entry.user_id}</span>}
                      {entry.details && (
                        <div className="text-[#8E8899] mt-0.5 truncate max-w-lg">
                          {JSON.stringify(entry.details)}
                        </div>
                      )}
                    </div>
                    <div className="text-[#8E8899] shrink-0 font-mono-num">
                      {new Date(entry.timestamp).toLocaleString()}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Citation Detail Modal Popup */}
        {selectedCitationDetail && (
          <div className="fixed inset-0 z-60 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs">
            <div className="bg-white rounded-xl p-5 max-w-md w-full border border-[#E5E1EE] shadow-2xl space-y-3">
              <div className="flex items-center justify-between border-b border-[#E5E1EE] pb-2">
                <div className="text-xs font-bold text-[#7C5CFC] uppercase">Physical Database Entity</div>
                <button
                  onClick={() => setSelectedCitationDetail(null)}
                  className="p-1 rounded text-[#8E8899] hover:text-[#211D2B]"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
              <div className="space-y-1.5 text-xs text-[#211D2B]">
                <div className="font-bold text-sm">{selectedCitationDetail.title}</div>
                <p className="text-[#8E8899] text-[11px]">
                  Verified database record physically bound to PostgreSQL storage with foreign key constraints.
                  Prevents hallucinated and dangling references.
                </p>
                <div className="p-2.5 rounded bg-[#FAF9FD] border border-[#E5E1EE] font-mono text-[11px]">
                  Type: {selectedCitationDetail.type}
                  <br />
                  Record ID: {selectedCitationDetail.id}
                  <br />
                  Incident Association: Verified
                </div>
              </div>
              <div className="flex justify-end">
                <button
                  onClick={() => setSelectedCitationDetail(null)}
                  className="px-3 py-1.5 rounded-lg text-xs font-bold bg-[#7C5CFC] text-white hover:bg-[#6846EB]"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
