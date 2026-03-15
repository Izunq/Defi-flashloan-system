import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import type { Trade } from '../types';
import { formatUnits } from 'ethers';

interface ChartPoint {
  time: string;
  cumulative: number;
}

function buildChartData(trades: Trade[]): ChartPoint[] {
  if (trades.length === 0) return [];

  const sorted = [...trades].sort((a, b) => a.timestamp - b.timestamp);
  let cumulative = 0;

  return sorted.map((t) => {
    const profitEth = parseFloat(formatUnits(t.profit_actual, 18));
    const gasCostEth = parseFloat(
      formatUnits(BigInt(t.gas_used) * BigInt(t.gas_price), 18)
    );
    cumulative += t.success ? profitEth - gasCostEth : -gasCostEth;

    return {
      time: new Date(t.timestamp * 1000).toLocaleTimeString(),
      cumulative: parseFloat(cumulative.toFixed(6)),
    };
  });
}

interface Props {
  trades: Trade[];
}

export default function PnLChart({ trades }: Props) {
  const data = buildChartData(trades);

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <h2 className="text-lg font-semibold text-white mb-3">
        Cumulative P&amp;L
      </h2>

      {data.length === 0 ? (
        <p className="text-gray-400 text-sm py-8 text-center">
          No trade data available for chart
        </p>
      ) : (
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis
              dataKey="time"
              stroke="#9CA3AF"
              tick={{ fontSize: 11 }}
              interval="preserveStartEnd"
            />
            <YAxis
              stroke="#9CA3AF"
              tick={{ fontSize: 11 }}
              tickFormatter={(v: number) => `${v} ETH`}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1F2937',
                border: '1px solid #374151',
                borderRadius: '0.5rem',
                color: '#F9FAFB',
                fontSize: 12,
              }}
              formatter={(value) => [`${value} ETH`, 'Cumulative P&L']}
            />
            <Line
              type="monotone"
              dataKey="cumulative"
              stroke="#34D399"
              strokeWidth={2}
              dot={{ r: 3, fill: '#34D399' }}
              activeDot={{ r: 5 }}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
