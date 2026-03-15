import type { SystemStatus } from '../types';

const CHAIN_NAMES: Record<number, string> = {
  1: 'Ethereum',
  42161: 'Arbitrum One',
  10: 'Optimism',
  137: 'Polygon',
  56: 'BNB Chain',
  8453: 'Base',
  43114: 'Avalanche',
};

function formatUptime(seconds: number): string {
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (d > 0) return `${d}d ${h}h ${m}m`;
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

function Dot({ active }: { active: boolean }) {
  return (
    <span
      className={`inline-block w-2.5 h-2.5 rounded-full ${
        active ? 'bg-green-400' : 'bg-red-500'
      }`}
    />
  );
}

interface Props {
  status: SystemStatus | null;
}

export default function StatusBar({ status }: Props) {
  if (!status) {
    return (
      <div className="bg-gray-800 rounded-lg p-4 text-gray-400 text-sm">
        Waiting for system status...
      </div>
    );
  }

  const chainName = CHAIN_NAMES[status.chain_id] ?? `Chain ${status.chain_id}`;
  const gasGwei = (status.gas_price / 1e9).toFixed(2);

  return (
    <div className="bg-gray-800 rounded-lg p-4 flex flex-wrap items-center gap-6 text-sm">
      <div className="flex items-center gap-2">
        <span className="text-gray-400">Network:</span>
        <span className="font-semibold text-white">{chainName}</span>
      </div>

      <div className="flex items-center gap-2">
        <span className="text-gray-400">Block:</span>
        <span className="font-mono text-white">
          {status.block_number.toLocaleString()}
        </span>
      </div>

      <div className="flex items-center gap-2">
        <span className="text-gray-400">Gas:</span>
        <span className="font-mono text-white">{gasGwei} gwei</span>
      </div>

      <div className="flex items-center gap-2">
        <span className="text-gray-400">Uptime:</span>
        <span className="text-white">{formatUptime(status.uptime)}</span>
      </div>

      <div className="flex items-center gap-2">
        <Dot active={status.is_scanning} />
        <span className={status.is_scanning ? 'text-green-400' : 'text-red-400'}>
          {status.is_scanning ? 'Scanning' : 'Idle'}
        </span>
      </div>

      <div className="flex items-center gap-2">
        <Dot active={status.is_executing} />
        <span className={status.is_executing ? 'text-green-400' : 'text-gray-400'}>
          {status.is_executing ? 'Executing' : 'No Execution'}
        </span>
      </div>
    </div>
  );
}
