import React from 'react';

type DonutChartProps = {
  value: number; // 0-100
  size?: number;
  thickness?: number;
  color?: string;
};

export const DonutChart: React.FC<DonutChartProps> = ({ value, size = 80, thickness = 10, color }) => {
  const r = (size - thickness) / 2;
  const c = 2 * Math.PI * r;
  const dash = (value / 100) * c;
  const stroke = color ?? '#4ea8ff';
  return (
    <svg width={size} height={size} role="img" aria-label={`Donut ${value}%`}>
      <circle cx={size / 2} cy={size / 2} r={r} stroke="rgba(255,255,255,0.2)" strokeWidth={thickness} fill="none" />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={r}
        stroke={stroke}
        strokeWidth={thickness}
        fill="none"
        strokeDasharray={c}
        strokeDashoffset={c - dash}
        strokeLinecap="round"
        transform={`rotate(-90 ${size / 2} ${size / 2})`}
      />
      <text x="50%" y="50%" textAnchor="middle" dominantBaseline="middle" fill="#fff" fontSize={size * 0.25}>
        {value}%
      </text>
    </svg>
  );
};

export default DonutChart;
