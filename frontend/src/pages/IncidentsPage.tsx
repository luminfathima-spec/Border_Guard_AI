import { useState, useEffect } from 'react';
import {
  Bot, CheckCircle2, Printer, RefreshCw, Send, Clock
} from 'lucide-react';
import { incidentApi, aiApi } from '../services/sentinelApi';
import type { Incident } from '../types';
import { SeverityBadge } from '../components/SeverityBadge';
import { ReportModal } from '../components/ReportModal';

export function IncidentsPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  const [analystNotes, setAnalystNotes] = useState<string>('');
  const [summarizing, setSummarizing] = useState(false);
  const [reportModalData, setReportModalData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const loadIncidents = async () => {
    try {
      setLoading(true);
      const data = await incidentApi.list();
      setIncidents(data);
      if (data.length > 0 && !selectedIncident) {
        setSelectedIncident(data[0]);
        setAnalystNotes(data[0].analyst_notes || '');
      }
    } catch (e) {
      console.error('Failed to load incidents:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadIncidents();
  }, []);

  const handleSelectIncident = (inc: Incident) => {
    setSelectedIncident(inc);
    setAnalystNotes(inc.analyst_notes || '');
  };

  const handleGenerateAISummary = async () => {
    if (!selectedIncident) return;
    try {
      setSummarizing(true);
      const res = await aiApi.summarizeIncident(selectedIncident.id);
      setSelectedIncident({
        ...selectedIncident,
        ai_summary: res.ai_summary,
        ai_recommendations: res.ai_recommendations,
      });
      loadIncidents();
    } catch (err) {
      console.error('Failed to generate AI summary:', err);
    } finally {
      setSummarizing(false);
    }
  };

  const handleSaveNotes = async () => {
    if (!selectedIncident) return;
    try {
      const updated = await incidentApi.update(selectedIncident.id, {
        analyst_notes: analystNotes,
      });
      setSelectedIncident(updated);
      loadIncidents();
    } catch (e) {
      console.error('Failed to save notes:', e);
    }
  };

  const handleGenerateFullReport = async () => {
    if (!selectedIncident) return;
    try {
      const res = await aiApi.generateReport(selectedIncident.id);
      setReportModalData(res);
    } catch (err) {
      console.error('Failed to generate report:', err);
    }
  };

  return (
    <div className="w-full space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-[#E5E1EE]">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#211D2B] tracking-tight flex items-center space-x-3">
            <span>Incident Dossiers & Forensics</span>
            <span className="text-xs px-3 py-1 rounded-full bg-[#F0EDFD] border border-[#DCD4FB] text-[#7C5CFC] font-bold">
              {incidents.length} Case Files
            </span>
          </h1>
          <p className="text-sm text-[#625D6D] mt-1 font-medium">
            Full forensic evidence chain, AI threat reasoning, and containment action logs
          </p>
        </div>

        <button
          onClick={loadIncidents}
          className="p-2.5 rounded-lg bg-white hover:bg-[#FAF9FD] border border-[#E5E1EE] text-[#625D6D] hover:text-[#211D2B] transition shadow-xs self-start sm:self-auto"
          title="Refresh Incidents"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-[#7C5CFC]' : ''}`} />
        </button>
      </div>

      {/* Main 2-Column Investigation Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 w-full">
        {/* Left 4 Cols: Cases Register */}
        <div className="lg:col-span-4 space-y-4">
          <div className="rounded-xl bg-white border border-[#E5E1EE] p-4 space-y-3 shadow-xs">
            <div className="text-xs font-bold text-[#8E8899] uppercase tracking-wider border-b border-[#E5E1EE] pb-2.5">
              Case Files Register
            </div>

            <div className="space-y-2.5 max-h-[640px] overflow-y-auto pr-1">
              {incidents.map((inc) => {
                const isSelected = selectedIncident?.id === inc.id;
                return (
                  <div
                    key={inc.id}
                    onClick={() => handleSelectIncident(inc)}
                    className={`p-4 rounded-xl border cursor-pointer transition space-y-2.5 ${
                      isSelected
                        ? 'bg-[#F0EDFD] border-[#7C5CFC] text-[#211D2B] shadow-xs'
                        : 'bg-[#FAF9FD] border-[#E5E1EE] text-[#625D6D] hover:border-[#C4BAE0]'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[#7C5CFC] font-extrabold text-xs font-mono-num">{inc.incident_number}</span>
                      <SeverityBadge severity={inc.severity} size="sm" />
                    </div>
                    <div className="text-[#211D2B] text-sm font-bold line-clamp-1">{inc.title}</div>
                    <div className="flex items-center justify-between text-xs text-[#8E8899] pt-1 border-t border-[#E5E1EE]">
                      <span className="flex items-center space-x-1.5 font-medium text-[#625D6D]">
                        <Clock className="w-3.5 h-3.5" />
                        <span>{new Date(inc.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                      </span>
                      <span className="text-[#4328A8] font-bold uppercase tracking-wider text-[11px]">{inc.status}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right 8 Cols: Active Dossier & Cognitive AI Reasoning */}
        <div className="lg:col-span-8 space-y-5">
          {selectedIncident ? (
            <div className="rounded-xl bg-white border border-[#E5E1EE] p-6 space-y-5 shadow-xs">
              {/* Dossier Header */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#E5E1EE] pb-4">
                <div className="space-y-1">
                  <div className="flex items-center space-x-3">
                    <span className="text-base font-extrabold text-[#7C5CFC] font-mono-num">{selectedIncident.incident_number}</span>
                    <SeverityBadge severity={selectedIncident.severity} size="sm" />
                    <span className="text-xs text-[#8E8899] font-bold">STATUS: {selectedIncident.status}</span>
                  </div>
                  <h2 className="text-xl font-extrabold text-[#211D2B]">{selectedIncident.title}</h2>
                </div>

                <button
                  onClick={handleGenerateFullReport}
                  className="px-4 py-2.5 rounded-lg bg-[#FAF9FD] hover:bg-[#F0EDFD] border border-[#E5E1EE] text-[#4328A8] text-sm font-bold flex items-center space-x-2 transition shadow-xs"
                >
                  <Printer className="w-4 h-4 text-[#7C5CFC]" />
                  <span>Export Report Dossier</span>
                </button>
              </div>

              {/* Physical Telemetry Event Log */}
              <div className="p-4 rounded-xl bg-[#FAF9FD] border border-[#E5E1EE] space-y-1.5">
                <div className="text-xs text-[#8E8899] font-bold uppercase tracking-wider">PHYSICAL TELEMETRY EVENT LOG:</div>
                <div className="text-[#211D2B] text-sm leading-relaxed">{selectedIncident.description}</div>
              </div>

              {/* Google Gemini AI Reasoning Box */}
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
                    {summarizing ? 'Reasoning...' : 'Regenerate AI Analysis'}
                  </button>
                </div>

                <div className="text-[#211D2B] text-sm leading-relaxed bg-white p-4 rounded-lg border border-[#DCD4FB]">
                  {selectedIncident.ai_summary || 'No AI threat reasoning generated yet. Click analyze above to run cognitive inference.'}
                </div>

                {selectedIncident.ai_recommendations && selectedIncident.ai_recommendations.length > 0 && (
                  <div className="space-y-2 pt-1">
                    <span className="text-xs text-[#4328A8] font-bold uppercase tracking-wider">
                      Recommended Tactical Containment Actions:
                    </span>
                    <ul className="space-y-1.5 text-xs sm:text-sm text-[#3E384D]">
                      {selectedIncident.ai_recommendations.map((rec, idx) => (
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
                <div className="text-xs text-[#8E8899] font-bold uppercase tracking-wider">
                  Field Analyst Investigation Notes:
                </div>
                <textarea
                  rows={4}
                  value={analystNotes}
                  onChange={(e) => setAnalystNotes(e.target.value)}
                  placeholder="Record tactical intercepts, Quick Reaction Team response timestamps, radar confirmations..."
                  className="w-full p-3.5 bg-white border border-[#E5E1EE] rounded-lg text-[#211D2B] text-sm focus:outline-none focus:border-[#7C5CFC] leading-relaxed font-sans shadow-2xs"
                />
                <div className="flex justify-end">
                  <button
                    onClick={handleSaveNotes}
                    className="px-4 py-2.5 rounded-lg bg-[#FAF9FD] hover:bg-[#F0EDFD] border border-[#E5E1EE] text-[#4328A8] text-xs font-bold flex items-center space-x-2 transition"
                  >
                    <Send className="w-3.5 h-3.5 text-[#7C5CFC]" />
                    <span>Save Field Notes</span>
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="p-16 text-center text-[#625D6D] text-sm bg-white rounded-xl border border-[#E5E1EE] shadow-xs">
              Select a case file from the register to inspect dossier.
            </div>
          )}
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
