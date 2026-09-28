import { useState } from 'react';
import { Maximize2, Radio, Signal } from 'lucide-react';
import type { Camera, Video } from '../types';

interface CameraTileProps {
  camera: Camera;
  video?: Video;
  onSelect?: (camera: Camera) => void;
  onFullscreen?: (camera: Camera) => void;
  compact?: boolean;
}

export function CameraTile({ camera, video, onSelect, onFullscreen, compact = false }: CameraTileProps) {
  const [hovered, setHovered] = useState(false);
  const isOnline = camera.status === 'ONLINE';

  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      className={`rounded-lg bg-[#111317] border transition-all duration-200 overflow-hidden flex flex-col justify-between group shadow-sm ${
        hovered ? 'border-[#3E4552]' : 'border-[#24272D]'
      }`}
    >
      {/* Tile Header */}
      <div className="px-3.5 py-2 bg-[#15181C] border-b border-[#24272D] flex items-center justify-between text-xs">
        <div className="flex items-center space-x-2 min-w-0">
          <span
            className={`w-2.5 h-2.5 rounded-full shrink-0 ${
              isOnline ? 'bg-[#5BAF75]' : 'bg-[#C75C5C]'
            }`}
          />
          <span className="font-bold text-sm text-[#F2F0EA] truncate">{camera.name}</span>
        </div>
        <span className="text-xs px-2 py-0.5 rounded bg-[#1B1E22] border border-[#2E333C] text-[#D6A84A] font-semibold shrink-0">
          {camera.camera_identifier}
        </span>
      </div>

      {/* Video Viewport Area */}
      <div
        onClick={() => onSelect && onSelect(camera)}
        className={`relative bg-[#0E1013] cursor-pointer overflow-hidden flex items-center justify-center ${
          compact ? 'aspect-video' : 'h-44 sm:h-52'
        }`}
      >
        {video ? (
          <video
            src={`http://localhost:8000/static/uploads/${video.filename}`}
            autoPlay
            loop
            muted
            playsInline
            className="w-full h-full object-cover group-hover:scale-[1.02] transition-transform duration-300"
          />
        ) : (
          <div className="w-full h-full p-4 flex flex-col items-center justify-center bg-[#0E1013] text-[#8E8B83] text-center space-y-2">
            <div className="w-10 h-10 rounded-full bg-[#171A1E] border border-[#262A31] flex items-center justify-center text-[#D6A84A]">
              <Signal className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xs font-bold text-[#D2CEBE]">STANDBY CHANNEL SIGNAL</div>
              <div className="text-[11px] text-[#8E8B83]">{camera.location}</div>
            </div>
          </div>
        )}

        {/* Live OSD Watermark */}
        <div className="absolute top-2 left-2 px-2 py-0.5 rounded bg-black/80 border border-black/40 text-xs font-semibold text-[#5BAF75] flex items-center space-x-1.5 backdrop-blur-sm">
          <span className="w-2 h-2 rounded-full bg-[#5BAF75] animate-ping"></span>
          <span>LIVE</span>
        </div>

        {/* Target Bounding Box Simulation */}
        {hovered && isOnline && (
          <div className="absolute inset-0 border border-[#D6A84A]/30 pointer-events-none flex items-center justify-center">
            <div className="w-24 h-36 border-2 border-[#D6A84A] rounded bg-[#D6A84A]/10 relative">
              <span className="absolute -top-5 left-0 px-1.5 py-0.5 bg-[#1B1E22] border border-[#3E4552] text-[#E5B85C] text-xs font-bold rounded">
                Person 96%
              </span>
            </div>
          </div>
        )}

        {/* Hover Action Overlay */}
        <div className="absolute bottom-2 right-2 opacity-0 group-hover:opacity-100 transition flex items-center space-x-1.5">
          {onFullscreen && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onFullscreen(camera);
              }}
              className="p-1.5 rounded bg-[#1B1E22]/90 hover:bg-[#252930] border border-[#333842] text-[#F2F0EA] shadow-md transition"
              title="Fullscreen View"
            >
              <Maximize2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Tile Footer Meta */}
      <div className="px-3.5 py-2 bg-[#14171B] border-t border-[#24272D] flex items-center justify-between text-xs text-[#A9A69D]">
        <span className="truncate max-w-[140px] font-medium">{camera.location}</span>
        <span className="text-[#8E8B83] font-medium">{camera.restricted_zones?.length || 0} Restricted Zones</span>
      </div>
    </div>
  );
}

interface CameraWallProps {
  cameras: Camera[];
  videos?: Video[];
  onSelectCamera?: (camera: Camera) => void;
}

export function CameraWall({ cameras, videos = [], onSelectCamera }: CameraWallProps) {
  return (
    <div className="space-y-2.5">
      <div className="flex items-center justify-between text-sm text-[#F2F0EA]">
        <div className="flex items-center space-x-2">
          <Radio className="w-4 h-4 text-[#D6A84A]" />
          <span className="font-semibold text-sm tracking-wide">Surveillance Video Matrix</span>
        </div>
        <span className="text-xs text-[#A9A69D] font-medium">{cameras.length} Active Camera Feeds</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
        {cameras.slice(0, 4).map((cam, idx) => (
          <CameraTile
            key={cam.id}
            camera={cam}
            video={videos[idx % (videos.length || 1)]}
            onSelect={onSelectCamera}
            compact={true}
          />
        ))}
      </div>
    </div>
  );
}
