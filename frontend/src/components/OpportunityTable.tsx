import { formatUnits } from 'ethers';
import type { Opportunity } from '../types';

function timeAgo(timestamp: number): string {
  const diff = Math.floor(Date.now() / 1000 - timestamp);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  return `${Math.floor(diff / 3600)}h ago`;
}

interface Props {
  opportunities: Opportunity[];
}

export default function OpportunityTable({ opportunities }: Props) {
  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <h2 className="text-lg font-semibold text-white mb-3">
        Live Opportunities
      </h2>

      {opportunities.length === 0 ? (
        <p className="text-gray-400 text-sm py-8 text-center">
          No opportunities found
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-gray-400 border-b border-gray-700">
              <tr>
                <th className="pb-2 pr-4">Pair</th>
                <th className="pb-2 pr-4">DEX A &rarr; B</th>
                <th className="pb-2 pr-4 text-right">Spread %</th>
                <th className="pb-2 pr-4 text-right">Est. Profit</th>
                <th className="pb-2 text-right">Time</th>
              </tr>
            </thead>
            <tbody>
              {opportunities.map((opp, i) => {
                const isHot = opp.spread_pct > 0.5;
                return (
                  <tr
                    key={`${opp.pair}-${opp.timestamp}-${i}`}
                    className={`border-b border-gray-700/50 ${
                      isHot ? 'bg-green-900/20' : ''
                    }`}
                  >
                    <td className="py-2 pr-4 font-mono text-white">
                      {opp.pair}
                    </td>
                    <td className="py-2 pr-4 text-gray-300">
                      {opp.dex_a} &rarr; {opp.dex_b}
                    </td>
                    <td
                      className={`py-2 pr-4 text-right font-mono ${
                        isHot ? 'text-green-400 font-bold' : 'text-gray-300'
                      }`}
                    >
                      {opp.spread_pct.toFixed(3)}%
                    </td>
                    <td className="py-2 pr-4 text-right font-mono text-gray-300">
                      {parseFloat(formatUnits(opp.amount_in, 18)).toFixed(4)} ETH
                    </td>
                    <td className="py-2 text-right text-gray-400">
                      {timeAgo(opp.timestamp)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
