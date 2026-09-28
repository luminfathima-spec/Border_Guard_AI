import { useEffect, useState } from 'react';
import { Upload, Layers, Radio } from 'lucide-react';
import { cameraApi, videoApi } from '../services/sentinelApi';
import type { Camera, Video } from '../types';
import { VideoUploadModal } from '../components/VideoUploadModal';

export function MonitoringPage() {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [videos, setVideos] = useState<Video[]>([]);
  const [activeProcessedVideo, setActiveProcessedVideo] = useState<Video | null>(null);
  const [selectedCamera, setSelectedCamera] = useState<Camera | null>(null);
  const [showOverlays, setShowOverlays] = useState(true);
  const [uploadModalOpen, setUploadModalOpen] = useState(false);

  const loadData = async () => {
    try {
      const [camsData, vidsData] = await Promise.all([
        cameraApi.list(),
        videoApi.list(),
      ]);
      setCameras(camsData);
      setVideos(vidsData);
      if (camsData.length > 0 && !selectedCamera) {
        setSelectedCamera(camsData[0]);
      }
      if (vidsData.length > 0 && !activeProcessedVideo) {
        const completedVid = vidsData.find(v => v.processed_path || v.status === 'COMPLETED') || vidsData[0];
        setActiveProcessedVideo(completedVid);
      }
    } catch (e) {
      console.error('Failed to load monitoring data:', e);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const matchedVideo = activeProcessedVideo && (activeProcessedVideo.camera_id === selectedCamera?.id || !videos.length)
    ? activeProcessedVideo
    : (videos.find((v) => v.camera_id === selectedCamera?.id) || activeProcessedVideo || videos[0]);

  let videoSrc = '';
  if (matchedVideo?.processed_path) {
    videoSrc = `http://localhost:8000/static/processed/${matchedVideo.processed_path.split('/').pop()}`;
  } else if (matchedVideo?.filename) {
    videoSrc = `http://localhost:8000/static/uploads/${matchedVideo.filename}`;
  } else {
    videoSrc = `http://localhost:8000/static/demo/demo_border_incursion.mp4`;
  }

  return (
    <div className="w-full space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-[#E5E1EE]">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#211D2B] tracking-tight flex items-center space-x-3">
            <span>Live Surveillance Operations Console</span>
            <span className="text-xs px-3 py-1 rounded-full bg-[#F0EDFD] border border-[#DCD4FB] text-[#7C5CFC] font-bold">
              Channel: {selectedCamera?.camera_identifier || 'CAM-01'}
            </span>
          </h1>
          <p className="text-sm text-[#625D6D] mt-1 font-medium">
            Real-time video telemetry, edge YOLOv8 detection bounding, and spatial intrusion vectoring
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => setShowOverlays(!showOverlays)}
            className={`px-4 py-2 rounded-lg text-sm font-bold border flex items-center space-x-2 transition ${
              showOverlays
                ? 'bg-[#F0EDFD] text-[#4328A8] border-[#DCD4FB]'
                : 'bg-white text-[#625D6D] border-[#E5E1EE]'
            }`}
          >
            <Layers className="w-4 h-4 text-[#7C5CFC]" />
            <span>{showOverlays ? 'AI Detection Overlays: ON' : 'AI Detection Overlays: OFF'}</span>
          </button>

          <button
            onClick={() => setUploadModalOpen(true)}
            className="px-5 py-2 rounded-lg bg-[#7C5CFC] hover:bg-[#6A46F9] text-white font-bold text-sm flex items-center space-x-2 transition shadow-xs"
          >
            <Upload className="w-4 h-4" />
            <span>Ingest Channel Feed</span>
          </button>
        </div>
      </div>

      {/* Main Console Split */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 w-full">
        {/* Left 4 Cols: Channels List */}
        <div className="lg:col-span-4 space-y-4">
          <div className="rounded-xl bg-white border border-[#E5E1EE] p-5 space-y-4 shadow-xs">
            <div className="text-xs font-bold text-[#8E8899] uppercase tracking-wider border-b border-[#E5E1EE] pb-2.5">
              Surveillance Sensor Channels ({cameras.length})
            </div>

            <div className="space-y-2.5 max-h-[600px] overflow-y-auto pr-1">
              {cameras.map((cam) => {
                const isSelected = selectedCamera?.id === cam.id;
                const isOnline = cam.status === 'ONLINE';
                return (
                  <div
                    key={cam.id}
                    onClick={() => setSelectedCamera(cam)}
                    className={`p-4 rounded-xl border cursor-pointer transition space-y-2 ${
                      isSelected
                        ? 'bg-[#F0EDFD] border-[#7C5CFC] text-[#211D2B]'
                        : 'bg-[#FAF9FD] border-[#E5E1EE] text-[#625D6D] hover:border-[#C4BAE0]'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span
                          className={`w-3 h-3 rounded-full ${
                            isOnline ? 'bg-[#16A34A]' : 'bg-[#D32F2F]'
                          }`}
                        />
                        <span className="font-bold text-base text-[#211D2B]">{cam.name}</span>
                      </div>
                      <span className="text-[#7C5CFC] text-xs font-bold font-mono-num">{cam.camera_identifier}</span>
                    </div>
                    <div className="flex justify-between text-xs text-[#8E8899]">
                      <span>{cam.location}</span>
                      <span className="text-[#211D2B] font-semibold">{cam.restricted_zones?.length || 0} Zones</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Center & Right 8 Cols: Large Primary Feed & Node Telemetry */}
        <div className="lg:col-span-8 space-y-5">
          <div className="rounded-xl bg-white border border-[#E5E1EE] p-5 space-y-4 shadow-xs">
            {/* Header */}
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2.5 font-bold text-lg text-[#211D2B]">
                <Radio className="w-5 h-5 text-[#16A34A] animate-pulse" />
                <span>{selectedCamera?.camera_identifier} — {selectedCamera?.name}</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-[11px] px-2.5 py-0.5 rounded-full bg-[#DCFCE7] text-[#15803D] font-extrabold uppercase">
                  DEMO FEED
                </span>
                <span className="text-xs px-3 py-1 rounded-full bg-[#F0EDFD] text-[#4328A8] font-bold">
                  Active Optical Stream
                </span>
              </div>
            </div>

            {/* Video Viewport */}
            <div className="relative aspect-video rounded-xl bg-[#0B0D10] overflow-hidden flex items-center justify-center shadow-inner">
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

              {/* Watermark OSD */}
              <div className="absolute top-3 left-3 px-3 py-1.5 rounded-md bg-black/80 text-xs text-[#16A34A] font-bold flex items-center space-x-2 backdrop-blur-xs">
                <span className="w-2 h-2 rounded-full bg-[#16A34A] animate-ping"></span>
                <span>{selectedCamera?.camera_identifier || 'CAM-01'}</span>
                <span className="text-white/40">|</span>
                <span className="text-white">{selectedCamera?.location || 'Sector 07 North'}</span>
                <span className="text-white/40">|</span>
                <span className="text-[#7C5CFC]">YOLOv8 Edge Detect</span>
              </div>
            </div>

            {/* Bottom Stream Telemetry Strip */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div className="p-3 rounded-lg bg-[#FAF9FD] border border-[#E5E1EE]">
                <div className="text-[#8E8899] font-medium">ENCODING</div>
                <div className="text-[#211D2B] font-bold text-sm font-mono-num">H.264 / 720p</div>
              </div>
              <div className="p-3 rounded-lg bg-[#FAF9FD] border border-[#E5E1EE]">
                <div className="text-[#8E8899] font-medium">FRAME RATE</div>
                <div className="text-[#16A34A] font-bold text-sm font-mono-num">25.0 FPS</div>
              </div>
              <div className="p-3 rounded-lg bg-[#FAF9FD] border border-[#E5E1EE]">
                <div className="text-[#8E8899] font-medium">INFERENCE LATENCY</div>
                <div className="text-[#D97706] font-bold text-sm font-mono-num">18 ms</div>
              </div>
              <div className="p-3 rounded-lg bg-[#FAF9FD] border border-[#E5E1EE]">
                <div className="text-[#8E8899] font-medium">ACTIVE DETECTIONS</div>
                <div className="text-[#7C5CFC] font-bold text-sm font-mono-num">
                  {matchedVideo?.total_detections_count || 61} Targets
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {uploadModalOpen && (
        <VideoUploadModal
          cameras={cameras}
          onClose={() => setUploadModalOpen(false)}
          onUploaded={(v) => {
            if (v) setActiveProcessedVideo(v);
            loadData();
          }}
        />
      )}
    </div>
  );
}
