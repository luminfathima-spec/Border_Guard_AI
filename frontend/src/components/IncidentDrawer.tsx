import { useState } from 'react';
import { Bot, CheckCircle2, Printer, X, Send, Clock, ShieldAlert, GitBranch, Layers } from 'lucide-react';
import { incidentApi, aiApi, reportApi } from '../services/sentinelApi';
import type { Incident } from '../types';
import { SeverityBadge } from './SeverityBadge';
import { ReportModal } from './ReportModal';
import { EvidenceTimeline } from './EvidenceTimeline';

interface IncidentDrawerProps {
  incident: Incident | null;
  onClose: () => void;
  onUpdated?: () => void;
}

export function IncidentDrawer({
  incident,
  onClose,
  onUpdated,
}: IncidentDrawerProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'timeline'>('overview');
  const [analystNotes, setAnalystNotes] = useState<string>(incident?.analyst_notes || '');
  const [summarizing, setSummarizing] = useState(false);
  const [currentIncident, setCurrentIncident] = useState<Incident | null>(incident);
  const [reportModalData, setReportModalData] = useState<any>(null);

  if (!incident) return null;

  const handleGenerateAISummary = async () => {
    try {
      setSummarizing(true);
      const res = await aiApi.summarizeIncident(incident.id);
      const updated = {
        ...incident,
        ai_summary: res.ai_summary,
        ai_recommendations: res.ai_recommendations,
      };
      setCurrentIncident(updated);
      if (onUpdated) onUpdated();
    } catch (err) {
      console.error('Failed to generate AI summary:', err);
    } finally {
      setSummarizing(false);
    }
  };

  const handleSaveNotes = async () => {
    try {
      const updated = await incidentApi.update(incident.id, {
        analyst_notes: analystNotes,
      });
      setCurrentIncident(updated);
      if (onUpdated) onUpdated();
    } catch (e) {
      console.error('Failed to save notes:', e);
    }
  };

  const handleGenerateFullReport = async () => {
    try {
      const res = await reportApi.generate(incident.id);
      setReportModalData(res);
    } catch (err) {
      console.error('Failed to generate report:', err);
    }
  };

  const activeInc = currentIncident || incident;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/40 backdrop-blur-xs select-none animate-fade-in">
      <div className="w-full max-w-2xl bg-white border-l border-[#E5E1EE] h-full overflow-y-auto p-6 space-y-6 shadow-2xl flex flex-col justify-between">
        <div className="space-y-6">
          {/* Drawer Header */}
          <div className="flex items-center justify-between border-b border-[#E5E1EE] pb-4">
            <div className="flex items-center space-x-3">
              <div className="w-9 h-9 rounded-lg bg-[#FEE2E2] border border-[#FCA5A5] flex items-center justify-center text-[#D32F2F]">
                <ShieldAlert className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center space-x-2.5">
                  <span className="font-extrabold text-lg text-[#211D2B]">{activeInc.incident_number}</span>
                  <SeverityBadge severity={activeInc.severity} size="sm" />
                </div>
                <div className="text-xs text-[#8E8899] font-semibold uppercase tracking-wider">
                  STATUS: {activeInc.status}
                </div>
              </div>
            </div>

            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-[#FAF9FD] text-[#8E8899] hover:text-[#211D2B] transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Incident Title & Telemetry */}
          <div className="space-y-3">
            <h2 className="text-xl font-extrabold text-[#211D2B]">{activeInc.title}</h2>
            <div className="p-4 rounded-xl bg-[#FAF9FD] border border-[#E5E1EE] space-y-2 text-sm text-[#625D6D]">
              <div className="text-xs font-bold text-[#8E8899] uppercase tracking-wider">PHYSICAL TELEMETRY EVENT LOG:</div>
              <div className="text-[#211D2B] text-sm leading-relaxed">{activeInc.description}</div>
              <div className="flex items-center space-x-2 text-xs text-[#8E8899] pt-1">
                <Clock className="w-4 h-4" />
                <span>Recorded: {new Date(activeInc.created_at).toLocaleString()}</span>
              </div>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex border-b border-[#E5E1EE] space-x-6 text-xs font-bold">
            <button
              onClick={() => setActiveTab('overview')}
              className={`pb-2.5 flex items-center space-x-1.5 transition border-b-2 -mb-px ${
                activeTab === 'overview'
                  ? 'border-[#7C5CFC] text-[#7C5CFC]'
                  : 'border-transparent text-[#8E8899] hover:text-[#211D2B]'
              }`}
            >
              <Layers className="w-4 h-4" />
              <span>Overview & AI Analysis</span>
            </button>
            <button
              onClick={() => setActiveTab('timeline')}
              className={`pb-2.5 flex items-center space-x-1.5 transition border-b-2 -mb-px ${
                activeTab === 'timeline'
                  ? 'border-[#7C5CFC] text-[#7C5CFC]'
                  : 'border-transparent text-[#8E8899] hover:text-[#211D2B]'
              }`}
            >
              <GitBranch className="w-4 h-4" />
              <span>Evidence Provenance Timeline</span>
            </button>
          </div>

          {activeTab === 'timeline' ? (
            <EvidenceTimeline incidentId={activeInc.id} incidentNumber={activeInc.incident_number} />
          ) : (
            <>
              {/* Google Gemini AI Threat Reasoning Box */}
              <div className="p-5 rounded-xl bg-[#F0EDFD] border border-[#DCD4FB] space-y-3.5 shadow-xs">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2 text-[#4328A8] font-bold text-sm">
                    <Bot className="w-5 h-5 text-[#7C5CFC]" />
                    <span>Google Gemini Cognitive Threat Assessment</span>
                  </div>
                  <button
                    onClick={handleGenerateAISummary}
                    disabled={summarizing}
                    className="px-3.5 py-1.5 rounded-lg bg-[#7C5CFC] hover:bg-[#6A46F9] text-white font-bold text-xs transition disabled:opacity-50 shadow-xs"
                  >
                    {summarizing ? 'Reasoning...' : 'Regenerate Analysis'}
                  </button>
                </div>

                <div className="text-[#211D2B] text-sm leading-relaxed bg-white p-4 rounded-lg border border-[#DCD4FB]">
                  {activeInc.ai_summary || 'No AI threat analysis generated yet. Click above to run cognitive inference.'}
                </div>

                {activeInc.ai_recommendations && activeInc.ai_recommendations.length > 0 && (
                  <div className="space-y-2 pt-1">
                    <span className="text-xs text-[#4328A8] font-bold uppercase tracking-wider">
                      Recommended Tactical Containment Actions:
                    </span>
                    <ul className="space-y-2 text-xs sm:text-sm text-[#3E384D]">
                      {activeInc.ai_recommendations.map((rec, idx) => (
                        <li key={idx} className="flex items-start space-x-2">
                          <CheckCircle2 className="w-4 h-4 text-[#7C5CFC] shrink-0 mt-0.5" />
                          <span>{rec}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {/* Field Analyst Notes */}
              <div className="space-y-2">
                <div className="text-xs font-bold text-[#8E8899] uppercase tracking-wider">
                  Field Analyst Investigation Notes:
                </div>
                <textarea
                  rows={3}
                  value={analystNotes}
                  onChange={(e) => setAnalystNotes(e.target.value)}
                  placeholder="Record tactical intercepts, Quick Reaction Team response, radar confirmations..."
                  className="w-full p-3 bg-white border border-[#E5E1EE] rounded-lg text-[#211D2B] text-sm focus:outline-none focus:border-[#7C5CFC] leading-relaxed shadow-2xs font-sans"
                />
                <div className="flex justify-end">
                  <button
                    onClick={handleSaveNotes}
                    className="px-4 py-2 rounded-lg bg-[#FAF9FD] hover:bg-[#F0EDFD] border border-[#E5E1EE] text-[#4328A8] text-xs font-bold flex items-center space-x-2 transition"
                  >
                    <Send className="w-3.5 h-3.5 text-[#7C5CFC]" />
                    <span>Save Field Notes</span>
                  </button>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Footer Actions */}
        <div className="pt-4 border-t border-[#E5E1EE] flex items-center justify-between">
          <button
            onClick={handleGenerateFullReport}
            className="px-4 py-2.5 rounded-lg bg-[#FAF9FD] hover:bg-[#F0EDFD] border border-[#E5E1EE] text-[#4328A8] text-sm font-bold flex items-center space-x-2 transition"
          >
            <Printer className="w-4 h-4 text-[#7C5CFC]" />
            <span>Generate PDF Case Dossier</span>
          </button>
          <button
            onClick={onClose}
            className="px-5 py-2.5 rounded-lg bg-[#211D2B] hover:bg-black text-white text-sm font-bold transition shadow-xs"
          >
            Close Drawer
          </button>
        </div>
      </div>

      {reportModalData && (
        <ReportModal
          report={reportModalData}
          onClose={() => setReportModalData(null)}
        />
      )}
    </div>
  );
}
