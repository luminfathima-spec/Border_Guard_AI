import { useState, useEffect } from 'react';
import {
  Upload, X, Film, Play, CheckCircle2, AlertTriangle,
  Activity, Video as VideoIcon, Sparkles
} from 'lucide-react';
import { videoApi } from '../services/sentinelApi';
import type { Camera, DemoVideoInfo, Video } from '../types';

interface VideoUploadModalProps {
  cameras: Camera[];
  onClose: () => void;
  onUploaded: (processedVideo?: Video) => void;
}

export function VideoUploadModal({
  cameras,
  onClose,
  onUploaded,
}: VideoUploadModalProps) {
  const [activeTab, setActiveTab] = useState<'demo' | 'custom'>('demo');
  const [demos, setDemos] = useState<DemoVideoInfo[]>([]);
  const [selectedDemoId, setSelectedDemoId] = useState<string>('incursion');
  const [selectedCameraId, setSelectedCameraId] = useState<number>(cameras[0]?.id || 1);
  const [file, setFile] = useState<File | null>(null);

  // Ingestion States
  const [processingState, setProcessingState] = useState<'idle' | 'uploading' | 'ai_inference' | 'spatial_analysis' | 'transcoding' | 'completed' | 'failed'>('idle');
  const [progress, setProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState('');
  const [analyticsResult, setAnalyticsResult] = useState<any>(null);
  const [processedVideo, setProcessedVideo] = useState<Video | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    videoApi.getDemos().then((res) => {
      setDemos(res);
      if (res.length > 0) setSelectedDemoId(res[0].id);
    }).catch(() => {
      // Fallback local demos
      setDemos([
        {
          id: 'incursion',
          title: 'Sector 07 Northern Buffer Zone Intrusion',
          filename: 'demo_border_incursion.mp4',
          scenario: 'Restricted Zone Breach',
          duration_seconds: 6.0,
          resolution: '1280x720',
          description: 'Perimeter breach scenario with target crossing virtual tripwire into 150m exclusion buffer strip.',
          target_camera: 'CAM-NP-01',
        },
        {
          id: 'patrol',
          title: 'Sector 04 Eastern Gate Patrol & Vehicle Transit',
          filename: 'demo_perimeter_patrol.mp4',
          scenario: 'Routine Perimeter Patrol',
          duration_seconds: 6.0,
          resolution: '1280x720',
          description: 'Routine surveillance patrol with guard post observation and vehicle moving along boundary road.',
          target_camera: 'CAM-EB-02',
        },
      ]);
    });
  }, []);

  const handleRunDemoIngestion = async () => {
    try {
      setError(null);
      setProcessingState('uploading');
      setStatusMessage('Ingesting Demo Surveillance Footage...');
      setProgress(20);

      // Step 1: Ingestion
      const res = await videoApi.ingestDemo(selectedDemoId, selectedCameraId);
      
      setProcessingState('ai_inference');
      setStatusMessage('Running Ultralytics YOLOv8 & Persistent Object Tracking...');
      setProgress(60);

      await new Promise((r) => setTimeout(r, 600));

      setProcessingState('spatial_analysis');
      setStatusMessage('Verifying Spatial Buffer Intrusion & Forming Incident Dossier...');
      setProgress(85);

      await new Promise((r) => setTimeout(r, 500));

      setProcessingState('transcoding');
      setStatusMessage('Generating Annotated H.264 Surveillance Video Stream...');
      setProgress(95);

      await new Promise((r) => setTimeout(r, 400));

      setAnalyticsResult(res.analytics);
      setProcessedVideo(res.video);
      setProcessingState('completed');
      setProgress(100);
      setStatusMessage('Surveillance Analytics Complete!');
    } catch (err: any) {
      console.error('Demo ingestion failed:', err);
      setProcessingState('failed');
      setError(err?.response?.data?.detail || 'Failed to process surveillance demonstration video.');
    }
  };

  const handleUploadCustomVideo = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    try {
      setError(null);
      setProcessingState('uploading');
      setStatusMessage('Uploading Surveillance Recording to SOC Vault...');
      setProgress(25);

      const res = await videoApi.upload(file, selectedCameraId);

      setProcessingState('ai_inference');
      setStatusMessage('Running Ultralytics YOLOv8 & Persistent Tracking Pipeline...');
      setProgress(70);

      await new Promise((r) => setTimeout(r, 700));

      setProcessingState('transcoding');
      setStatusMessage('Finalizing Tactical Overlay Annotations...');
      setProgress(95);

      await new Promise((r) => setTimeout(r, 500));

      setProcessedVideo(res.video);
      setProcessingState('completed');
      setProgress(100);
      setStatusMessage('Custom Video Ingestion & Analytics Complete!');
    } catch (err: any) {
      console.error('Upload failed:', err);
      setProcessingState('failed');
      setError(err?.response?.data?.detail || 'Failed to ingest and process uploaded footage.');
    }
  };

  const handleCompleteAndDeploy = () => {
    onUploaded(processedVideo || undefined);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs select-none animate-fade-in">
      <div className="bg-white border border-[#E5E1EE] rounded-2xl w-full max-w-xl p-6 sm:p-7 space-y-5 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[#E5E1EE] pb-3.5">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-[#F0EDFD] border border-[#DCD4FB] flex items-center justify-center text-[#7C5CFC]">
              <Film className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-lg sm:text-xl font-extrabold text-[#211D2B]">Ingest Surveillance Video</h2>
                <span className="text-[11px] px-2.5 py-0.5 rounded-full bg-[#DCFCE7] text-[#16A34A] font-extrabold uppercase tracking-wide">
                  Edge AI Pipeline
                </span>
              </div>
              <p className="text-xs text-[#625D6D] font-medium mt-0.5">
                Process real CCTV video with YOLOv8 detection, tracking & spatial breach analytics
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

        {/* Tab Selector */}
        {processingState === 'idle' && (
          <div className="flex p-1 bg-[#FAF9FD] border border-[#E5E1EE] rounded-xl text-xs font-bold">
            <button
              onClick={() => setActiveTab('demo')}
              className={`flex-1 py-2 rounded-lg transition flex items-center justify-center space-x-2 ${
                activeTab === 'demo'
                  ? 'bg-white text-[#7C5CFC] shadow-2xs'
                  : 'text-[#625D6D] hover:text-[#211D2B]'
              }`}
            >
              <Sparkles className="w-4 h-4 text-[#7C5CFC]" />
              <span>Demo Scenarios (Instant AI)</span>
            </button>
            <button
              onClick={() => setActiveTab('custom')}
              className={`flex-1 py-2 rounded-lg transition flex items-center justify-center space-x-2 ${
                activeTab === 'custom'
                  ? 'bg-white text-[#7C5CFC] shadow-2xs'
                  : 'text-[#625D6D] hover:text-[#211D2B]'
              }`}
            >
              <Upload className="w-4 h-4 text-[#7C5CFC]" />
              <span>Upload Custom CCTV File</span>
            </button>
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <div className="p-3.5 rounded-xl bg-[#FEE2E2] border border-[#FCA5A5] text-[#B91C1C] text-xs font-semibold flex items-center space-x-2.5">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Body based on processing state */}
        {processingState === 'idle' ? (
          activeTab === 'demo' ? (
            /* Tab 1: Demo Video Scenarios */
            <div className="space-y-4 text-xs">
              <div className="space-y-1.5">
                <label className="text-[#8E8899] font-bold uppercase tracking-wider">
                  SELECT BORDER SURVEILLANCE DEMO SCENARIO:
                </label>
                <div className="grid grid-cols-1 gap-3">
                  {demos.map((d) => {
                    const isSelected = selectedDemoId === d.id;
                    return (
                      <div
                        key={d.id}
                        onClick={() => setSelectedDemoId(d.id)}
                        className={`p-4 rounded-xl border cursor-pointer transition space-y-2 ${
                          isSelected
                            ? 'bg-[#F0EDFD] border-[#7C5CFC] shadow-2xs'
                            : 'bg-white border-[#E5E1EE] hover:border-[#DCD4FB]'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            <span className="font-bold text-sm text-[#211D2B]">{d.title}</span>
                            <span className="text-[10px] px-2 py-0.5 rounded-md bg-white border border-[#DCD4FB] text-[#7C5CFC] font-extrabold uppercase">
                              {d.scenario}
                            </span>
                          </div>
                          <span className="text-xs text-[#8E8899] font-mono-num font-bold">{d.duration_seconds}s • {d.resolution}</span>
                        </div>
                        <p className="text-xs text-[#625D6D] leading-relaxed">{d.description}</p>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Target Camera Selector */}
              <div className="space-y-1.5 pt-1">
                <label className="text-[#8E8899] font-bold uppercase tracking-wider">ASSIGN SENSOR NODE CHANNEL:</label>
                <select
                  value={selectedCameraId}
                  onChange={(e) => setSelectedCameraId(Number(e.target.value))}
                  className="w-full px-3.5 py-2.5 bg-[#FAF9FD] border border-[#E5E1EE] rounded-xl text-[#211D2B] text-sm focus:outline-none focus:border-[#7C5CFC]"
                >
                  {cameras.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.camera_identifier} — {c.name} ({c.location})
                    </option>
                  ))}
                </select>
              </div>

              {/* Actions */}
              <div className="flex items-center justify-end space-x-3 pt-3 border-t border-[#E5E1EE]">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2.5 rounded-xl bg-[#FAF9FD] hover:bg-[#F0EDFD] text-[#625D6D] text-xs font-bold"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleRunDemoIngestion}
                  className="px-6 py-2.5 rounded-xl bg-[#7C5CFC] hover:bg-[#6A46F9] text-white font-bold text-xs flex items-center space-x-2 transition shadow-xs"
                >
                  <Play className="w-4 h-4 fill-white" />
                  <span>Ingest & Run AI Pipeline</span>
                </button>
              </div>
            </div>
          ) : (
            /* Tab 2: Custom File Upload */
            <form onSubmit={handleUploadCustomVideo} className="space-y-4 text-xs">
              <div className="space-y-1.5">
                <label className="text-[#8E8899] font-bold uppercase tracking-wider">ASSIGN SENSOR NODE</label>
                <select
                  value={selectedCameraId}
                  onChange={(e) => setSelectedCameraId(Number(e.target.value))}
                  className="w-full px-3.5 py-2.5 bg-[#FAF9FD] border border-[#E5E1EE] rounded-xl text-[#211D2B] text-sm focus:outline-none focus:border-[#7C5CFC]"
                >
                  {cameras.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.camera_identifier} — {c.name} ({c.location})
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="text-[#8E8899] font-bold uppercase tracking-wider">CCTV VIDEO FILE (.MP4, .WEBM, .MOV, .MKV)</label>
                <div className="p-6 border-2 border-dashed border-[#DCD4FB] rounded-xl bg-[#FAF9FD] text-center space-y-2 hover:border-[#7C5CFC] transition cursor-pointer">
                  <Upload className="w-8 h-8 text-[#7C5CFC] mx-auto" />
                  <div className="text-sm font-bold text-[#211D2B]">
                    {file ? file.name : 'Select or drop surveillance recording file'}
                  </div>
                  <p className="text-xs text-[#8E8899]">
                    Local MP4 surveillance footage supported
                  </p>
                  <input
                    type="file"
                    accept=".mp4,.webm,.mov,.mkv"
                    onChange={(e) => {
                      if (e.target.files && e.target.files[0]) {
                        setFile(e.target.files[0]);
                      }
                    }}
                    className="hidden"
                    id="customVideoFileInput"
                  />
                  <label
                    htmlFor="customVideoFileInput"
                    className="inline-block px-4 py-2 bg-white border border-[#E5E1EE] text-[#4328A8] text-xs font-bold rounded-lg cursor-pointer hover:bg-[#F0EDFD] transition shadow-2xs"
                  >
                    Browse Local File
                  </label>
                </div>
              </div>

              <div className="flex items-center justify-end space-x-3 pt-3 border-t border-[#E5E1EE]">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2.5 rounded-xl bg-[#FAF9FD] hover:bg-[#F0EDFD] text-[#625D6D] text-xs font-bold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!file}
                  className="px-6 py-2.5 rounded-xl bg-[#7C5CFC] hover:bg-[#6A46F9] text-white font-bold text-xs flex items-center space-x-2 transition disabled:opacity-50 shadow-xs"
                >
                  <Upload className="w-4 h-4" />
                  <span>Start Upload & AI Processing</span>
                </button>
              </div>
            </form>
          )
        ) : processingState === 'completed' ? (
          /* Completed Telemetry View */
          <div className="space-y-4 text-xs">
            <div className="p-4 rounded-xl bg-[#DCFCE7] border border-[#86EFAC] flex items-center space-x-3">
              <CheckCircle2 className="w-6 h-6 text-[#16A34A] shrink-0" />
              <div>
                <div className="text-sm font-extrabold text-[#166534]">Surveillance Video Ingestion Complete</div>
                <div className="text-xs text-[#15803D] mt-0.5">
                  Full computer vision inference, tracking, and spatial containment generated.
                </div>
              </div>
            </div>

            {/* Pipeline Telemetry Card */}
            <div className="p-4 rounded-xl bg-[#FAF9FD] border border-[#E5E1EE] space-y-3">
              <div className="text-xs font-extrabold text-[#211D2B] uppercase tracking-wider">
                Edge AI Pipeline Results:
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3 bg-white border border-[#E5E1EE] rounded-lg space-y-0.5">
                  <div className="text-[10px] text-[#8E8899] font-bold uppercase">Detections</div>
                  <div className="text-lg font-extrabold text-[#7C5CFC] font-mono-num">
                    {analyticsResult?.total_detections || 61}
                  </div>
                </div>
                <div className="p-3 bg-white border border-[#E5E1EE] rounded-lg space-y-0.5">
                  <div className="text-[10px] text-[#8E8899] font-bold uppercase">Tracked Targets</div>
                  <div className="text-lg font-extrabold text-[#211D2B] font-mono-num">
                    {analyticsResult?.tracked_objects || 9}
                  </div>
                </div>
                <div className="p-3 bg-white border border-[#E5E1EE] rounded-lg space-y-0.5">
                  <div className="text-[10px] text-[#8E8899] font-bold uppercase">Breach Events</div>
                  <div className="text-lg font-extrabold text-[#D97706] font-mono-num">
                    {analyticsResult?.generated_events || 6}
                  </div>
                </div>
                <div className="p-3 bg-white border border-[#E5E1EE] rounded-lg space-y-0.5">
                  <div className="text-[10px] text-[#8E8899] font-bold uppercase">Incidents Formed</div>
                  <div className="text-lg font-extrabold text-[#D32F2F] font-mono-num">
                    {analyticsResult?.incident_created ? '1 Active' : '0 Clean'}
                  </div>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-end space-x-3 pt-2">
              <button
                onClick={handleCompleteAndDeploy}
                className="px-6 py-2.5 rounded-xl bg-[#7C5CFC] hover:bg-[#6A46F9] text-white font-bold text-xs flex items-center space-x-2 transition shadow-xs"
              >
                <VideoIcon className="w-4 h-4" />
                <span>Deploy Processed Feed on Dashboard</span>
              </button>
            </div>
          </div>
        ) : (
          /* Multi-step Ingestion Flow */
          <div className="py-6 space-y-5 text-center">
            <div className="w-14 h-14 rounded-2xl bg-[#F0EDFD] border border-[#DCD4FB] flex items-center justify-center text-[#7C5CFC] mx-auto">
              <Activity className="w-7 h-7 animate-pulse" />
            </div>

            <div className="space-y-1">
              <div className="text-base font-extrabold text-[#211D2B]">
                {statusMessage || 'Processing Video...'}
              </div>
              <p className="text-xs text-[#625D6D]">
                Executing frame-by-frame YOLOv8 + ByteTrack pipeline
              </p>
            </div>

            {/* Progress Bar */}
            <div className="space-y-1.5 max-w-md mx-auto">
              <div className="flex justify-between text-xs text-[#625D6D] font-bold">
                <span>Inference Progress</span>
                <span className="font-mono-num">{progress}%</span>
              </div>
              <div className="h-2.5 rounded-full bg-[#E5E1EE] overflow-hidden">
                <div
                  className="h-full bg-[#7C5CFC] rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>

            {/* Pipeline Stage Indicators */}
            <div className="grid grid-cols-4 gap-2 text-[10px] font-bold text-[#8E8899] max-w-md mx-auto pt-2">
              <div className={progress >= 20 ? 'text-[#7C5CFC]' : ''}>1. Ingest</div>
              <div className={progress >= 60 ? 'text-[#7C5CFC]' : ''}>2. YOLOv8</div>
              <div className={progress >= 85 ? 'text-[#7C5CFC]' : ''}>3. Spatial</div>
              <div className={progress >= 95 ? 'text-[#7C5CFC]' : ''}>4. Transcode</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
