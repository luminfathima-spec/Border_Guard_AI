import { useState } from 'react';
import { Radio, Upload } from 'lucide-react';
import type { Camera, Video } from '../types';

interface LiveSurveillanceHeroProps {
  cameras: Camera[];
  videos?: Video[];
  activeProcessedVideo?: Video | null;
  onIngestClick?: () => void;
  onSelectCamera?: (camera: Camera) => void;
}

export function LiveSurveillanceHero({
  cameras,
  videos = [],
  activeProcessedVideo,
  onIngestClick,
  onSelectCamera,
}: LiveSurveillanceHeroProps) {
  const [selectedChannelId, setSelectedChannelId] = useState<number>(cameras[0]?.id || 1);

  const activeCamera = cameras.find((c) => c.id === selectedChannelId) || cameras[0];

  const matchedVideo = activeProcessedVideo && (activeProcessedVideo.camera_id === activeCamera?.id || !videos.length)
    ? activeProcessedVideo
    : (videos.find((v) => v.camera_id === activeCamera?.id) || activeProcessedVideo || videos[0]);

  let videoSrc = '';
  if (matchedVideo?.processed_path) {
    videoSrc = `http://localhost:8000/static/processed/${matchedVideo.processed_path.split('/').pop()}`;
  } else if (matchedVideo?.filename) {
    videoSrc = `http://localhost:8000/static/uploads/${matchedVideo.filename}`;
  } else {
    videoSrc = `http://localhost:8000/static/demo/demo_border_incursion.mp4`;
  }

  return (
    <div className="rounded-xl bg-white border border-[#E5E1EE] p-5 space-y-4 shadow-xs">
      {/* Feed Header Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-[#E5E1EE]">
        <div className="flex items-center space-x-2.5">
          <Radio className="w-4 h-4 text-[#16A34A] animate-pulse" />
          <span className="font-extrabold text-base text-[#211D2B]">
            Primary Live Surveillance Feed — {activeCamera?.name || 'Northern Perimeter'}
          </span>
          <span className="text-xs px-2.5 py-0.5 rounded-full bg-[#DCFCE7] border border-[#86EFAC] text-[#15803D] font-bold">
            {activeCamera?.camera_identifier || 'CAM-01'}
          </span>
          <span className="text-[11px] px-2 py-0.5 rounded-full bg-[#F0EDFD] border border-[#DCD4FB] text-[#7C5CFC] font-extrabold uppercase">
            DEMO FEED
          </span>
        </div>

        <div className="flex items-center space-x-2">
          {onIngestClick && (
            <button
              onClick={onIngestClick}
              className="px-4 py-2 rounded-lg bg-[#7C5CFC] hover:bg-[#6A46F9] text-white font-bold text-xs flex items-center space-x-1.5 transition shadow-xs"
            >
              <Upload className="w-3.5 h-3.5" />
              <span>Ingest Surveillance Video</span>
            </button>
          )}
        </div>
      </div>

      {/* Large Primary Video Viewport */}
      <div className="relative aspect-video rounded-xl bg-[#0B0D10] overflow-hidden flex items-center justify-center group shadow-inner">
        <video
          key={videoSrc}
          src={videoSrc}
          controls
          autoPlay
          loop
          muted
          playsInline
          className="w-full h-full object-cover"
        />

        {/* Video Overlays (OSD) */}
        <div className="absolute top-3 left-3 px-3 py-1 rounded-md bg-black/80 border border-black/40 text-xs text-[#16A34A] font-bold flex items-center space-x-2 backdrop-blur-xs">
          <span className="w-2 h-2 rounded-full bg-[#16A34A] animate-ping"></span>
          <span>{activeCamera?.camera_identifier || 'CAM-01'}</span>
          <span className="text-white/40">|</span>
          <span className="text-white">{activeCamera?.location || 'Sector 07 North'}</span>
          <span className="text-white/40">|</span>
          <span className="text-[#7C5CFC]">AI DETECT ACTIVE</span>
        </div>

        {/* Bottom Stream Telemetry Bar Overlay */}
        <div className="absolute bottom-3 left-3 right-3 bg-black/75 backdrop-blur-xs border border-white/10 rounded-lg p-2.5 flex items-center justify-between text-xs text-white">
          <div className="flex items-center space-x-3">
            <span>Encoder: <strong className="text-white font-mono-num">H.264 / 720p</strong></span>
            <span>•</span>
            <span>FPS: <strong className="text-[#16A34A] font-mono-num">25.0</strong></span>
            <span>•</span>
            <span>Inference Latency: <strong className="text-[#D97706] font-mono-num">18 ms</strong></span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-[#FCD34D] font-bold">
              Objects: {matchedVideo?.total_detections_count || 3} • Persons: 2 • Vehicles: 1
            </span>
          </div>
        </div>
      </div>

      {/* Channel Switcher Strip */}
      <div className="space-y-1.5 pt-1">
        <div className="text-xs font-bold text-[#8E8899] uppercase tracking-wider">
          Quick Camera Channel Switcher ({cameras.length} Active Nodes)
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
          {cameras.map((cam) => {
            const isSelected = activeCamera?.id === cam.id;
            const camOnline = cam.status === 'ONLINE';
            return (
              <div
                key={cam.id}
                onClick={() => {
                  setSelectedChannelId(cam.id);
                  if (onSelectCamera) onSelectCamera(cam);
                }}
                className={`p-3 rounded-xl border cursor-pointer transition space-y-1 ${
                  isSelected
                    ? 'bg-[#F0EDFD] border-[#7C5CFC] text-[#211D2B] shadow-xs'
                    : 'bg-[#FAF9FD] border-[#E5E1EE] text-[#625D6D] hover:border-[#C4BAE0]'
                }`}
              >
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center space-x-1.5">
                    <span
                      className={`w-2.5 h-2.5 rounded-full ${
                        camOnline ? 'bg-[#16A34A]' : 'bg-[#D32F2F]'
                      }`}
                    />
                    <span className="font-bold text-[#211D2B] truncate max-w-[90px]">{cam.name}</span>
                  </div>
                  <span className="text-[#7C5CFC] font-bold text-[11px] font-mono-num">{cam.camera_identifier}</span>
                </div>
                <div className="text-[11px] text-[#8E8899] truncate">{cam.location}</div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
