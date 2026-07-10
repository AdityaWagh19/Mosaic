import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

interface TimeSeriesChartProps {
  data: { timestep: number; diversity: number; pairwise_distance: number }[];
}

export const TimeSeriesChart: React.FC<TimeSeriesChartProps> = ({ data }) => {
  return (
    <div style={{ width: '100%', height: '400px' }}>
      <h3 style={{ marginBottom: 'var(--spacing-16)', fontFamily: 'var(--font-egyptienne-f-lt)', fontSize: 'var(--text-heading-sm)' }}>
        Diversity Decay
      </h3>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--color-paper-cool)" />
          <XAxis 
            dataKey="timestep" 
            tick={{ fill: 'var(--color-stone)', fontSize: 11, fontFamily: 'var(--font-diatype-mono)' }} 
            axisLine={{ stroke: 'var(--color-paper-cool)' }}
            tickLine={false}
          />
          <YAxis 
            tick={{ fill: 'var(--color-stone)', fontSize: 11, fontFamily: 'var(--font-diatype-mono)' }} 
            axisLine={{ stroke: 'var(--color-paper-cool)' }}
            tickLine={false}
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: 'var(--color-paper-warm)', 
              border: 'none', 
              borderRadius: 'var(--radius-cards)',
              boxShadow: 'var(--shadow-md)',
              fontFamily: 'var(--font-diatype)'
            }} 
          />
          <Legend wrapperStyle={{ fontFamily: 'var(--font-diatype)', fontSize: '13px' }} />
          <Line 
            type="monotone" 
            dataKey="diversity" 
            stroke="var(--color-ink)" 
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
          <Line 
            type="monotone" 
            dataKey="pairwise_distance" 
            stroke="var(--color-stone)" 
            strokeWidth={2}
            dot={false} 
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};
