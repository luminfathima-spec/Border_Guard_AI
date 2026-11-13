import { useState, useEffect, useRef } from 'react';
import {
  Film, Upload, Radio, Play, RefreshCw, CheckCircle2,
  AlertCircle, Clock, ShieldCheck, X, FileVideo,
  Copy, Check
} from 'lucide-react';
import { videoApi, cameraApi } from '../services/sentinelApi';
import type { Video, Camera, RTSPTestResponse } from '../types';

export function VideoManagementPage() {
  const [videos, setVideos] = useState<Video[]>([]);
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [loading, setLoading] = useState(true);

  // Upload modal state
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedCameraId, setSelectedCameraId] = useState<number | undefined>(undefined);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // RTSP tester modal state
  const [rtspModalOpen, setRtspModalOpen] = useState(false);
  const [rtspUrl, setRtspUrl] = useState('');
  const [rtspTimeout, setRtspTimeout] = useState(5);
  const [testingRtsp, setTestingRtsp] = useState(false);
  const [rtspResult, setRtspResult] = useState<RTSPTestResponse | null>(null);

  // Video preview player state
  const [previewVideo, setPreviewVideo] = useState<Video | null>(null);
  const [copiedSha, setCopiedSha] = useState<number | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const [videoList, cameraList] = await Promise.all([
        videoApi.list(),
        cameraApi.list(),
      ]);
      setVideos(videoList);
      setCameras(cameraList);
    } catch (err) {
      console.error('Failed to load video management data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    // Poll every 10 seconds to update videos that are PROCESSING
    const interval = setInterval(async () => {
      try {
        const videoList = await videoApi.list();
        setVideos(videoList);
      } catch (e) {
        // silent polling catch
      }
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setUploadError(null);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      setSelectedFile(file);
      setUploadError(null);
    }
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    try {
      setUploading(true);
      setUploadError(null);
      await videoApi.upload(selectedFile, selectedCameraId);
      setUploadModalOpen(false);
      setSelectedFile(null);
      setSelectedCameraId(undefined);
      await loadData();
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Video upload failed';
      setUploadError(msg);
    } finally {
      setUploading(false);
    }
  };

  const handleTestRtsp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rtspUrl.trim()) return;

    try {
      setTestingRtsp(true);
      setRtspResult(null);
      const res = await cameraApi.testStream(rtspUrl, rtspTimeout);
      setRtspResult(res);
    } catch (err: any) {
      setRtspResult({
        connected: false,
        stream_url: rtspUrl,
        message: err.response?.data?.detail || err.message || 'Connection test failed',
        tested_at: new Date().toISOString(),
      });
    } finally {
      setTestingRtsp(false);
    }
  };

  const copyShaToClipboard = (sha: string, id: number) => {
    navigator.clipboard.writeText(sha);
    setCopiedSha(id);
    setTimeout(() => setCopiedSha(null), 2000);
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return '—';
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const formatDuration = (seconds?: number) => {
    if (seconds === undefined || seconds === null) return '—';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}m ${secs}s`;
  };

  const totalDuration = videos.reduce((acc, v) => acc + (v.duration || 0), 0);
  const completedCount = videos.filter((v) => v.status === 'COMPLETED').length;
  const processingCount = videos.filter((v) => v.status === 'PROCESSING' || v.status === 'PENDING').length;
  const failedCount = videos.filter((v) => v.status === 'FAILED').length;

  return (
    <div className="w-full space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-[#E5E1EE]">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#211D2B] tracking-tight flex items-center space-x-3">
            <span>Video Ingestion & CCTV Sources</span>
            <span className="text-xs px-3 py-1 rounded-full bg-[#F0EDFD] border border-[#DCD4FB] text-[#7C5CFC] font-bold">
              Phase 2 Active
            </span>
          </h1>
          <p className="text-sm text-[#625D6D] mt-1 font-medium">
            Manage prerecorded surveillance footage, validate chunked uploads with SHA-256 integrity, and test live RTSP stream connections
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={loadData}
            className="p-2.5 rounded-lg bg-white hover:bg-[#FAF9FD] border border-[#E5E1EE] text-[#625D6D] hover:text-[#211D2B] transition shadow-2xs"
            title="Refresh list"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-[#7C5CFC]' : ''}`} />
          </button>

          <button
            onClick={() => {
              setRtspResult(null);
              setRtspModalOpen(true);
            }}
            className="px-4 py-2.5 rounded-lg bg-white hover:bg-[#FAF9FD] border border-[#E5E1EE] text-[#211D2B] font-bold text-sm flex items-center space-x-2 transition shadow-2xs"
          >
            <Radio className="w-4 h-4 text-[#7C5CFC]" />
            <span>Test RTSP Stream</span>
          </button>

          <button
            onClick={() => {
              setSelectedFile(null);
              setUploadError(null);
              setUploadModalOpen(true);
            }}
            className="px-5 py-2.5 rounded-lg bg-[#7C5CFC] hover:bg-[#6A46F9] text-white font-bold text-sm flex items-center space-x-2 transition shadow-xs"
          >
            <Upload className="w-4 h-4" />
            <span>Upload Video</span>
          </button>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white border border-[#E5E1EE] p-5 rounded-2xl shadow-2xs space-y-1">
          <div className="flex items-center justify-between text-xs font-bold text-[#8E8899] uppercase tracking-wider">
            <span>Ingested Videos</span>
            <FileVideo className="w-4 h-4 text-[#7C5CFC]" />
          </div>
          <p className="text-2xl font-black text-[#211D2B]">{videos.length}</p>
          <p className="text-xs text-[#625D6D]">{completedCount} processed and verified</p>
        </div>

        <div className="bg-white border border-[#E5E1EE] p-5 rounded-2xl shadow-2xs space-y-1">
          <div className="flex items-center justify-between text-xs font-bold text-[#8E8899] uppercase tracking-wider">
            <span>Processing Queue</span>
            <Clock className="w-4 h-4 text-[#F59E0B]" />
          </div>
          <p className="text-2xl font-black text-[#211D2B]">{processingCount}</p>
          <p className="text-xs text-[#625D6D]">{failedCount} failed or rejected</p>
        </div>

        <div className="bg-white border border-[#E5E1EE] p-5 rounded-2xl shadow-2xs space-y-1">
          <div className="flex items-center justify-between text-xs font-bold text-[#8E8899] uppercase tracking-wider">
            <span>Total Footage Duration</span>
            <Film className="w-4 h-4 text-[#10B981]" />
          </div>
          <p className="text-2xl font-black text-[#211D2B]">{formatDuration(totalDuration)}</p>
          <p className="text-xs text-[#625D6D]">Max limit: 3,600s / video</p>
        </div>

        <div className="bg-white border border-[#E5E1EE] p-5 rounded-2xl shadow-2xs space-y-1">
          <div className="flex items-center justify-between text-xs font-bold text-[#8E8899] uppercase tracking-wider">
            <span>Integrity Verification</span>
            <ShieldCheck className="w-4 h-4 text-[#7C5CFC]" />
          </div>
          <p className="text-2xl font-black text-[#211D2B]">SHA-256</p>
          <p className="text-xs text-[#625D6D]">Tamper-evident checksumming</p>
        </div>
      </div>

      {/* Video Inventory Table */}
      <div className="bg-white border border-[#E5E1EE] rounded-2xl overflow-hidden shadow-2xs">
        <div className="p-5 border-b border-[#E5E1EE] flex items-center justify-between">
          <div>
            <h2 className="text-lg font-extrabold text-[#211D2B]">Ingestion Records & Media Inventory</h2>
            <p className="text-xs text-[#625D6D] mt-0.5">
              Evidence-grade video files, technical specifications, and background processing status
            </p>
          </div>
        </div>

        {videos.length === 0 ? (
          <div className="p-12 text-center space-y-3">
            <div className="w-12 h-12 rounded-xl bg-[#F0EDFD] text-[#7C5CFC] flex items-center justify-center mx-auto">
              <Film className="w-6 h-6" />
            </div>
            <p className="text-sm font-bold text-[#211D2B]">No video records found</p>
            <p className="text-xs text-[#625D6D] max-w-sm mx-auto">
              Upload an MP4 or CCTV recording file, or ingest one of the pre-bundled border patrol demos to get started.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-[#211D2B]">
              <thead className="bg-[#FAF9FD] text-[11px] font-bold text-[#8E8899] uppercase tracking-wider border-b border-[#E5E1EE]">
                <tr>
                  <th className="px-5 py-3">File / Camera</th>
                  <th className="px-5 py-3">Resolution & FPS</th>
                  <th className="px-5 py-3">Duration</th>
                  <th className="px-5 py-3">File Size</th>
                  <th className="px-5 py-3">SHA-256 Hash</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E5E1EE]">
                {videos.map((vid) => {
                  const camera = cameras.find((c) => c.id === vid.camera_id);
                  return (
                    <tr key={vid.id} className="hover:bg-[#FAF9FD] transition-colors">
                      <td className="px-5 py-3.5">
                        <div className="font-bold text-[#211D2B] truncate max-w-xs" title={vid.original_filename || vid.filename}>
                          {vid.original_filename || vid.filename}
                        </div>
                        <div className="text-xs text-[#8E8899]">
                          {camera ? `Camera: ${camera.name} (${camera.camera_identifier})` : 'Unassigned Camera'}
                        </div>
                      </td>

                      <td className="px-5 py-3.5 text-xs text-[#625D6D]">
                        {vid.resolution ? (
                          <span>
                            <span className="font-semibold text-[#211D2B]">{vid.resolution}</span>
                            {vid.fps ? ` @ ${vid.fps.toFixed(0)} FPS` : ''}
                          </span>
                        ) : (
                          '—'
                        )}
                      </td>

                      <td className="px-5 py-3.5 text-xs text-[#625D6D]">
                        {formatDuration(vid.duration)}
                      </td>

                      <td className="px-5 py-3.5 text-xs text-[#625D6D]">
                        {formatFileSize(vid.file_size_bytes)}
                      </td>

                      <td className="px-5 py-3.5 text-xs">
                        {vid.checksum_sha256 ? (
                          <div className="flex items-center space-x-1 font-mono text-[11px] text-[#625D6D]">
                            <span title={vid.checksum_sha256}>
                              {vid.checksum_sha256.substring(0, 10)}...{vid.checksum_sha256.substring(58)}
                            </span>
                            <button
                              onClick={() => copyShaToClipboard(vid.checksum_sha256!, vid.id)}
                              className="p-1 hover:text-[#7C5CFC] transition"
                              title="Copy full SHA-256"
                            >
                              {copiedSha === vid.id ? (
                                <Check className="w-3.5 h-3.5 text-green-600" />
                              ) : (
                                <Copy className="w-3.5 h-3.5 text-[#8E8899]" />
                              )}
                            </button>
                          </div>
                        ) : (
                          <span className="text-[#8E8899]">—</span>
                        )}
                      </td>

                      <td className="px-5 py-3.5 text-xs">
                        <span
                          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold ${
                            vid.status === 'COMPLETED'
                              ? 'bg-[#ECFDF5] text-[#059669] border border-[#A7F3D0]'
                              : vid.status === 'PROCESSING'
                              ? 'bg-[#EFF6FF] text-[#2563EB] border border-[#BFDBFE]'
                              : vid.status === 'FAILED'
                              ? 'bg-[#FEF2F2] text-[#DC2626] border border-[#FECACA]'
                              : 'bg-[#FFFBEB] text-[#D97706] border border-[#FDE68A]'
                          }`}
                        >
                          {vid.status}
                        </span>
                      </td>

                      <td className="px-5 py-3.5 text-right space-x-2">
                        <button
                          onClick={() => setPreviewVideo(vid)}
                          className="px-3 py-1.5 rounded-lg bg-[#F0EDFD] hover:bg-[#E4DCFC] text-[#7C5CFC] font-bold text-xs inline-flex items-center space-x-1.5 transition"
                          title="Stream Video Preview"
                        >
                          <Play className="w-3.5 h-3.5" />
                          <span>Preview</span>
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Upload Modal */}
      {uploadModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs animate-fade-in">
          <div className="bg-white border border-[#E5E1EE] rounded-2xl w-full max-w-lg p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between border-b border-[#E5E1EE] pb-3">
              <div className="flex items-center space-x-3">
                <div className="w-9 h-9 rounded-lg bg-[#F0EDFD] border border-[#DCD4FB] flex items-center justify-center text-[#7C5CFC]">
                  <Upload className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-lg font-extrabold text-[#211D2B]">Upload Surveillance Video</h2>
                  <p className="text-xs text-[#625D6D]">Max 500 MB • MP4, AVI, MOV, MKV</p>
                </div>
              </div>

              <button
                onClick={() => setUploadModalOpen(false)}
                className="p-1.5 rounded-lg hover:bg-[#FAF9FD] text-[#8E8899] hover:text-[#211D2B] transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleUploadSubmit} className="space-y-4">
              {/* Dropzone */}
              <div
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-[#DCD4FB] hover:border-[#7C5CFC] rounded-xl p-6 text-center cursor-pointer transition bg-[#FAF9FD]"
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="video/mp4,video/avi,video/quicktime,video/x-matroska,.mp4,.avi,.mov,.mkv"
                  onChange={handleFileSelect}
                  className="hidden"
                />

                {selectedFile ? (
                  <div className="space-y-1">
                    <CheckCircle2 className="w-8 h-8 text-[#10B981] mx-auto" />
                    <p className="text-sm font-bold text-[#211D2B]">{selectedFile.name}</p>
                    <p className="text-xs text-[#625D6D]">
                      {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                    </p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <Film className="w-8 h-8 text-[#7C5CFC] mx-auto" />
                    <p className="text-sm font-bold text-[#211D2B]">
                      Drag and drop your video file here, or click to browse
                    </p>
                    <p className="text-xs text-[#8E8899]">
                      Files are hashed with SHA-256 and verified for header authenticity
                    </p>
                  </div>
                )}
              </div>

              {/* Camera selection */}
              <div>
                <label className="block text-xs font-bold text-[#211D2B] uppercase tracking-wider mb-1.5">
                  Associate with Camera (Optional)
                </label>
                <select
                  value={selectedCameraId || ''}
                  onChange={(e) =>
                    setSelectedCameraId(e.target.value ? Number(e.target.value) : undefined)
                  }
                  className="w-full px-3.5 py-2.5 rounded-lg border border-[#E5E1EE] text-sm text-[#211D2B] bg-white focus:outline-hidden focus:border-[#7C5CFC]"
                >
                  <option value="">None / Standalone Recording</option>
                  {cameras.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name} ({c.camera_identifier}) — {c.location}
                    </option>
                  ))}
                </select>
              </div>

              {uploadError && (
                <div className="p-3 rounded-lg bg-[#FEF2F2] border border-[#FECACA] flex items-start space-x-2 text-xs text-[#DC2626]">
                  <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                  <span>{uploadError}</span>
                </div>
              )}

              <div className="flex items-center justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setUploadModalOpen(false)}
                  className="px-4 py-2 rounded-lg border border-[#E5E1EE] text-[#625D6D] hover:bg-[#FAF9FD] text-sm font-bold transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!selectedFile || uploading}
                  className="px-5 py-2 rounded-lg bg-[#7C5CFC] hover:bg-[#6A46F9] disabled:opacity-50 text-white text-sm font-bold flex items-center space-x-2 transition"
                >
                  {uploading ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      <span>Uploading & Validating...</span>
                    </>
                  ) : (
                    <>
                      <Upload className="w-4 h-4" />
                      <span>Start Ingestion</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* RTSP Stream Tester Modal */}
      {rtspModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs animate-fade-in">
          <div className="bg-white border border-[#E5E1EE] rounded-2xl w-full max-w-lg p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between border-b border-[#E5E1EE] pb-3">
              <div className="flex items-center space-x-3">
                <div className="w-9 h-9 rounded-lg bg-[#F0EDFD] border border-[#DCD4FB] flex items-center justify-center text-[#7C5CFC]">
                  <Radio className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-lg font-extrabold text-[#211D2B]">RTSP Stream Connection Probe</h2>
                  <p className="text-xs text-[#625D6D]">
                    Credentials are automatically masked and never stored in cleartext
                  </p>
                </div>
              </div>

              <button
                onClick={() => setRtspModalOpen(false)}
                className="p-1.5 rounded-lg hover:bg-[#FAF9FD] text-[#8E8899] hover:text-[#211D2B] transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleTestRtsp} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-[#211D2B] uppercase tracking-wider mb-1.5">
                  RTSP Stream URL
                </label>
                <input
                  type="text"
                  placeholder="rtsp://admin:secretpass@192.168.1.100:554/stream1"
                  value={rtspUrl}
                  onChange={(e) => setRtspUrl(e.target.value)}
                  required
                  className="w-full px-3.5 py-2.5 rounded-lg border border-[#E5E1EE] text-sm text-[#211D2B] bg-white focus:outline-hidden focus:border-[#7C5CFC] font-mono"
                />
                <p className="text-[11px] text-[#8E8899] mt-1">
                  Format: <code className="bg-[#FAF9FD] px-1 py-0.5 rounded">rtsp://[user:pass@]host[:port]/path</code>
                </p>
              </div>

              <div>
                <label className="block text-xs font-bold text-[#211D2B] uppercase tracking-wider mb-1.5">
                  Timeout (Seconds)
                </label>
                <input
                  type="number"
                  min="1"
                  max="30"
                  value={rtspTimeout}
                  onChange={(e) => setRtspTimeout(Number(e.target.value))}
                  className="w-full px-3.5 py-2.5 rounded-lg border border-[#E5E1EE] text-sm text-[#211D2B] bg-white focus:outline-hidden focus:border-[#7C5CFC]"
                />
              </div>

              {rtspResult && (
                <div
                  className={`p-4 rounded-xl border space-y-2 text-xs ${
                    rtspResult.connected
                      ? 'bg-[#ECFDF5] border-[#A7F3D0] text-[#065F46]'
                      : 'bg-[#FEF2F2] border-[#FECACA] text-[#991B1B]'
                  }`}
                >
                  <div className="flex items-center space-x-2 font-bold text-sm">
                    {rtspResult.connected ? (
                      <>
                        <CheckCircle2 className="w-5 h-5 text-[#059669]" />
                        <span>Stream Connected Successfully</span>
                      </>
                    ) : (
                      <>
                        <AlertCircle className="w-5 h-5 text-[#DC2626]" />
                        <span>Connection Failed</span>
                      </>
                    )}
                  </div>
                  <p>{rtspResult.message}</p>
                  <div className="pt-2 border-t border-black/10 space-y-1 font-mono text-[11px]">
                    <div>
                      <span className="font-bold">Masked URL:</span> {rtspResult.stream_url}
                    </div>
                    {rtspResult.resolution && (
                      <div>
                        <span className="font-bold">Resolution:</span> {rtspResult.resolution}
                      </div>
                    )}
                    {rtspResult.fps !== undefined && (
                      <div>
                        <span className="font-bold">FPS:</span> {rtspResult.fps}
                      </div>
                    )}
                    {rtspResult.latency_ms !== undefined && (
                      <div>
                        <span className="font-bold">Latency:</span> {rtspResult.latency_ms} ms
                      </div>
                    )}
                  </div>
                </div>
              )}

              <div className="flex items-center justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setRtspModalOpen(false)}
                  className="px-4 py-2 rounded-lg border border-[#E5E1EE] text-[#625D6D] hover:bg-[#FAF9FD] text-sm font-bold transition"
                >
                  Close
                </button>
                <button
                  type="submit"
                  disabled={!rtspUrl.trim() || testingRtsp}
                  className="px-5 py-2 rounded-lg bg-[#7C5CFC] hover:bg-[#6A46F9] disabled:opacity-50 text-white text-sm font-bold flex items-center space-x-2 transition"
                >
                  {testingRtsp ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      <span>Probing Stream...</span>
                    </>
                  ) : (
                    <>
                      <Radio className="w-4 h-4" />
                      <span>Test Connection</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Video Preview Player Modal */}
      {previewVideo && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs animate-fade-in">
          <div className="bg-white border border-[#E5E1EE] rounded-2xl w-full max-w-3xl p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-[#E5E1EE] pb-3">
              <div className="flex items-center space-x-3">
                <div className="w-9 h-9 rounded-lg bg-[#F0EDFD] border border-[#DCD4FB] flex items-center justify-center text-[#7C5CFC]">
                  <Film className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-lg font-extrabold text-[#211D2B]">
                    Stream Preview — {previewVideo.original_filename || previewVideo.filename}
                  </h2>
                  <p className="text-xs text-[#625D6D]">
                    HTTP 206 Partial Content range stream • ID #{previewVideo.id}
                  </p>
                </div>
              </div>

              <button
                onClick={() => setPreviewVideo(null)}
                className="p-1.5 rounded-lg hover:bg-[#FAF9FD] text-[#8E8899] hover:text-[#211D2B] transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Video Player */}
            <div className="relative aspect-video rounded-xl bg-black overflow-hidden flex items-center justify-center shadow-inner">
              <video
                src={videoApi.getStreamUrl(previewVideo.id)}
                controls
                autoPlay
                className="w-full h-full object-contain"
              >
                Your browser does not support the video tag.
              </video>
            </div>

            {/* Metadata Footer */}
            <div className="bg-[#FAF9FD] border border-[#E5E1EE] rounded-xl p-4 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div>
                <span className="text-[#8E8899] block font-medium">Resolution</span>
                <span className="font-bold text-[#211D2B]">{previewVideo.resolution || 'N/A'}</span>
              </div>
              <div>
                <span className="text-[#8E8899] block font-medium">Frame Rate</span>
                <span className="font-bold text-[#211D2B]">
                  {previewVideo.fps ? `${previewVideo.fps.toFixed(1)} FPS` : 'N/A'}
                </span>
              </div>
              <div>
                <span className="text-[#8E8899] block font-medium">Duration</span>
                <span className="font-bold text-[#211D2B]">{formatDuration(previewVideo.duration)}</span>
              </div>
              <div>
                <span className="text-[#8E8899] block font-medium">File Size</span>
                <span className="font-bold text-[#211D2B]">{formatFileSize(previewVideo.file_size_bytes)}</span>
              </div>
            </div>

            {previewVideo.checksum_sha256 && (
              <div className="flex items-center justify-between text-xs bg-white border border-[#E5E1EE] rounded-lg px-3 py-2">
                <div className="flex items-center space-x-2 text-[#625D6D] font-mono truncate mr-2">
                  <ShieldCheck className="w-4 h-4 text-[#7C5CFC] shrink-0" />
                  <span className="truncate">{previewVideo.checksum_sha256}</span>
                </div>
                <button
                  onClick={() => copyShaToClipboard(previewVideo.checksum_sha256!, previewVideo.id)}
                  className="px-2 py-1 rounded bg-[#F0EDFD] hover:bg-[#E4DCFC] text-[#7C5CFC] font-bold text-xs shrink-0 transition"
                >
                  {copiedSha === previewVideo.id ? 'Copied!' : 'Copy Hash'}
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
