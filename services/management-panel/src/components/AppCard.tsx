import { FleetPet, type CreatureView } from './FleetPet';
import { FleetWhy } from './FleetWhy';

interface AppCardProps {
  id: string;
  name: string;
  image: string;
  status: 'running' | 'stopped' | 'restarting' | 'error';
  cpu?: number;
  memory?: number;
  uptime?: string;
  ports?: Array<{ hostPort: number; containerPort: number; protocol: string }>;
  onClick?: () => void;
  creature?: CreatureView | null;
}

export const AppCard = ({
  id,
  name,
  image,
  status,
  cpu,
  memory,
  uptime,
  ports = [],
  onClick,
  creature = null,
}: AppCardProps) => {
  const getStatusColor = () => {
    switch (status) {
      case 'running':
        return {
          bg: 'bg-green-500/10',
          text: 'text-green-400',
          dot: 'bg-green-500',
        };
      case 'stopped':
        return {
          bg: 'bg-gray-500/10',
          text: 'text-gray-400',
          dot: 'bg-gray-500',
        };
      case 'restarting':
        return {
          bg: 'bg-yellow-500/10',
          text: 'text-yellow-400',
          dot: 'bg-yellow-500 animate-pulse',
        };
      case 'error':
        return {
          bg: 'bg-red-500/10',
          text: 'text-red-400',
          dot: 'bg-red-500 animate-pulse',
        };
      default:
        return {
          bg: 'bg-white/5',
          text: 'text-white/45',
          dot: 'bg-white/30',
        };
    }
  };

  const statusColor = getStatusColor();

  const getAppInitial = () => (name.trim().charAt(0) || '?').toUpperCase();

  return (
    <div
      onClick={onClick}
      className="card p-6 hover:border-blue-500 hover:shadow-lg hover:shadow-blue-500/20 transition-all cursor-pointer group"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3 flex-1">
          <div className="w-10 h-10 bg-white/10 rounded-lg flex items-center justify-center text-lg group-hover:bg-white/10 transition-colors">
            {getAppInitial()}
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-white truncate">
              {name}{' '}
              {creature && <FleetPet creature={creature} />}
            </h3>
            <p className="text-xs text-white/45 truncate">{image}</p>
          </div>
        </div>

        {/* Status Badge */}
        <div className={`${statusColor.bg} ${statusColor.text} px-3 py-1 rounded-full flex items-center gap-2 flex-shrink-0`}>
          <span className={`w-2 h-2 rounded-full ${statusColor.dot}`}></span>
          <span className="text-xs font-semibold">{status}</span>
        </div>
      </div>

      {/* Living Fleet: why-detail, collapsed by default */}
      {creature && creature.explanation && creature.explanation.length > 0 && (
        <FleetWhy creature={creature} />
      )}

      {/* Uptime */}
      {status === 'running' && uptime && (
        <p className="text-xs text-white/45 mb-4">Uptime: {uptime}</p>
      )}

      {/* Resource Usage */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        {/* CPU */}
        <div>
          <div className="flex justify-between items-center mb-1">
            <span className="text-xs text-white/45">CPU</span>
            <span className="text-sm font-semibold text-white">{cpu !== undefined ? `${cpu}%` : '—'}</span>
          </div>
          <div className="w-full h-1.5 bg-white/10 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-500"
              style={{ width: `${cpu ?? 0}%` }}
            ></div>
          </div>
        </div>

        {/* Memory */}
        <div>
          <div className="flex justify-between items-center mb-1">
            <span className="text-xs text-white/45">MEM</span>
            <span className="text-sm font-semibold text-white">{memory !== undefined ? `${memory}MB` : '—'}</span>
          </div>
          <div className="w-full h-1.5 bg-white/10 rounded-full overflow-hidden">
            <div
              className="h-full bg-white/40"
              style={{ width: `${memory !== undefined ? Math.min(memory / 2, 100) : 0}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* Ports */}
      {ports.length > 0 && (
        <div className="border-t border-white/10 pt-3">
          <p className="text-xs text-white/45 mb-2">Ports:</p>
          <div className="flex flex-wrap gap-1">
            {ports.slice(0, 2).map((port, idx) => (
              <span
                key={idx}
                className="text-xs bg-white/10 text-white/60 px-2 py-1 rounded"
              >
                {port.hostPort}:{port.containerPort}
              </span>
            ))}
            {ports.length > 2 && (
              <span className="text-xs bg-white/10 text-white/45 px-2 py-1 rounded">
                +{ports.length - 2}
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
