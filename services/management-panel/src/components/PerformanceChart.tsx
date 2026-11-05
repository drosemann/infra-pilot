interface PerformanceChartProps {
  data: number[];

  height?: number;
  label?: string;
  value?: string;
  maxValue?: number;
}

export const PerformanceChart = ({
  data,

  height = 120,
  label = 'TPS',
  value,
  maxValue,
}: PerformanceChartProps) => {
  if (data.length === 0) return null;

  const max = maxValue || Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;

  return (
    <div className="card p-4">
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm text-white/45">{label}</span>
        {value && <span className="text-lg font-bold text-white">{value}</span>}
      </div>
      <div className="relative" style={{ height }}>
        <svg
          width="100%"
          height={height}
          viewBox={`0 0 ${data.length - 1} 100`}
          preserveAspectRatio="none"
          className="overflow-visible"
        >
          <defs>
            <linearGradient id={`grad-${label}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="currentColor" stopOpacity="0.3" />
              <stop offset="100%" stopColor="currentColor" stopOpacity="0.05" />
            </linearGradient>
          </defs>
          <polyline
            points={data
              .map((v, i) => `${i},${100 - ((v - min) / range) * 100}`)
              .join(' ')}
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            vectorEffect="non-scaling-stroke"
            className="text-blue-400"
          />
          <polygon
            points={`${data
              .map((v, i) => `${i},${100 - ((v - min) / range) * 100}`)
              .join(' ')},${data.length - 1},100 0,100`}
            fill={`url(#grad-${label})`}
            className="text-blue-400"
          />
        </svg>
      </div>
      <div className="flex items-center justify-between mt-2 text-xs text-white/40">
        <span>5m ago</span>
        <span>now</span>
      </div>
    </div>
  );
};

export default PerformanceChart;
