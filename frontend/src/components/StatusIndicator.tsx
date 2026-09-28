import type { CameraStatus } from '../types';

interface StatusIndicatorProps {
  status: CameraStatus | 'ACTIVE' | 'INACTIVE' | string;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  pulse?: boolean;
}

export function StatusIndicator({
  status,
  size = 'md',
  showLabel = false,
  pulse = false,
}: StatusIndicatorProps) {
  let colorClass = 'bg-[#8E8899]';
  let labelText = status;
  let textColorClass = 'text-[#625D6D]';

  switch (status.toUpperCase()) {
    case 'ONLINE':
    case 'ACTIVE':
    case 'SECURE':
      colorClass = 'bg-[#16A34A]';
      textColorClass = 'text-[#15803D]';
      labelText = 'Online';
      break;
    case 'DEGRADED':
    case 'WARNING':
      colorClass = 'bg-[#D97706]';
      textColorClass = 'text-[#B45309]';
      labelText = 'Degraded';
      break;
    case 'OFFLINE':
    case 'CRITICAL':
    case 'BREACH':
      colorClass = 'bg-[#D32F2F]';
      textColorClass = 'text-[#B91C1C]';
      labelText = 'Offline';
      break;
    case 'PROCESSING':
      colorClass = 'bg-[#7C5CFC]';
      textColorClass = 'text-[#6A46F9]';
      labelText = 'Processing';
      break;
    default:
      colorClass = 'bg-[#8E8899]';
      textColorClass = 'text-[#625D6D]';
      break;
  }

  const dotSize =
    size === 'sm' ? 'w-2.5 h-2.5' : size === 'md' ? 'w-3 h-3' : 'w-3.5 h-3.5';

  return (
    <div className="inline-flex items-center space-x-2 text-sm">
      <span className="relative flex items-center justify-center">
        <span
          className={`${dotSize} rounded-full ${colorClass} ${
            pulse ? 'animate-ping opacity-75' : ''
          }`}
        />
        {pulse && (
          <span
            className={`absolute top-0 left-0 ${dotSize} rounded-full ${colorClass}`}
          />
        )}
      </span>
      {showLabel && (
        <span className={`font-bold ${textColorClass}`}>
          {labelText}
        </span>
      )}
    </div>
  );
}
