import { useState, useEffect } from 'react';
import { Camera as CameraIcon, Plus, Shield, Grid, List } from 'lucide-react';
import { cameraApi } from '../services/sentinelApi';
import type { Camera } from '../types';
import { ZoneCanvasModal } from '../components/ZoneCanvasModal';
import { StatusIndicator } from '../components/StatusIndicator';

export function CamerasPage() {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [selectedCameraForZones, setSelectedCameraForZones] = useState<Camera | null>(null);
  const [addModalOpen, setAddModalOpen] = useState(false);
  const [newCameraName, setNewCameraName] = useState('');
  const [newCameraId, setNewCameraId] = useState('');
  const [newLocation, setNewLocation] = useState('');
  const [newZone, setNewZone] = useState('');

  const loadCameras = async () => {
    try {
      const data = await cameraApi.list();
      setCameras(data);
    } catch (e) {
      console.error('Failed to load cameras:', e);
    }
  };

  useEffect(() => {
    loadCameras();
  }, []);

  const handleCreateCamera = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await cameraApi.create({
        name: newCameraName,
        camera_identifier: newCameraId,
        location: newLocation,
        zone: newZone,
        status: 'ONLINE',
        restricted_zones: [],
        virtual_lines: [],
      });
      setAddModalOpen(false);
      setNewCameraName('');
      setNewCameraId('');
      setNewLocation('');
      setNewZone('');
      loadCameras();
    } catch (err) {
      console.error('Failed to create camera:', err);
    }
  };

  return (
    <div className="w-full space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-[#E5E1EE]">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#211D2B] tracking-tight flex items-center space-x-3">
            <span>Surveillance Sensor Fleet</span>
            <span className="text-xs px-3 py-1 rounded-full bg-[#F0EDFD] border border-[#DCD4FB] text-[#7C5CFC] font-bold">
              {cameras.length} Nodes Configured
            </span>
          </h1>
          <p className="text-sm text-[#625D6D] mt-1 font-medium">
            Manage physical CCTV stream endpoints, exclusion zones, and virtual tripwires
          </p>
        </div>

        <div className="flex items-center space-x-3">
          {/* View Toggle */}
          <div className="flex bg-white border border-[#E5E1EE] rounded-lg p-1 shadow-2xs">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 rounded-md transition ${
                viewMode === 'grid' ? 'bg-[#F0EDFD] text-[#7C5CFC]' : 'text-[#8E8899] hover:text-[#211D2B]'
              }`}
              title="Grid View"
            >
              <Grid className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 rounded-md transition ${
                viewMode === 'list' ? 'bg-[#F0EDFD] text-[#7C5CFC]' : 'text-[#8E8899] hover:text-[#211D2B]'
              }`}
              title="List View"
            >
              <List className="w-4 h-4" />
            </button>
          </div>

          <button
            onClick={() => setAddModalOpen(true)}
            className="px-5 py-2.5 rounded-lg bg-[#7C5CFC] hover:bg-[#6A46F9] text-white font-bold text-sm flex items-center space-x-2 transition shadow-xs"
          >
            <Plus className="w-4 h-4" />
            <span>Register New Camera</span>
          </button>
        </div>
      </div>

      {/* Cameras View (Grid or List) */}
      {viewMode === 'grid' ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {cameras.map((camera) => (
            <div
              key={camera.id}
              className="rounded-xl bg-white border border-[#E5E1EE] p-5 space-y-4 flex flex-col justify-between shadow-xs hover:border-[#7C5CFC] transition"
            >
              <div className="space-y-3.5">
                <div className="flex items-center justify-between border-b border-[#E5E1EE] pb-3">
                  <div className="flex items-center space-x-3">
                    <div className="w-9 h-9 rounded-lg bg-[#F0EDFD] border border-[#DCD4FB] flex items-center justify-center text-[#7C5CFC]">
                      <CameraIcon className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="font-bold text-base text-[#211D2B] truncate max-w-[140px]">{camera.name}</div>
                      <div className="text-xs text-[#7C5CFC] font-bold font-mono-num">{camera.camera_identifier}</div>
                    </div>
                  </div>
                  <StatusIndicator status={camera.status} showLabel={false} />
                </div>

                <div className="p-3.5 rounded-lg bg-[#FAF9FD] border border-[#E5E1EE] space-y-2 text-xs text-[#625D6D]">
                  <div className="flex justify-between">
                    <span className="text-[#8E8899]">Location:</span>
                    <span className="text-[#211D2B] font-semibold truncate max-w-[120px]">{camera.location}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#8E8899]">Sector:</span>
                    <span className="text-[#211D2B] font-medium">{camera.zone || 'Northern Perimeter'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#8E8899]">Exclusion Zones:</span>
                    <span className="text-[#7C5CFC] font-bold">{camera.restricted_zones?.length || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#8E8899]">Virtual Tripwires:</span>
                    <span className="text-[#7C5CFC] font-bold">{camera.virtual_lines?.length || 0}</span>
                  </div>
                </div>
              </div>

              <div className="pt-2 border-t border-[#E5E1EE]">
                <button
                  onClick={() => setSelectedCameraForZones(camera)}
                  className="w-full py-2.5 rounded-lg bg-[#FAF9FD] hover:bg-[#F0EDFD] border border-[#E5E1EE] text-[#4328A8] text-xs font-bold flex items-center justify-center space-x-2 transition"
                >
                  <Shield className="w-4 h-4 text-[#7C5CFC]" />
                  <span>Configure Zones & Tripwires</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="rounded-xl bg-white border border-[#E5E1EE] overflow-hidden shadow-xs">
          <table className="w-full text-left text-sm">
            <thead className="bg-[#FAF9FD] border-b border-[#E5E1EE] text-xs text-[#8E8899] uppercase tracking-wider">
              <tr>
                <th className="py-3.5 px-5">Status</th>
                <th className="py-3.5 px-5">Identifier</th>
                <th className="py-3.5 px-5">Camera Name</th>
                <th className="py-3.5 px-5">Location</th>
                <th className="py-3.5 px-5">Sector</th>
                <th className="py-3.5 px-5">Zones & Lines</th>
                <th className="py-3.5 px-5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E5E1EE]">
              {cameras.map((camera) => (
                <tr key={camera.id} className="hover:bg-[#FAF9FD] transition">
                  <td className="py-4 px-5">
                    <StatusIndicator status={camera.status} showLabel={true} />
                  </td>
                  <td className="py-4 px-5 font-bold text-[#7C5CFC] font-mono-num">{camera.camera_identifier}</td>
                  <td className="py-4 px-5 font-bold text-[#211D2B]">{camera.name}</td>
                  <td className="py-4 px-5 text-[#625D6D]">{camera.location}</td>
                  <td className="py-4 px-5 text-[#211D2B] font-medium">{camera.zone || 'Perimeter'}</td>
                  <td className="py-4 px-5 text-[#625D6D]">
                    <span className="text-[#7C5CFC] font-bold">{camera.restricted_zones?.length || 0} Zones</span> •{' '}
                    <span className="text-[#7C5CFC] font-bold">{camera.virtual_lines?.length || 0} Lines</span>
                  </td>
                  <td className="py-4 px-5 text-right">
                    <button
                      onClick={() => setSelectedCameraForZones(camera)}
                      className="px-4 py-1.5 rounded-lg bg-[#F0EDFD] hover:bg-[#E3DCFB] text-[#4328A8] text-xs font-bold transition"
                    >
                      Configure Zones
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Add Camera Modal */}
      {addModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs select-none">
          <div className="bg-white border border-[#E5E1EE] rounded-xl w-full max-w-md p-6 space-y-4 shadow-2xl">
            <h2 className="text-lg font-extrabold text-[#211D2B]">
              Register Surveillance Camera Node
            </h2>
            <form onSubmit={handleCreateCamera} className="space-y-4 text-xs">
              <div className="space-y-1">
                <label className="text-[#8E8899] font-bold uppercase">CAMERA NAME</label>
                <input
                  type="text"
                  required
                  value={newCameraName}
                  onChange={(e) => setNewCameraName(e.target.value)}
                  placeholder="Sector 4 Forward PTZ"
                  className="w-full px-3.5 py-2.5 bg-[#FAF9FD] border border-[#E5E1EE] rounded-lg text-[#211D2B] text-sm focus:outline-none focus:border-[#7C5CFC]"
                />
              </div>

              <div className="space-y-1">
                <label className="text-[#8E8899] font-bold uppercase">IDENTIFIER CODE</label>
                <input
                  type="text"
                  required
                  value={newCameraId}
                  onChange={(e) => setNewCameraId(e.target.value)}
                  placeholder="CAM-SEC4-PTZ"
                  className="w-full px-3.5 py-2.5 bg-[#FAF9FD] border border-[#E5E1EE] rounded-lg text-[#211D2B] text-sm focus:outline-none focus:border-[#7C5CFC]"
                />
              </div>

              <div className="space-y-1">
                <label className="text-[#8E8899] font-bold uppercase">PHYSICAL LOCATION</label>
                <input
                  type="text"
                  required
                  value={newLocation}
                  onChange={(e) => setNewLocation(e.target.value)}
                  placeholder="Watchtower Post Alpha"
                  className="w-full px-3.5 py-2.5 bg-[#FAF9FD] border border-[#E5E1EE] rounded-lg text-[#211D2B] text-sm focus:outline-none focus:border-[#7C5CFC]"
                />
              </div>

              <div className="space-y-1">
                <label className="text-[#8E8899] font-bold uppercase">SECTOR / ZONE</label>
                <input
                  type="text"
                  value={newZone}
                  onChange={(e) => setNewZone(e.target.value)}
                  placeholder="Sector 4 Perimeter"
                  className="w-full px-3.5 py-2.5 bg-[#FAF9FD] border border-[#E5E1EE] rounded-lg text-[#211D2B] text-sm focus:outline-none focus:border-[#7C5CFC]"
                />
              </div>

              <div className="flex items-center justify-end space-x-3 pt-3">
                <button
                  type="button"
                  onClick={() => setAddModalOpen(false)}
                  className="px-4 py-2.5 rounded-lg bg-[#FAF9FD] hover:bg-[#F0EDFD] text-[#625D6D] text-xs font-bold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2.5 rounded-lg bg-[#7C5CFC] hover:bg-[#6A46F9] text-white font-bold text-xs shadow-xs"
                >
                  Save Node
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {selectedCameraForZones && (
        <ZoneCanvasModal
          camera={selectedCameraForZones}
          onClose={() => setSelectedCameraForZones(null)}
          onSaved={() => {
            loadCameras();
          }}
        />
      )}
    </div>
  );
}
