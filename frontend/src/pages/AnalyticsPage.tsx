import { useState, useEffect } from 'react';
import { TrendingUp } from 'lucide-react';
import { analyticsApi } from '../services/sentinelApi';

export function AnalyticsPage() {
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await analyticsApi.getOverview();
        setData(res);
      } catch (e) {
        console.error('Failed to load analytics:', e);
      }
    };
    load();
  }, []);

  return (
    <div className="w-full space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-[#E5E1EE]">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#211D2B] tracking-tight flex items-center space-x-3">
            <span>Operational Surveillance Analytics</span>
            <span className="text-xs px-3 py-1 rounded-full bg-[#F0EDFD] border border-[#DCD4FB] text-[#7C5CFC] font-bold">
              Real-Time Metrics
            </span>
          </h1>
          <p className="text-sm text-[#625D6D] mt-1 font-medium">
            Longitudinal breach frequency, classification distribution, and sector risk velocity
          </p>
        </div>
      </div>

      {/* 4 KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="p-5 rounded-xl bg-white border border-[#E5E1EE] space-y-2 shadow-xs">
          <div className="text-xs text-[#8E8899] font-bold uppercase tracking-wider">TOTAL DETECTIONS</div>
          <div className="text-3xl font-extrabold text-[#211D2B] font-mono-num">{data?.total_events_today || 28}</div>
          <div className="text-xs text-[#16A34A] font-semibold flex items-center space-x-1">
            <TrendingUp className="w-3.5 h-3.5" />
            <span>+14% vs yesterday</span>
          </div>
        </div>

        <div className="p-5 rounded-xl bg-white border border-[#E5E1EE] space-y-2 shadow-xs">
          <div className="text-xs text-[#8E8899] font-bold uppercase tracking-wider">SECURITY INCIDENTS</div>
          <div className="text-3xl font-extrabold text-[#7C5CFC] font-mono-num">{data?.critical_incidents || 3}</div>
          <div className="text-xs text-[#8E8899] font-medium">2 Active • 1 Resolved</div>
        </div>

        <div className="p-5 rounded-xl bg-white border border-[#E5E1EE] space-y-2 shadow-xs">
          <div className="text-xs text-[#8E8899] font-bold uppercase tracking-wider">ACTIVE ALERTS</div>
          <div className="text-3xl font-extrabold text-[#D32F2F] font-mono-num">{data?.active_alerts || 1}</div>
          <div className="text-xs text-[#B91C1C] font-semibold">Immediate QRT Action</div>
        </div>

        <div className="p-5 rounded-xl bg-white border border-[#E5E1EE] space-y-2 shadow-xs">
          <div className="text-xs text-[#8E8899] font-bold uppercase tracking-wider">SENSOR FLEET UPTIME</div>
          <div className="text-3xl font-extrabold text-[#16A34A] font-mono-num">99.8%</div>
          <div className="text-xs text-[#16A34A] font-semibold">{data?.active_cameras || 4}/{data?.total_cameras || 4} Online</div>
        </div>
      </div>

      {/* Chart Placeholders / Visual Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Detection Breakdown */}
        <div className="p-6 rounded-xl bg-white border border-[#E5E1EE] space-y-4 shadow-xs">
          <h3 className="text-lg font-extrabold text-[#211D2B]">Detection Classification Breakdown</h3>
          <div className="space-y-3 pt-2">
            {[
              { label: 'Restricted Zone Incursions', count: 12, pct: '42%', color: 'bg-[#7C5CFC]' },
              { label: 'Virtual Line Crossings', count: 8, pct: '28%', color: 'bg-[#9B7EDE]' },
              { label: 'Loitering in Buffer Strip', count: 5, pct: '18%', color: 'bg-[#D97706]' },
              { label: 'Vehicle Boundary Approaches', count: 3, pct: '12%', color: 'bg-[#16A34A]' },
            ].map((item, idx) => (
              <div key={idx} className="space-y-1.5 text-xs">
                <div className="flex justify-between font-bold text-[#211D2B]">
                  <span>{item.label}</span>
                  <span className="font-mono-num">{item.count} ({item.pct})</span>
                </div>
                <div className="h-2.5 rounded-full bg-[#FAF9FD] border border-[#E5E1EE] overflow-hidden">
                  <div className={`h-full rounded-full ${item.color}`} style={{ width: item.pct }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Sector Threat Index */}
        <div className="p-6 rounded-xl bg-white border border-[#E5E1EE] space-y-4 shadow-xs">
          <h3 className="text-lg font-extrabold text-[#211D2B]">Sector Threat Velocity Index</h3>
          <div className="space-y-3 pt-2">
            {[
              { sector: 'Sector 07 — Northern Perimeter', risk: 'HIGH', score: 88, color: 'text-[#B91C1C]', bar: 'bg-[#D32F2F]' },
              { sector: 'Sector 09 — Riverine Demarcation', risk: 'MODERATE', score: 54, color: 'text-[#B45309]', bar: 'bg-[#D97706]' },
              { sector: 'Sector 04 — Eastern Gate Outpost', risk: 'LOW', score: 18, color: 'text-[#15803D]', bar: 'bg-[#16A34A]' },
            ].map((s, idx) => (
              <div key={idx} className="p-3.5 rounded-xl bg-[#FAF9FD] border border-[#E5E1EE] space-y-2">
                <div className="flex justify-between items-center text-xs">
                  <span className="font-bold text-[#211D2B]">{s.sector}</span>
                  <span className={`font-bold ${s.color}`}>{s.risk} (Score: {s.score}/100)</span>
                </div>
                <div className="h-2 rounded-full bg-white border border-[#E5E1EE] overflow-hidden">
                  <div className={`h-full rounded-full ${s.bar}`} style={{ width: `${s.score}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
