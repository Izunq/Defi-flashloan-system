import { useApi } from './hooks/useApi';
import StatusBar from './components/StatusBar';
import OpportunityTable from './components/OpportunityTable';
import TradeHistory from './components/TradeHistory';
import PnLChart from './components/PnLChart';
import PoolStatus from './components/PoolStatus';

function Spinner() {
  return (
    <div className="flex items-center justify-center py-20">
      <div className="w-10 h-10 border-4 border-gray-600 border-t-green-400 rounded-full animate-spin" />
    </div>
  );
}

export default function App() {
  const { status, opportunities, trades, pnl, pool, loading, error } = useApi();

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="border-b border-gray-800 px-6 py-4">
        <h1 className="text-2xl font-bold tracking-tight">
          DeFi Flash Loan Arbitrage Dashboard
        </h1>
        <p className="text-sm text-gray-400 mt-1">
          Real-time monitoring &middot; Arbitrum One
        </p>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6 space-y-6">
        {/* Error banner */}
        {error && (
          <div className="bg-red-900/40 border border-red-700 text-red-300 rounded-lg px-4 py-3 text-sm">
            <span className="font-semibold">API Error:</span> {error}
            <span className="block text-xs text-red-400 mt-1">
              Retrying every 5 seconds...
            </span>
          </div>
        )}

        {loading ? (
          <Spinner />
        ) : (
          <>
            {/* Status bar */}
            <StatusBar status={status} />

            {/* P&L summary cards */}
            {pnl && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <SummaryCard
                  label="Net Profit"
                  value={`$${pnl.net_profit.toFixed(2)}`}
                  accent={pnl.net_profit >= 0}
                />
                <SummaryCard
                  label="Total Profit (USD)"
                  value={`$${pnl.total_profit_usd.toFixed(2)}`}
                  accent
                />
                <SummaryCard
                  label="Trade Count"
                  value={pnl.trade_count.toString()}
                  accent
                />
                <SummaryCard
                  label="Win Rate"
                  value={
                    trades.length > 0
                      ? `${(
                          (trades.filter((t) => t.success).length /
                            trades.length) *
                          100
                        ).toFixed(1)}%`
                      : 'N/A'
                  }
                  accent
                />
              </div>
            )}

            {/* Two-column layout */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Left column */}
              <div className="space-y-6">
                <OpportunityTable opportunities={opportunities} />
                <TradeHistory trades={trades} />
              </div>

              {/* Right column */}
              <div className="space-y-6">
                <PnLChart trades={trades} />
                <PoolStatus pool={pool} />
              </div>
            </div>
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-800 px-6 py-3 text-center text-xs text-gray-500">
        Flash Loan Arbitrage System &middot; Data refreshes every 5s
      </footer>
    </div>
  );
}

/* ---------- small helper component ---------- */

function SummaryCard({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent: boolean;
}) {
  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <p className="text-xs text-gray-400 uppercase tracking-wide">{label}</p>
      <p
        className={`text-xl font-bold mt-1 font-mono ${
          accent ? 'text-green-400' : 'text-red-400'
        }`}
      >
        {value}
      </p>
    </div>
  );
}
