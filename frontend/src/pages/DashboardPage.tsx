import { useEffect, useState } from 'react';
import { Upload, RefreshCw, CheckCircle2 } from 'lucide-react';
import { eventApi, cameraApi, incidentApi, videoApi } from '../services/sentinelApi';
import type {
  Camera, SecurityEvent, Incident, Video
} from '../types';
import { OperationsMap } from '../components/OperationsMap';
import { ActiveIncidentsSection } from '../components/ActiveIncidentsSection';
import { SurveillanceVideoMatrix } from '../components/SurveillanceVideoMatrix';
import { LiveEventStreamSection } from '../components/LiveEventStreamSection';
import { IncidentDrawer } from '../components/IncidentDrawer';
import { VideoUploadModal } from '../components/VideoUploadModal';

interface DashboardPageProps {
  onNavigate: (tab: string) => void;
}

export function DashboardPage({ onNavigate }: DashboardPageProps) {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [videos, setVideos] = useState<Video[]>([]);
  const [activeProcessedVideo, setActiveProcessedVideo] = useState<Video | null>(null);
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [notification, setNotification] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [camsData, vidsData, eventsData, incidentsData] = await Promise.all([
        cameraApi.list(),
        videoApi.list(),
        eventApi.list({ limit: 12 }),
        incidentApi.list(),
      ]);
      setCameras(camsData);
      setVideos(vidsData);
      if (vidsData.length > 0 && !activeProcessedVideo) {
        // Set most recent processed video as default active
        const completedVid = vidsData.find(v => v.processed_path || v.status === 'COMPLETED') || vidsData[0];
        setActiveProcessedVideo(completedVid);
      }
      setEvents(eventsData);
      setIncidents(incidentsData);
    } catch (err) {
      console.error('Failed to load command center data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const timer = setInterval(fetchData, 8000);
    return () => clearInterval(timer);
  }, []);

  const handleVideoUploaded = (newVideo?: Video) => {
    if (newVideo) {
      setActiveProcessedVideo(newVideo);
      setNotification(`Surveillance video '${newVideo.original_filename || newVideo.filename}' deployed to AI Matrix.`);
      setTimeout(() => setNotification(null), 6000);
    }
    fetchData();
  };

  return (
    <div className="w-full space-y-6">
      {/* Dynamic Notification Banner */}
      {notification && (
        <div className="p-4 rounded-xl bg-[#DCFCE7] border border-[#86EFAC] text-[#166534] text-xs sm:text-sm font-bold flex items-center justify-between shadow-xs animate-fade-in">
          <div className="flex items-center space-x-2.5">
            <CheckCircle2 className="w-5 h-5 text-[#16A34A] shrink-0" />
            <span>{notification}</span>
          </div>
          <button
            onClick={() => setNotification(null)}
            className="text-[#15803D] hover:text-[#166534] text-xs font-extrabold uppercase ml-3"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* PAGE HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-[#E5E1EE]">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#211D2B] tracking-tight">
            Border Surveillance Operations Overview
          </h1>
          <p className="text-sm text-[#625D6D] mt-1 font-medium">
            Automated border perimeter surveillance using existing CCTV infrastructure with YOLOv8 analytics and spatial zone intrusion detection
          </p>
        </div>

        <div className="flex items-center space-x-3 shrink-0">
          <button
            onClick={fetchData}
            className="p-2.5 rounded-lg bg-white hover:bg-[#FAF9FD] border border-[#E5E1EE] text-[#625D6D] hover:text-[#211D2B] transition shadow-xs"
            title="Refresh Operational Telemetry"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-[#7C5CFC]' : ''}`} />
          </button>
          <button
            onClick={() => setUploadModalOpen(true)}
            className="px-5 py-2.5 rounded-lg bg-[#7C5CFC] hover:bg-[#6A46F9] text-white font-bold text-sm flex items-center space-x-2 transition shadow-xs"
          >
            <Upload className="w-4 h-4" />
            <span>Ingest Surveillance Video</span>
          </button>
        </div>
      </div>

      {/* SECTION 1: BORDER OPERATIONS GEOSPATIAL MAP (Full Content Width) */}
      <section className="w-full">
        <OperationsMap
          cameras={cameras}
          events={events}
          incidents={incidents}
          onSelectCamera={() => onNavigate('live-surveillance')}
          onSelectIncident={(inc) => setSelectedIncident(inc)}
        />
      </section>

      {/* SECTION 2: ACTIVE INCIDENTS (Full Content Width) */}
      <section className="w-full">
        <ActiveIncidentsSection
          incidents={incidents}
          onSelectIncident={(inc) => setSelectedIncident(inc)}
          onNavigateIncidents={() => onNavigate('incidents')}
        />
      </section>

      {/* SECTION 3: SURVEILLANCE VIDEO MATRIX (2-Column Desktop Grid) */}
      <section className="w-full">
        <SurveillanceVideoMatrix
          cameras={cameras}
          videos={videos}
          activeProcessedVideo={activeProcessedVideo}
          onSelectCamera={() => onNavigate('live-surveillance')}
        />
      </section>

      {/* SECTION 4, 5, 6: LIVE EVENT STREAM, RECENT ACTIVITY, SYSTEM HEALTH */}
      <section className="w-full">
        <LiveEventStreamSection
          events={events}
          onSelectEvent={() => onNavigate('events')}
          onNavigateEvents={() => onNavigate('events')}
          cameraCount={{
            online: cameras.filter((c) => c.status === 'ONLINE').length || 4,
            total: cameras.length || 4,
          }}
        />
      </section>

      {/* Contextual Slide-Over Incident Drawer */}
      <IncidentDrawer
        incident={selectedIncident}
        onClose={() => setSelectedIncident(null)}
        onUpdated={fetchData}
      />

      {/* Video Ingest Modal */}
      {uploadModalOpen && (
        <VideoUploadModal
          cameras={cameras}
          onClose={() => setUploadModalOpen(false)}
          onUploaded={handleVideoUploaded}
        />
      )}
    </div>
  );
}
