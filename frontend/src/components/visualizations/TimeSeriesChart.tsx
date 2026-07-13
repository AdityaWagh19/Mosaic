import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import type { TimelinePoint } from '../../types/models';

export function TimeSeriesChart({ data }: { data: TimelinePoint[] }) {
  return (
    <div className="chart">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 16, right: 12, left: -16, bottom: 0 }}>
          <CartesianGrid stroke="var(--color-hairline)" vertical={false} />
          <XAxis 
            dataKey="timestep" 
            tick={{ fontSize: 11, fill: '#737373' }} 
            tickLine={false} 
            minTickGap={30}
          />
          <YAxis 
            tick={{ fontSize: 11, fill: '#737373' }} 
            tickLine={false} 
          />
          <Tooltip 
            contentStyle={{ border: '1px solid #e5e7eb', borderRadius: 8, fontSize: 12 }} 
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Line 
            type="monotone" 
            dataKey="diversity" 
            name="Diversity" 
            stroke="#0077ff" 
            dot={false} 
            strokeWidth={2} 
            isAnimationActive 
            animationDuration={300} 
          />
          <Line 
            type="monotone" 
            dataKey="pairwise_distance" 
            name="Pairwise distance" 
            stroke="#000" 
            dot={false} 
            strokeWidth={2} 
            isAnimationActive 
            animationDuration={300} 
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
