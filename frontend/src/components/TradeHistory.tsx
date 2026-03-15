import { formatUnits } from 'ethers';
import type { Trade } from '../types';

function truncateHash(hash: string): string {
  if (hash.length <= 14) return hash;
  return `${hash.slice(0, 8)}...${hash.slice(-6)}`;
}

function formatTime(timestamp: number): string {
  return new Date(timestamp * 1000).toLocaleTimeString();
}

interface Props {
  trades: Trade[];
}

export default function TradeHistory({ trades }: Props) {
  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <h2 className="text-lg font-semibold text-white mb-3">Trade History</h2>

      {trades.length === 0 ? (
        <p className="text-gray-400 text-sm py-8 text-center">
          No trades executed yet
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-gray-400 border-b border-gray-700">
              <tr>
                <th className="pb-2 pr-4">Tx Hash</th>
                <th className="pb-2 pr-4 text-center">Status</th>
                <th className="pb-2 pr-4 text-right">Profit</th>
                <th className="pb-2 pr-4 text-right">Gas Cost</th>
                <th className="pb-2 text-right">Time</th>
              </tr>
            </thead>
            <tbody>
              {trades.map((trade) => {
                const gasCostEth = parseFloat(
                  formatUnits(
                    BigInt(trade.gas_used) * BigInt(trade.gas_price),
                    18
                  )
                );
                const profitEth = parseFloat(
                  formatUnits(trade.profit_actual, 18)
                );

                return (
                  <tr
                    key={trade.tx_hash}
                    className="border-b border-gray-700/50"
                  >
                    <td className="py-2 pr-4">
                      <a
                        href={`https://arbiscan.io/tx/${trade.tx_hash}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="font-mono text-blue-400 hover:text-blue-300 hover:underline"
                      >
                        {truncateHash(trade.tx_hash)}
                      </a>
                    </td>
                    <td className="py-2 pr-4 text-center">
                      {trade.success ? (
                        <span className="text-green-400 font-bold" title="Success">
                          &#10003;
                        </span>
                      ) : (
                        <span
                          className="text-red-400 font-bold"
                          title={trade.error ?? 'Failed'}
                        >
                          &#10007;
                        </span>
                      )}
                    </td>
                    <td
                      className={`py-2 pr-4 text-right font-mono ${
                        profitEth >= 0 ? 'text-green-400' : 'text-red-400'
                      }`}
                    >
                      {profitEth.toFixed(6)} ETH
                    </td>
                    <td className="py-2 pr-4 text-right font-mono text-gray-300">
                      {gasCostEth.toFixed(6)} ETH
                    </td>
                    <td className="py-2 text-right text-gray-400">
                      {formatTime(trade.timestamp)}
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
