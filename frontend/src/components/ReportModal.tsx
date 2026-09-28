import { X, Printer, Shield, CheckCircle2 } from 'lucide-react';

interface ReportModalProps {
  report: {
    incident_id: number;
    generated_at: string;
    report_title: string;
    executive_summary: string;
    event_timeline: string[];
    ai_risk_assessment: string;
    recommended_containment: string[];
  };
  onClose: () => void;
}

export function ReportModal({ report, onClose }: ReportModalProps) {
  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs select-none animate-fade-in">
      <div className="bg-white border border-[#E5E1EE] rounded-2xl w-full max-w-3xl p-6 sm:p-8 space-y-6 shadow-2xl max-h-[90vh] overflow-y-auto">
        {/* Printable Header */}
        <div className="flex items-center justify-between border-b-2 border-[#7C5CFC] pb-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-[#F0EDFD] border border-[#DCD4FB] flex items-center justify-center text-[#7C5CFC]">
              <Shield className="w-6 h-6" />
            </div>
            <div>
              <div className="text-xs font-bold text-[#7C5CFC] uppercase tracking-wider">
                CONFIDENTIAL • BORDER INTELLIGENCE REPORT
              </div>
              <h2 className="text-xl font-extrabold text-[#211D2B]">{report.report_title}</h2>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-[#FAF9FD] text-[#8E8899] hover:text-[#211D2B] transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Metadata Strip */}
        <div className="grid grid-cols-3 gap-3 p-3.5 bg-[#FAF9FD] rounded-xl border border-[#E5E1EE] text-xs">
          <div>
            <span className="text-[#8E8899] block font-medium">Incident ID:</span>
            <span className="font-bold text-[#211D2B] font-mono-num">INC-{report.incident_id}</span>
          </div>
          <div>
            <span className="text-[#8E8899] block font-medium">Generated Timestamp:</span>
            <span className="font-semibold text-[#211D2B] font-mono-num">{new Date(report.generated_at).toLocaleString()}</span>
          </div>
          <div>
            <span className="text-[#8E8899] block font-medium">Classification:</span>
            <span className="font-bold text-[#D32F2F]">OFFICIAL / LAW ENFORCEMENT</span>
          </div>
        </div>

        {/* Executive Summary */}
        <div className="space-y-2">
          <h3 className="text-sm font-extrabold text-[#211D2B] uppercase tracking-wider">
            1. Executive Tactical Summary
          </h3>
          <p className="text-sm text-[#3E384D] leading-relaxed bg-[#FAF9FD] p-4 rounded-xl border border-[#E5E1EE]">
            {report.executive_summary}
          </p>
        </div>

        {/* AI Risk Assessment */}
        <div className="space-y-2">
          <h3 className="text-sm font-extrabold text-[#211D2B] uppercase tracking-wider">
            2. Google Gemini Cognitive Risk Assessment
          </h3>
          <p className="text-sm text-[#3E384D] leading-relaxed bg-[#F0EDFD] p-4 rounded-xl border border-[#DCD4FB]">
            {report.ai_risk_assessment}
          </p>
        </div>

        {/* Chronological Event Timeline */}
        <div className="space-y-2">
          <h3 className="text-sm font-extrabold text-[#211D2B] uppercase tracking-wider">
            3. Chronological Evidence Timeline
          </h3>
          <ul className="space-y-2 text-xs sm:text-sm text-[#3E384D]">
            {report.event_timeline.map((item, idx) => (
              <li key={idx} className="p-3 rounded-lg bg-[#FAF9FD] border border-[#E5E1EE] flex items-center space-x-2">
                <span className="w-2 h-2 rounded-full bg-[#7C5CFC]" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Recommendations */}
        <div className="space-y-2">
          <h3 className="text-sm font-extrabold text-[#211D2B] uppercase tracking-wider">
            4. Recommended Containment Strategies
          </h3>
          <ul className="space-y-2 text-xs sm:text-sm text-[#3E384D]">
            {report.recommended_containment.map((item, idx) => (
              <li key={idx} className="flex items-start space-x-2">
                <CheckCircle2 className="w-4 h-4 text-[#16A34A] shrink-0 mt-0.5" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between pt-4 border-t border-[#E5E1EE]">
          <button
            onClick={handlePrint}
            className="px-5 py-2.5 rounded-xl bg-[#7C5CFC] hover:bg-[#6A46F9] text-white text-xs font-bold flex items-center space-x-2 transition shadow-xs"
          >
            <Printer className="w-4 h-4" />
            <span>Print Official Case Dossier</span>
          </button>

          <button
            onClick={onClose}
            className="px-5 py-2.5 rounded-xl bg-[#211D2B] hover:bg-black text-white text-xs font-bold transition shadow-xs"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
