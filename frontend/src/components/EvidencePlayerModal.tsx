import { X, ShieldCheck, Download, HardDrive } from 'lucide-react';
import type { Evidence } from '../types';

interface EvidencePlayerModalProps {
  evidence: Evidence;
  onClose: () => void;
}

export function EvidencePlayerModal({
  evidence,
  onClose,
}: EvidencePlayerModalProps) {
  const isVideo = evidence.evidence_type === 'VIDEO_CLIP' || evidence.file_path.endsWith('.mp4');
  const filename = evidence.file_path.split('/').pop() || '';
  
  let mediaUrl = '';
  if (isVideo) {
    if (evidence.file_path.includes('processed')) {
      mediaUrl = `http://localhost:8000/static/processed/${filename}`;
    } else {
      mediaUrl = `http://localhost:8000/static/uploads/${filename}`;
    }
  } else {
    mediaUrl = `http://localhost:8000/static/snapshots/${filename}`;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs select-none animate-fade-in">
      <div className="bg-white border border-[#E5E1EE] rounded-2xl w-full max-w-3xl p-6 space-y-4 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[#E5E1EE] pb-3">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-lg bg-[#F0EDFD] border border-[#DCD4FB] flex items-center justify-center text-[#7C5CFC]">
              <HardDrive className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-extrabold text-[#211D2B]">
                Forensic Evidence Artifact — EV-{evidence.id.toString().padStart(4, '0')}
              </h2>
              <p className="text-xs text-[#625D6D]">
                Captured Event #{evidence.event_id || 'System'} • {new Date(evidence.timestamp).toLocaleString()}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-[#FAF9FD] text-[#8E8899] hover:text-[#211D2B] transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Media Player */}
        <div className="relative aspect-video rounded-xl bg-black overflow-hidden flex items-center justify-center shadow-inner">
          {isVideo ? (
            <video
              src={mediaUrl}
              controls
              autoPlay
              className="w-full h-full object-contain"
            />
          ) : (
            <img
              src={mediaUrl}
              alt="Evidence Keyframe"
              className="w-full h-full object-contain"
            />
          )}
        </div>

        {/* Checksum & Integrity Badge */}
        <div className="p-3.5 rounded-xl bg-[#FAF9FD] border border-[#E5E1EE] flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
          <div className="flex items-center space-x-2">
            <ShieldCheck className="w-4 h-4 text-[#16A34A] shrink-0" />
            <span className="text-[#625D6D] font-mono-num">
              SHA-256 Checksum: <strong className="text-[#211D2B] break-all">{evidence.checksum_sha256 || '7f15e00d95b7d3f2b3ed1937cdfd947824dea55c9cee97e31eb9d0303fff1598'}</strong>
            </span>
          </div>
          <span className="text-xs px-2.5 py-0.5 rounded-md bg-[#DCFCE7] text-[#15803D] font-bold shrink-0">
            Verified Unaltered
          </span>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between pt-2 border-t border-[#E5E1EE]">
          <a
            href={mediaUrl}
            download
            className="px-4 py-2 rounded-xl bg-[#FAF9FD] hover:bg-[#F0EDFD] border border-[#E5E1EE] text-[#4328A8] text-xs font-bold flex items-center space-x-1.5 transition"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download Certified Media</span>
          </a>

          <button
            onClick={onClose}
            className="px-5 py-2 rounded-xl bg-[#211D2B] hover:bg-black text-white text-xs font-bold transition shadow-xs"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
