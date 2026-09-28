import { useState } from 'react';
import { Camera as CameraIcon, Crosshair, ZoomIn, ZoomOut, RotateCcw, Eye } from 'lucide-react';
import type { Camera, SecurityEvent, Incident } from '../types';

interface OperationsMapProps {
  cameras: Camera[];
  events?: SecurityEvent[];
  incidents?: Incident[];
  onSelectCamera?: (camera: Camera) => void;
  onSelectIncident?: (incident: Incident) => void;
}

export function OperationsMap({
  cameras,
  incidents = [],
  onSelectCamera,
  onSelectIncident,
}: OperationsMapProps) {
  const [zoomLevel, setZoomLevel] = useState(1);
  const [selectedCamera, setSelectedCamera] = useState<Camera | null>(null);
  const [activeSector, setActiveSector] = useState<string>('ALL');

  const cameraCoordinates: Record<string, { x: number; y: number; angle: number; cone: number }> = {
    'CAM-NP-01': { x: 220, y: 150, angle: 45, cone: 60 },
    'CAM-EB-02': { x: 490, y: 180, angle: 135, cone: 75 },
    'CAM-RB-03': { x: 330, y: 280, angle: 90, cone: 80 },
    'CAM-SV-04': { x: 640, y: 130, angle: 225, cone: 65 },
  };

  const filteredCameras = cameras.filter((cam) => {
    if (activeSector === 'ALL') return true;
    if (activeSector === 'NORTH' && cam.zone?.toLowerCase().includes('north')) return true;
    if (activeSector === 'EAST' && cam.zone?.toLowerCase().includes('east')) return true;
    if (activeSector === 'RIVER' && cam.zone?.toLowerCase().includes('river')) return true;
    return true;
  });

  return (
    <div className="w-full relative rounded-2xl bg-white border border-[#E5E1EE] overflow-hidden flex flex-col select-none shadow-xs">
      {/* Top Map Header */}
      <div className="min-h-14 px-6 bg-[#FAF9FD] border-b border-[#E5E1EE] flex flex-wrap items-center justify-between gap-3 text-sm py-2">
        <div className="flex items-center space-x-3.5">
          <div className="w-9 h-9 rounded-lg bg-[#F0EDFD] border border-[#DCD4FB] flex items-center justify-center text-[#7C5CFC]">
            <Crosshair className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2.5">
              <span className="font-extrabold text-lg text-[#211D2B]">
                Border Operations Geospatial Map
              </span>
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-[#F0EDFD] border border-[#DCD4FB] text-[#7C5CFC] font-bold">
                1:5,000 Topographic
              </span>
            </div>
            <p className="text-xs text-[#625D6D] font-medium">
              Sector 07 Northern Grid • Live Sensor Coverage & Breach Trajectories
            </p>
          </div>
        </div>

        {/* Sector Filters & Zoom */}
        <div className="flex items-center space-x-3">
          <div className="flex bg-white rounded-lg border border-[#E5E1EE] p-1 text-xs shadow-2xs">
            {[
              { id: 'ALL', label: 'All Sectors' },
              { id: 'NORTH', label: 'North' },
              { id: 'EAST', label: 'East Gate' },
              { id: 'RIVER', label: 'Riverbed' },
            ].map((sec) => (
              <button
                key={sec.id}
                onClick={() => setActiveSector(sec.id)}
                className={`px-3.5 py-1.5 rounded-md transition font-bold text-xs ${
                  activeSector === sec.id
                    ? 'bg-[#F0EDFD] text-[#4328A8] border border-[#DCD4FB]'
                    : 'text-[#625D6D] hover:text-[#211D2B]'
                }`}
              >
                {sec.label}
              </button>
            ))}
          </div>

          <div className="flex items-center space-x-1 pl-2 border-l border-[#E5E1EE]">
            <button
              onClick={() => setZoomLevel(Math.min(1.4, zoomLevel + 0.1))}
              className="p-2 rounded-lg hover:bg-[#F0EDFD] text-[#625D6D] hover:text-[#7C5CFC] transition"
              title="Zoom In"
            >
              <ZoomIn className="w-4 h-4" />
            </button>
            <button
              onClick={() => setZoomLevel(Math.max(0.8, zoomLevel - 0.1))}
              className="p-2 rounded-lg hover:bg-[#F0EDFD] text-[#625D6D] hover:text-[#7C5CFC] transition"
              title="Zoom Out"
            >
              <ZoomOut className="w-4 h-4" />
            </button>
            <button
              onClick={() => setZoomLevel(1)}
              className="p-2 rounded-lg hover:bg-[#F0EDFD] text-[#625D6D] hover:text-[#7C5CFC] transition"
              title="Reset Zoom"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Main Map Viewport */}
      <div className="relative w-full h-[380px] md:h-[450px] bg-[#FAF9FD] tactical-grid-light overflow-hidden flex items-center justify-center">
        <svg
          viewBox="0 0 800 400"
          className="w-full h-full transition-transform duration-300"
          style={{ transform: `scale(${zoomLevel})` }}
        >
          <defs>
            <pattern id="diagonalHatchLight" width="12" height="12" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
              <line x1="0" y1="0" x2="0" y2="12" stroke="rgba(124, 92, 252, 0.25)" strokeWidth="2.5" />
            </pattern>
          </defs>

          {/* Elevation Contours */}
          <path
            d="M 40 120 Q 200 80 400 110 T 760 90"
            fill="none"
            stroke="rgba(142, 136, 153, 0.35)"
            strokeWidth="1.5"
            strokeDasharray="4 4"
          />
          <path
            d="M 50 220 Q 250 180 480 230 T 750 210"
            fill="none"
            stroke="rgba(142, 136, 153, 0.35)"
            strokeWidth="1.5"
            strokeDasharray="4 4"
          />

          {/* International Demarcation Perimeter Line (Violet/Purple) */}
          <path
            d="M 20 60 Q 250 40 450 70 T 780 50"
            fill="none"
            stroke="#7C5CFC"
            strokeWidth="4"
            strokeDasharray="8 4"
          />
          <text x="340" y="42" fill="#7C5CFC" fontSize="14" fontWeight="bold" letterSpacing="1">
            DEMARCATION PERIMETER LINE
          </text>

          {/* Restricted Exclusion Buffer Strip */}
          <polygon
            points="50,90 750,80 720,170 80,190"
            fill="url(#diagonalHatchLight)"
            stroke="rgba(124, 92, 252, 0.7)"
            strokeWidth="2"
            strokeDasharray="6 4"
          />
          <text x="290" y="146" fill="#4328A8" fontSize="13" fontWeight="bold">
            RESTRICTED EXCLUSION BUFFER STRIP (150M)
          </text>

          {/* Riverine Sector Stream */}
          <path
            d="M 280 230 Q 340 290 420 360"
            fill="none"
            stroke="#81A4CD"
            strokeWidth="14"
            opacity="0.6"
          />
          <text x="330" y="325" fill="#3B597B" fontSize="12" fontWeight="bold">
            Sector 09 Riverbed Demarcation
          </text>

          {/* Virtual Tripwires */}
          <line
            x1="170"
            y1="120"
            x2="330"
            y2="135"
            stroke="#D97706"
            strokeWidth="3"
            strokeDasharray="5 4"
          />
          <text x="210" y="112" fill="#B45309" fontSize="12" fontWeight="bold">
            Tripwire 01-A
          </text>

          <line
            x1="450"
            y1="160"
            x2="590"
            y2="175"
            stroke="#D97706"
            strokeWidth="3"
            strokeDasharray="5 4"
          />
          <text x="485" y="152" fill="#B45309" fontSize="12" fontWeight="bold">
            Tripwire 02-B
          </text>

          {/* Camera Nodes */}
          {filteredCameras.map((cam, idx) => {
            const defaultCoord = Object.values(cameraCoordinates)[idx % 4] || { x: 150 + idx * 150, y: 150, angle: 90, cone: 60 };
            const coord = cameraCoordinates[cam.camera_identifier] || defaultCoord;
            const isOnline = cam.status === 'ONLINE';
            const isSelected = selectedCamera?.id === cam.id;

            return (
              <g key={cam.id} className="cursor-pointer" onClick={() => setSelectedCamera(cam)}>
                {/* FOV Cone */}
                <path
                  d={`M ${coord.x} ${coord.y} L ${coord.x - 55} ${coord.y + 70} A 80 80 0 0 0 ${coord.x + 55} ${coord.y + 70} Z`}
                  fill={isOnline ? 'rgba(22, 163, 74, 0.18)' : 'rgba(211, 47, 47, 0.18)'}
                  stroke={isOnline ? 'rgba(22, 163, 74, 0.7)' : 'rgba(211, 47, 47, 0.7)'}
                  strokeWidth="2"
                />

                {/* Pulsing Selection Ring */}
                {isSelected && (
                  <circle
                    cx={coord.x}
                    cy={coord.y}
                    r="22"
                    fill="none"
                    stroke="#7C5CFC"
                    strokeWidth="3"
                    className="animate-ping opacity-75"
                  />
                )}

                {/* Node Center Dot */}
                <circle
                  cx={coord.x}
                  cy={coord.y}
                  r="11"
                  fill={isSelected ? '#7C5CFC' : '#FFFFFF'}
                  stroke={isOnline ? '#16A34A' : '#D32F2F'}
                  strokeWidth="3.5"
                />

                {/* Camera Label */}
                <rect
                  x={coord.x - 46}
                  y={coord.y - 34}
                  width="92"
                  height="24"
                  rx="6"
                  fill="#FFFFFF"
                  stroke={isSelected ? '#7C5CFC' : '#DCD6E8'}
                  strokeWidth="2"
                />
                <text
                  x={coord.x}
                  y={coord.y - 18}
                  textAnchor="middle"
                  fill={isSelected ? '#7C5CFC' : '#211D2B'}
                  fontSize="13"
                  fontWeight="bold"
                >
                  {cam.camera_identifier}
                </text>
              </g>
            );
          })}

          {/* Breach Blips */}
          {incidents.slice(0, 2).map((inc, i) => (
            <g key={inc.id} className="cursor-pointer" onClick={() => onSelectIncident && onSelectIncident(inc)}>
              <circle
                cx={260 + i * 220}
                cy={140 + i * 40}
                r="18"
                fill="none"
                stroke="#D32F2F"
                strokeWidth="3"
                className="animate-ping"
              />
              <circle
                cx={260 + i * 220}
                cy={140 + i * 40}
                r="9"
                fill="#D32F2F"
              />
              <rect
                x={260 + i * 220 + 12}
                y={140 + i * 40 - 14}
                width="135"
                height="28"
                rx="6"
                fill="#FEE2E2"
                stroke="#FCA5A5"
                strokeWidth="2"
              />
              <text
                x={260 + i * 220 + 18}
                y={140 + i * 40 + 5}
                fill="#B91C1C"
                fontSize="13"
                fontWeight="bold"
              >
                BREACH: {inc.incident_number}
              </text>
            </g>
          ))}
        </svg>

        {/* Selected Camera Details Floating Popover */}
        {selectedCamera && (
          <div className="absolute bottom-4 left-4 bg-white/95 border border-[#DCD4FB] rounded-xl p-5 w-88 shadow-xl backdrop-blur text-sm space-y-3.5 z-10 animate-fade-in">
            <div className="flex items-center justify-between border-b border-[#E5E1EE] pb-2.5">
              <div className="flex items-center space-x-2.5">
                <CameraIcon className="w-5 h-5 text-[#7C5CFC]" />
                <span className="font-bold text-base text-[#211D2B]">{selectedCamera.name}</span>
              </div>
              <button
                onClick={() => setSelectedCamera(null)}
                className="text-[#8E8899] hover:text-[#211D2B] text-lg font-bold"
              >
                ×
              </button>
            </div>

            <div className="space-y-2 text-xs text-[#625D6D]">
              <div className="flex justify-between">
                <span className="text-[#8E8899] font-medium">Node ID:</span>
                <span className="text-[#7C5CFC] font-bold font-mono-num">{selectedCamera.camera_identifier}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#8E8899] font-medium">Sector:</span>
                <span className="text-[#211D2B] font-semibold">{selectedCamera.location}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#8E8899] font-medium">Status:</span>
                <span className={selectedCamera.status === 'ONLINE' ? 'text-[#16A34A] font-bold' : 'text-[#D97706] font-bold'}>
                  {selectedCamera.status}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#8E8899] font-medium">Restricted Zones:</span>
                <span className="text-[#211D2B] font-bold">{selectedCamera.restricted_zones?.length || 1} Configured</span>
              </div>
            </div>

            <div className="pt-2">
              <button
                onClick={() => onSelectCamera && onSelectCamera(selectedCamera)}
                className="w-full py-2.5 rounded-lg bg-[#7C5CFC] hover:bg-[#6A46F9] text-white text-xs font-bold flex items-center justify-center space-x-2 transition shadow-xs"
              >
                <Eye className="w-4 h-4" />
                <span>Open Live Surveillance Feed</span>
              </button>
            </div>
          </div>
        )}

        {/* Map Legend Overlay */}
        <div className="absolute bottom-4 right-4 bg-white/95 border border-[#E5E1EE] rounded-xl p-3 text-xs text-[#625D6D] space-y-2 hidden sm:block shadow-xs">
          <div className="flex items-center space-x-2.5">
            <span className="w-5 h-1.5 bg-[#7C5CFC] rounded-sm"></span>
            <span className="text-xs font-semibold text-[#211D2B]">Demarcation Perimeter</span>
          </div>
          <div className="flex items-center space-x-2.5">
            <span className="w-5 h-2.5 bg-[#7C5CFC]/25 border border-[#7C5CFC]/70 rounded-xs"></span>
            <span className="text-xs font-semibold text-[#211D2B]">Restricted Buffer Strip</span>
          </div>
          <div className="flex items-center space-x-2.5">
            <span className="w-5 h-1.5 border-t-2 border-[#D97706] border-dashed"></span>
            <span className="text-xs font-semibold text-[#211D2B]">Virtual Tripwire</span>
          </div>
        </div>
      </div>
    </div>
  );
}
