import { formatUnits } from 'ethers';
import type { PoolStatus as PoolStatusT } from '../types';

interface Props {
  pool: PoolStatusT | null;
}

export default function PoolStatus({ pool }: Props) {
  if (!pool) {
    return (
      <div className="bg-gray-800 rounded-lg p-4">
        <h2 className="text-lg font-semibold text-white mb-3">
          Mudarabah Pool
        </h2>
        <p className="text-gray-400 text-sm py-8 text-center">
          Waiting for pool data...
        </p>
      </div>
    );
  }

  const tvlEth = parseFloat(formatUnits(pool.tvl, 18)).toFixed(4);
  const totalProfitEth = parseFloat(formatUnits(pool.total_profit, 18)).toFixed(4);
  const providerPct = (pool.provider_share_bps / 100).toFixed(1);
  const mudaribPct = (pool.mudarib_share_bps / 100).toFixed(1);

  const stats = [
    { label: 'TVL', value: `${tvlEth} ETH` },
    { label: 'Providers', value: pool.provider_count.toString() },
    { label: 'Total Profit', value: `${totalProfitEth} ETH` },
    { label: 'Utilization', value: `${pool.utilization.toFixed(1)}%` },
    {
      label: 'Profit Split',
      value: `${providerPct}% / ${mudaribPct}%`,
      subtitle: 'Provider / Mudarib',
    },
  ];

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <h2 className="text-lg font-semibold text-white mb-3">
        Mudarabah Pool
      </h2>

      <div className="space-y-3">
        {stats.map((s) => (
          <div
            key={s.label}
            className="flex items-center justify-between py-2 border-b border-gray-700/50 last:border-0"
          >
            <div>
              <span className="text-gray-400 text-sm">{s.label}</span>
              {s.subtitle && (
                <span className="block text-gray-500 text-xs">
                  {s.subtitle}
                </span>
              )}
            </div>
            <span className="font-mono text-white text-sm">{s.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
