import { useState } from 'react';
import { X, Shield, Plus, Check, RotateCcw } from 'lucide-react';
import type { Camera, RestrictedZone, VirtualLine, ZoneCoordinate } from '../types';
import { cameraApi } from '../services/sentinelApi';

interface ZoneCanvasModalProps {
  camera: Camera;
  onClose: () => void;
  onSaved: () => void;
}

export function ZoneCanvasModal({
  camera,
  onClose,
  onSaved,
}: ZoneCanvasModalProps) {
  const [zones, setZones] = useState<RestrictedZone[]>(camera.restricted_zones || []);
  const [lines, setLines] = useState<VirtualLine[]>(camera.virtual_lines || []);
  const [activeMode, setActiveMode] = useState<'NONE' | 'DRAW_ZONE' | 'DRAW_LINE'>('NONE');
  const [currentPoints, setCurrentPoints] = useState<ZoneCoordinate[]>([]);
  const [saving, setSaving] = useState(false);

  const handleCanvasClick = (e: React.MouseEvent<SVGSVGElement>) => {
    if (activeMode === 'NONE') return;

    const rect = e.currentTarget.getBoundingClientRect();
    const x = Math.round(((e.clientX - rect.left) / rect.width) * 1000) / 10;
    const y = Math.round(((e.clientY - rect.top) / rect.height) * 1000) / 10;
    const point: ZoneCoordinate = { x, y };

    if (activeMode === 'DRAW_ZONE') {
      setCurrentPoints([...currentPoints, point]);
    } else if (activeMode === 'DRAW_LINE') {
      if (currentPoints.length === 0) {
        setCurrentPoints([point]);
      } else {
        const newLine: VirtualLine = {
          id: Date.now().toString(),
          name: `Virtual Tripwire ${lines.length + 1}`,
          p1: currentPoints[0],
          p2: point,
          direction: 'BOTH',
          alert_severity: 'HIGH',
        };
        setLines([...lines, newLine]);
        setCurrentPoints([]);
        setActiveMode('NONE');
      }
    }
  };

  const handleFinishPolygon = () => {
    if (currentPoints.length < 3) return;
    const newZone: RestrictedZone = {
      id: Date.now().toString(),
      name: `Restricted Zone ${zones.length + 1}`,
      polygon: currentPoints,
      alert_severity: 'HIGH',
    };
    setZones([...zones, newZone]);
    setCurrentPoints([]);
    setActiveMode('NONE');
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      await cameraApi.update(camera.id, {
        restricted_zones: zones,
        virtual_lines: lines,
      });
      onSaved();
      onClose();
    } catch (e) {
      console.error('Failed to save zones:', e);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs select-none animate-fade-in">
      <div className="bg-white border border-[#E5E1EE] rounded-2xl w-full max-w-4xl p-6 space-y-4 shadow-2xl flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[#E5E1EE] pb-3">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-lg bg-[#F0EDFD] border border-[#DCD4FB] flex items-center justify-center text-[#7C5CFC]">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-extrabold text-[#211D2B]">
                Configure Exclusion Zones & Tripwires — {camera.name}
              </h2>
              <p className="text-xs text-[#625D6D]">
                Node: <strong className="text-[#7C5CFC] font-mono-num">{camera.camera_identifier}</strong> • Location: {camera.location}
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

        {/* Toolbar */}
        <div className="flex flex-wrap items-center justify-between gap-2 p-3 bg-[#FAF9FD] rounded-xl border border-[#E5E1EE] text-xs">
          <div className="flex items-center space-x-2">
            <button
              onClick={() => {
                setActiveMode(activeMode === 'DRAW_ZONE' ? 'NONE' : 'DRAW_ZONE');
                setCurrentPoints([]);
              }}
              className={`px-3.5 py-1.5 rounded-lg font-bold transition flex items-center space-x-1.5 ${
                activeMode === 'DRAW_ZONE'
                  ? 'bg-[#7C5CFC] text-white shadow-xs'
                  : 'bg-white border border-[#E5E1EE] text-[#4328A8] hover:bg-[#F0EDFD]'
              }`}
            >
              <Plus className="w-4 h-4" />
              <span>{activeMode === 'DRAW_ZONE' ? 'Click on Canvas to Add Points' : 'Draw Polygon Zone'}</span>
            </button>

            <button
              onClick={() => {
                setActiveMode(activeMode === 'DRAW_LINE' ? 'NONE' : 'DRAW_LINE');
                setCurrentPoints([]);
              }}
              className={`px-3.5 py-1.5 rounded-lg font-bold transition flex items-center space-x-1.5 ${
                activeMode === 'DRAW_LINE'
                  ? 'bg-[#7C5CFC] text-white shadow-xs'
                  : 'bg-white border border-[#E5E1EE] text-[#4328A8] hover:bg-[#F0EDFD]'
              }`}
            >
              <Plus className="w-4 h-4" />
              <span>{activeMode === 'DRAW_LINE' ? 'Click 2 Points for Line' : 'Draw Virtual Tripwire'}</span>
            </button>

            {activeMode === 'DRAW_ZONE' && currentPoints.length >= 3 && (
              <button
                onClick={handleFinishPolygon}
                className="px-3.5 py-1.5 rounded-lg bg-[#16A34A] hover:bg-[#15803D] text-white font-bold transition flex items-center space-x-1.5 shadow-xs"
              >
                <Check className="w-4 h-4" />
                <span>Complete Polygon ({currentPoints.length} Points)</span>
              </button>
            )}
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => {
                setZones([]);
                setLines([]);
                setCurrentPoints([]);
              }}
              className="px-3 py-1.5 rounded-lg bg-white border border-[#E5E1EE] text-[#B91C1C] hover:bg-[#FEE2E2] font-bold transition flex items-center space-x-1"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Clear All</span>
            </button>
          </div>
        </div>

        {/* Interactive SVG Canvas Area */}
        <div className="relative w-full h-80 sm:h-96 rounded-xl bg-[#FAF9FD] border border-[#E5E1EE] overflow-hidden tactical-grid-light flex items-center justify-center">
          <svg
            viewBox="0 0 100 100"
            className="w-full h-full cursor-crosshair"
            onClick={handleCanvasClick}
          >
            {/* Existing Polygons */}
            {zones.map((z, idx) => (
              <polygon
                key={z.id || idx}
                points={z.polygon?.map((p: ZoneCoordinate) => `${p.x},${p.y}`).join(' ')}
                fill="rgba(124, 92, 252, 0.25)"
                stroke="#7C5CFC"
                strokeWidth="0.8"
              />
            ))}

            {/* Existing Tripwire Lines */}
            {lines.map((l, idx) => (
              <line
                key={l.id || idx}
                x1={l.p1.x}
                y1={l.p1.y}
                x2={l.p2.x}
                y2={l.p2.y}
                stroke="#D97706"
                strokeWidth="1.2"
                strokeDasharray="2 1"
              />
            ))}

            {/* Current Drawing Points */}
            {currentPoints.map((p, idx) => (
              <circle key={idx} cx={p.x} cy={p.y} r="1.5" fill="#7C5CFC" stroke="#FFFFFF" strokeWidth="0.5" />
            ))}

            {currentPoints.length > 1 && activeMode === 'DRAW_ZONE' && (
              <polyline
                points={currentPoints.map((p) => `${p.x},${p.y}`).join(' ')}
                fill="none"
                stroke="#7C5CFC"
                strokeWidth="0.8"
                strokeDasharray="1 1"
              />
            )}
          </svg>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between pt-3 border-t border-[#E5E1EE]">
          <div className="text-xs text-[#625D6D]">
            Configured: <strong className="text-[#7C5CFC]">{zones.length} Zones</strong> • <strong className="text-[#D97706]">{lines.length} Tripwires</strong>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-[#FAF9FD] hover:bg-[#F0EDFD] text-[#625D6D] text-xs font-bold"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-6 py-2 rounded-xl bg-[#7C5CFC] hover:bg-[#6A46F9] text-white text-xs font-bold transition shadow-xs disabled:opacity-50"
            >
              {saving ? 'Saving Topology...' : 'Save Configuration'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
