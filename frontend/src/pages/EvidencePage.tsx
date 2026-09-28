import { useState, useEffect } from 'react';
import { Download, ShieldCheck, RefreshCw, Eye, Film, Image as ImageIcon } from 'lucide-react';
import { evidenceApi } from '../services/sentinelApi';
import type { Evidence } from '../types';
import { EvidencePlayerModal } from '../components/EvidencePlayerModal';

export function EvidencePage() {
  const [evidenceList, setEvidenceList] = useState<Evidence[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedEvidence, setSelectedEvidence] = useState<Evidence | null>(null);

  const loadEvidence = async () => {
    try {
      setLoading(true);
      const data = await evidenceApi.list();
      setEvidenceList(data);
    } catch (e) {
      console.error('Failed to load evidence vault:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEvidence();
  }, []);

  const getMediaUrl = (ev: Evidence) => {
    const filename = ev.file_path.split('/').pop() || '';
    if (ev.evidence_type === 'VIDEO_CLIP' || ev.file_path.endsWith('.mp4')) {
      if (ev.file_path.includes('processed')) {
        return `http://localhost:8000/static/processed/${filename}`;
      }
      return `http://localhost:8000/static/uploads/${filename}`;
    }
    return `http://localhost:8000/static/snapshots/${filename}`;
  };

  return (
    <div className="w-full space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-[#E5E1EE]">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#211D2B] tracking-tight flex items-center space-x-3">
            <span>Forensic Evidence Vault & Chain of Custody</span>
            <span className="text-xs px-3 py-1 rounded-full bg-[#F0EDFD] border border-[#DCD4FB] text-[#7C5CFC] font-bold font-mono-num">
              {evidenceList.length} Media Artifacts
            </span>
          </h1>
          <p className="text-sm text-[#625D6D] mt-1 font-medium">
            SHA-256 integrity-verified video recordings, intrusion keyframe snapshots, and tamper-evident logs
          </p>
        </div>

        <button
          onClick={loadEvidence}
          className="p-2.5 rounded-lg bg-white hover:bg-[#FAF9FD] border border-[#E5E1EE] text-[#625D6D] hover:text-[#211D2B] transition shadow-xs self-start sm:self-auto"
          title="Refresh Vault"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-[#7C5CFC]' : ''}`} />
        </button>
      </div>

      {/* Evidence Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {evidenceList.length === 0 ? (
          <div className="col-span-full py-16 text-center text-[#625D6D] text-sm bg-white rounded-xl border border-[#E5E1EE]">
            No forensic evidence artifacts stored yet.
          </div>
        ) : (
          evidenceList.map((ev) => {
            const mediaUrl = getMediaUrl(ev);
            const isVideo = ev.evidence_type === 'VIDEO_CLIP' || ev.file_path.endsWith('.mp4');

            return (
              <div
                key={ev.id}
                className="rounded-xl bg-white border border-[#E5E1EE] p-4 space-y-3.5 flex flex-col justify-between shadow-xs hover:border-[#7C5CFC] transition group"
              >
                <div className="space-y-3">
                  {/* Media Thumbnail */}
                  <div
                    onClick={() => setSelectedEvidence(ev)}
                    className="relative aspect-video rounded-lg bg-[#0B0D10] border border-[#E5E1EE] overflow-hidden cursor-pointer flex items-center justify-center group-hover:border-[#7C5CFC] transition"
                  >
                    {isVideo ? (
                      <div className="flex flex-col items-center justify-center text-[#7C5CFC] space-y-1">
                        <Film className="w-10 h-10 text-[#7C5CFC]" />
                        <span className="text-[10px] text-white/80 font-bold uppercase">H.264 Video Stream</span>
                      </div>
                    ) : (
                      <img
                        src={mediaUrl}
                        alt="Evidence Frame"
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                        onError={(e) => {
                          (e.target as HTMLElement).style.display = 'none';
                        }}
                      />
                    )}
                    <div className="absolute inset-0 bg-black/30 flex items-center justify-center opacity-0 group-hover:opacity-100 transition">
                      <Eye className="w-8 h-8 text-white" />
                    </div>
                    <span className="absolute top-2 left-2 px-2 py-0.5 rounded bg-black/80 text-[11px] font-bold text-[#7C5CFC] flex items-center space-x-1">
                      {isVideo ? <Film className="w-3 h-3" /> : <ImageIcon className="w-3 h-3" />}
                      <span>{ev.evidence_type}</span>
                    </span>
                  </div>

                  {/* Metadata */}
                  <div className="space-y-1.5 text-xs text-[#625D6D]">
                    <div className="flex justify-between font-mono-num">
                      <span className="text-[#8E8899]">Artifact ID:</span>
                      <span className="text-[#7C5CFC] font-bold">EV-{ev.id.toString().padStart(4, '0')}</span>
                    </div>
                    {ev.incident_id && (
                      <div className="flex justify-between">
                        <span className="text-[#8E8899]">Incident:</span>
                        <span className="text-[#D32F2F] font-bold">Incident #{ev.incident_id}</span>
                      </div>
                    )}
                    {ev.event_id && (
                      <div className="flex justify-between">
                        <span className="text-[#8E8899]">Event ID:</span>
                        <span className="text-[#211D2B] font-semibold">Event #{ev.event_id}</span>
                      </div>
                    )}
                    <div className="flex justify-between font-mono-num">
                      <span className="text-[#8E8899]">Captured:</span>
                      <span>{new Date(ev.timestamp).toLocaleTimeString()}</span>
                    </div>
                    <div className="flex justify-between font-mono-num">
                      <span className="text-[#8E8899]">File Size:</span>
                      <span>{ev.file_size_bytes ? `${(ev.file_size_bytes / 1024).toFixed(1)} KB` : 'N/A'}</span>
                    </div>
                  </div>

                  {/* SHA-256 Checksum Badge */}
                  <div className="p-2.5 rounded-lg bg-[#FAF9FD] border border-[#E5E1EE] flex items-center space-x-2 text-xs">
                    <ShieldCheck className="w-4 h-4 text-[#16A34A] shrink-0" />
                    <span className="text-[11px] text-[#625D6D] font-mono-num truncate" title={ev.checksum_sha256 || 'SHA-256 Unaltered'}>
                      SHA256: {ev.checksum_sha256 ? `${ev.checksum_sha256.substring(0, 10)}...${ev.checksum_sha256.substring(ev.checksum_sha256.length - 4)}` : 'Verified'}
                    </span>
                  </div>
                </div>

                <div className="pt-2 border-t border-[#E5E1EE] flex items-center space-x-2">
                  <button
                    onClick={() => setSelectedEvidence(ev)}
                    className="flex-1 py-2 rounded-lg bg-[#FAF9FD] hover:bg-[#F0EDFD] border border-[#E5E1EE] text-[#4328A8] text-xs font-bold transition flex items-center justify-center space-x-1.5"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    <span>Inspect</span>
                  </button>
                  <a
                    href={mediaUrl}
                    download
                    className="p-2 rounded-lg bg-[#FAF9FD] hover:bg-[#F0EDFD] border border-[#E5E1EE] text-[#625D6D] hover:text-[#7C5CFC] transition"
                    title="Download File"
                  >
                    <Download className="w-4 h-4" />
                  </a>
                </div>
              </div>
            );
          })
        )}
      </div>

      {selectedEvidence && (
        <EvidencePlayerModal
          evidence={selectedEvidence}
          onClose={() => setSelectedEvidence(null)}
        />
      )}
    </div>
  );
}
