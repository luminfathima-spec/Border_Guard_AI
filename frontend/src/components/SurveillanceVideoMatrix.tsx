import { useState, useRef } from 'react';
import {
  Radio, Maximize2, Shield, Play, Pause, Volume2, VolumeX,
  Sparkles, CheckCircle2
} from 'lucide-react';
import type { Camera, Video } from '../types';

interface SurveillanceVideoMatrixProps {
  cameras: Camera[];
  videos?: Video[];
  activeProcessedVideo?: Video | null;
  onSelectCamera?: (camera: Camera) => void;
  onFullscreen?: (camera: Camera) => void;
}

export function SurveillanceVideoMatrix({
  cameras,
  videos = [],
  activeProcessedVideo,
  onSelectCamera,
  onFullscreen,
}: SurveillanceVideoMatrixProps) {
  const [playingStates, setPlayingStates] = useState<Record<number, boolean>>({});
  const [mutedStates, setMutedStates] = useState<Record<number, boolean>>({});
  const videoRefs = useRef<Record<number, HTMLVideoElement | null>>({});

  const togglePlay = (cameraId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    const vid = videoRefs.current[cameraId];
    if (vid) {
      if (vid.paused) {
        vid.play();
        setPlayingStates(prev => ({ ...prev, [cameraId]: true }));
      } else {
        vid.pause();
        setPlayingStates(prev => ({ ...prev, [cameraId]: false }));
      }
    }
  };

  const toggleMute = (cameraId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    const vid = videoRefs.current[cameraId];
    if (vid) {
      vid.muted = !vid.muted;
      setMutedStates(prev => ({ ...prev, [cameraId]: vid.muted }));
    }
  };

  return (
    <div className="w-full rounded-2xl bg-white border border-[#E5E1EE] p-6 sm:p-7 space-y-5 shadow-xs">
      {/* Section Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#E5E1EE] pb-4">
        <div className="flex items-center space-x-3.5">
          <div className="w-10 h-10 rounded-xl bg-[#F0EDFD] border border-[#DCD4FB] flex items-center justify-center text-[#7C5CFC] shadow-xs">
            <Radio className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-3">
              <h2 className="font-extrabold text-xl text-[#211D2B]">Surveillance Video Matrix</h2>
              <span className="text-xs px-3 py-0.5 rounded-full bg-[#DCFCE7] border border-[#86EFAC] text-[#15803D] font-bold">
                {cameras.length} Active Streams
              </span>
              {activeProcessedVideo && (
                <span className="text-xs px-3 py-0.5 rounded-full bg-[#F0EDFD] border border-[#DCD4FB] text-[#7C5CFC] font-extrabold flex items-center space-x-1">
                  <Sparkles className="w-3 h-3" />
                  <span>Real AI Feed Active</span>
                </span>
              )}
            </div>
            <p className="text-sm text-[#625D6D] font-medium mt-0.5">
              High-resolution surveillance feeds with real-time YOLOv8 bounding and intrusion telemetry
            </p>
          </div>
        </div>
      </div>

      {/* 2-Column Responsive Video Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {cameras.slice(0, 4).map((camera, idx) => {
          const isTargetOfActiveVideo = activeProcessedVideo && (activeProcessedVideo.camera_id === camera.id || idx === 0);
          const matchedVideo = isTargetOfActiveVideo ? activeProcessedVideo : (videos[idx % (videos.length || 1)] || activeProcessedVideo);
          
          let videoSrc = '';
          if (matchedVideo?.processed_path) {
            videoSrc = `http://localhost:8000/static/processed/${matchedVideo.processed_path.split('/').pop()}`;
          } else if (matchedVideo?.filename) {
            videoSrc = `http://localhost:8000/static/uploads/${matchedVideo.filename}`;
          } else {
            videoSrc = `http://localhost:8000/static/demo/demo_border_incursion.mp4`;
          }

          const isOnline = camera.status === 'ONLINE';
          const isPlaying = playingStates[camera.id] ?? true;
          const isMuted = mutedStates[camera.id] ?? true;

          return (
            <div
              key={camera.id}
              className="rounded-xl bg-[#FAF9FD] border border-[#E5E1EE] hover:border-[#7C5CFC] overflow-hidden flex flex-col justify-between transition-all duration-200 shadow-xs group"
            >
              {/* Card Header */}
              <div className="px-5 py-3.5 bg-white border-b border-[#E5E1EE] flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <span
                    className={`w-3 h-3 rounded-full shrink-0 ${
                      isOnline ? 'bg-[#16A34A] animate-pulse' : 'bg-[#D32F2F]'
                    }`}
                  />
                  <div>
                    <span className="font-bold text-base text-[#211D2B]">{camera.name}</span>
                    <span className="text-xs text-[#7C5CFC] ml-2 font-bold font-mono-num">{camera.camera_identifier}</span>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <span className="text-[11px] px-2.5 py-0.5 rounded-full bg-[#DCFCE7] border border-[#86EFAC] text-[#15803D] font-extrabold uppercase">
                    DEMO FEED
                  </span>
                  <span className="text-xs px-3 py-1 rounded-md bg-[#F0EDFD] border border-[#DCD4FB] text-[#4328A8] font-bold">
                    {camera.location}
                  </span>
                </div>
              </div>

              {/* Large Video Area (approx 280-340px high) */}
              <div
                onClick={() => onSelectCamera && onSelectCamera(camera)}
                className="relative h-72 sm:h-80 bg-[#0B0D10] cursor-pointer overflow-hidden flex items-center justify-center"
              >
                <video
                  ref={(el) => {
                    videoRefs.current[camera.id] = el;
                  }}
                  src={videoSrc}
                  autoPlay
                  loop
                  muted
                  playsInline
                  className="w-full h-full object-cover group-hover:scale-[1.005] transition-transform duration-300"
                />

                {/* Top Live OSD Telemetry Badge */}
                <div className="absolute top-3 left-3 px-3 py-1 rounded-md bg-black/80 border border-black/40 text-xs font-bold text-[#16A34A] flex items-center space-x-2 backdrop-blur-xs">
                  <span className="w-2 h-2 rounded-full bg-[#16A34A] animate-ping"></span>
                  <span>LIVE SURVEILLANCE</span>
                  <span className="text-white/40">|</span>
                  <span className="text-white font-mono-num">{camera.camera_identifier}</span>
                </div>

                {/* Top Right AI Detection Badge */}
                <div className="absolute top-3 right-3 px-3 py-1 rounded-md bg-black/80 border border-black/40 text-xs font-bold text-[#7C5CFC] flex items-center space-x-1.5 backdrop-blur-xs">
                  <Sparkles className="w-3.5 h-3.5 text-[#7C5CFC]" />
                  <span>AI DETECTION ACTIVE</span>
                </div>

                {/* Bottom Video Telemetry HUD */}
                <div className="absolute bottom-3 left-3 right-3 px-3.5 py-2 rounded-lg bg-black/85 backdrop-blur-xs text-xs text-[#F5F3ED] flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <span>Objects: <strong className="text-[#FCD34D] font-mono-num">{matchedVideo?.total_detections_count || 3}</strong></span>
                    <span>•</span>
                    <span>Persons: <strong className="text-[#60A5FA] font-mono-num">2</strong></span>
                    <span>•</span>
                    <span>Vehicles: <strong className="text-[#34D399] font-mono-num">1</strong></span>
                  </div>

                  {/* Player Controls */}
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={(e) => togglePlay(camera.id, e)}
                      className="p-1 rounded hover:bg-white/20 text-white transition"
                      title={isPlaying ? "Pause" : "Play"}
                    >
                      {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5 fill-white" />}
                    </button>
                    <button
                      onClick={(e) => toggleMute(camera.id, e)}
                      className="p-1 rounded hover:bg-white/20 text-white transition"
                      title={isMuted ? "Unmute" : "Mute"}
                    >
                      {isMuted ? <VolumeX className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />}
                    </button>
                    {onFullscreen && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onFullscreen(camera);
                        }}
                        className="p-1 rounded hover:bg-white/20 text-white transition"
                        title="Fullscreen"
                      >
                        <Maximize2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                </div>
              </div>

              {/* Card Footer */}
              <div className="px-5 py-3 bg-white border-t border-[#E5E1EE] flex flex-wrap items-center justify-between gap-2 text-xs sm:text-sm text-[#625D6D]">
                <div className="flex items-center space-x-3">
                  <span className="flex items-center space-x-1">
                    <Shield className="w-4 h-4 text-[#7C5CFC]" />
                    <span>Zones: <strong className="text-[#211D2B]">{camera.restricted_zones?.length || 1}</strong></span>
                  </span>
                  <span>•</span>
                  <span>Tripwires: <strong className="text-[#211D2B]">{camera.virtual_lines?.length || 1}</strong></span>
                </div>
                <span className="font-bold text-[#16A34A] flex items-center space-x-1.5">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>YOLOv8 + ByteTrack Linked</span>
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
