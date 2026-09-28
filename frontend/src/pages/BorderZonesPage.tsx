import { Shield } from 'lucide-react';

export function BorderZonesPage() {
  const sectors = [
    {
      id: 'SEC-07',
      name: 'Sector 07 — Northern Perimeter',
      risk: 'HIGH RISK',
      cameras: 4,
      zones: 8,
      tripwires: 4,
      status: 'ACTIVE BREACH DETECTED',
      riskColor: 'text-[#B91C1C]',
      riskBg: 'bg-[#FEE2E2] border-[#FCA5A5]',
    },
    {
      id: 'SEC-04',
      name: 'Sector 04 — Eastern Gate Outpost',
      risk: 'NOMINAL',
      cameras: 2,
      zones: 3,
      tripwires: 2,
      status: 'SECURE PATROL',
      riskColor: 'text-[#15803D]',
      riskBg: 'bg-[#DCFCE7] border-[#86EFAC]',
    },
    {
      id: 'SEC-09',
      name: 'Sector 09 — Riverine Demarcation Sector',
      risk: 'ELEVATED',
      cameras: 2,
      zones: 4,
      tripwires: 3,
      status: 'WATER TRANSIT ALERT',
      riskColor: 'text-[#B45309]',
      riskBg: 'bg-[#FEF3C7] border-[#FCD34D]',
    },
  ];

  return (
    <div className="w-full space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-[#E5E1EE]">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#211D2B] tracking-tight">
            Border Security Sectors & Exclusion Zones
          </h1>
          <p className="text-sm text-[#625D6D] mt-1 font-medium">
            Spatial polygon geometry, virtual perimeter tripwires, and buffer strip enforcement
          </p>
        </div>
      </div>

      {/* Sectors Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {sectors.map((sec) => (
          <div
            key={sec.id}
            className="rounded-xl bg-white border border-[#E5E1EE] p-5 space-y-4 shadow-xs hover:border-[#7C5CFC] transition"
          >
            <div className="flex items-center justify-between border-b border-[#E5E1EE] pb-3">
              <div className="flex items-center space-x-2.5">
                <Shield className="w-5 h-5 text-[#7C5CFC]" />
                <span className="font-extrabold text-base text-[#211D2B]">{sec.name}</span>
              </div>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-xs font-bold text-[#8E8899]">THREAT LEVEL:</span>
              <span className={`px-2.5 py-1 rounded-md text-xs font-bold border ${sec.riskColor} ${sec.riskBg}`}>
                {sec.risk}
              </span>
            </div>

            <div className="p-3.5 rounded-lg bg-[#FAF9FD] border border-[#E5E1EE] space-y-2 text-xs text-[#625D6D]">
              <div className="flex justify-between">
                <span className="text-[#8E8899]">Active Cameras:</span>
                <span className="text-[#211D2B] font-bold">{sec.cameras} Nodes</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#8E8899]">Restricted Zones:</span>
                <span className="text-[#7C5CFC] font-bold">{sec.zones} Polygons</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#8E8899]">Virtual Tripwires:</span>
                <span className="text-[#7C5CFC] font-bold">{sec.tripwires} Lines</span>
              </div>
              <div className="flex justify-between pt-1 border-t border-[#E5E1EE]">
                <span className="text-[#8E8899]">Patrol State:</span>
                <span className="text-[#211D2B] font-bold">{sec.status}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
