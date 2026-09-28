import type { SeverityLevel } from '../types';

interface SeverityBadgeProps {
  severity: SeverityLevel | string;
  size?: 'sm' | 'md' | 'lg';
}

export function SeverityBadge({ severity, size = 'sm' }: SeverityBadgeProps) {
  const norm = severity.toUpperCase();

  let colorClasses = 'bg-[#F0EEF8] text-[#4A4556] border-[#D6CFDF]';
  let label = 'Low';

  if (norm === 'CRITICAL') {
    colorClasses = 'bg-[#FEE2E2] text-[#B91C1C] border-[#FCA5A5]';
    label = 'Critical';
  } else if (norm === 'HIGH') {
    colorClasses = 'bg-[#FEF3C7] text-[#B45309] border-[#FCD34D]';
    label = 'High';
  } else if (norm === 'MEDIUM') {
    colorClasses = 'bg-[#FEF9C3] text-[#A16207] border-[#FDE047]';
    label = 'Medium';
  } else if (norm === 'LOW') {
    colorClasses = 'bg-[#DCFCE7] text-[#15803D] border-[#86EFAC]';
    label = 'Low';
  }

  const padding =
    size === 'sm'
      ? 'px-2.5 py-1 text-xs font-bold'
      : size === 'md'
      ? 'px-3.5 py-1 text-sm font-bold'
      : 'px-4 py-1.5 text-base font-bold';

  return (
    <span
      className={`inline-flex items-center rounded-md border tracking-wide uppercase ${padding} ${colorClasses} shadow-xs`}
    >
      {label}
    </span>
  );
}
