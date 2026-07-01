import { createFileRoute, useRouter } from "@tanstack/react-router";
import { createServerFn } from "@tanstack/react-start";
import { readFile } from "node:fs/promises";
import { useEffect } from "react";

// How often the dashboard re-fetches the bot's status snapshot (ms).
const REFRESH_MS = 15000;

type Position = {
  symbol: string;
  side: string;
  amount: number;
  entry_price: number;
  current_price: number;
  stop_loss: number | null;
  take_profit: number | null;
  unrealized_pnl: number;
};

type Status = {
  updated_at: string;
  balance: number;
  portfolio_value: number;
  committed_capital: number;
  available_buying_power: number;
  open_positions: Position[];
  open_position_count: number;
  closed_trades: number;
  regime: Record<string, unknown>;
};

// The trading bot publishes website/status.json each cycle; read it at request
// time. Returns null when the bot hasn't produced a snapshot yet.
const getStatus = createServerFn({ method: "GET" }).handler(async () => {
  try {
    return JSON.parse(await readFile("status.json", "utf8")) as Status;
  } catch {
    return null;
  }
});

export const Route = createFileRoute("/dashboard")({
  loader: () => getStatus(),
  component: Dashboard,
});

function fmtMoney(n: number | undefined): string {
  if (typeof n !== "number" || Number.isNaN(n)) return "—";
  return n.toLocaleString(undefined, { style: "currency", currency: "USD" });
}

function MetricCard({ label, value, accent }: { label: string; value: string; accent?: string }) {
  return (
    <div className={`rounded-3xl border-4 ${accent ?? "border-sage"} bg-white p-8 shadow-xl flex flex-col gap-3`}>
      <span className="text-[10px] md:text-xs tracking-[0.3em] uppercase font-black text-sage-bold">{label}</span>
      <span className="text-3xl md:text-4xl font-bold text-[#1a1c17]">{value}</span>
    </div>
  );
}

function Dashboard() {
  const status = Route.useLoaderData();
  const router = useRouter();

  // Poll: re-run the loader on an interval so the dashboard reflects the bot's
  // latest published snapshot without a manual refresh.
  useEffect(() => {
    const id = setInterval(() => {
      router.invalidate();
    }, REFRESH_MS);
    return () => clearInterval(id);
  }, [router]);

  return (
    <main className="relative min-h-dvh overflow-x-hidden bg-[#faf7f2] dark:bg-[#0d0e0a] selection-botanical pb-32">
      <div className="botanical-pattern absolute inset-0 pointer-events-none opacity-40" />
      <div className="absolute top-[-10%] -left-[10%] w-[40%] h-[40%] bg-[#a8b08e] soft-glow rounded-full pointer-events-none animate-drift" />
      <div className="absolute bottom-[-5%] -right-[10%] w-[50%] h-[50%] bg-[#d6b5ff] soft-glow rounded-full pointer-events-none animate-drift" style={{ animationDelay: "-5s" }} />

      <header className="relative z-20 pt-12 px-6 flex justify-center">
        <div className="flex flex-wrap justify-center items-center gap-4 md:gap-6 text-sage-bold">
          <img src="/flower-sage.svg" className="w-8 h-8 md:w-10 md:h-10" alt="" />
          <span className="text-[10px] md:text-sm tracking-[0.4em] md:tracking-[0.6em] font-bold uppercase">
            Live Garden Status
          </span>
          <img src="/flower-rose.svg" className="w-8 h-8 md:w-10 md:h-10" alt="" />
        </div>
      </header>

      <section className="relative z-10 max-w-6xl mx-auto px-4 md:px-6 pt-16 text-center">
        <h1 className="text-4xl md:text-7xl font-bold tracking-tight text-[#1a1c17] dark:text-white mb-8">
          Bot Dashboard
        </h1>

        {!status ? (
          <div className="mt-16 inline-flex items-center gap-4 px-10 py-6 rounded-full border-4 border-lavender text-lavender-bold text-xs md:text-sm tracking-[0.3em] font-black bg-white shadow-xl uppercase">
            Awaiting first snapshot — start the bot to populate live data
          </div>
        ) : (
          <>
            <div className="mb-12 inline-flex items-center gap-4 px-8 py-4 rounded-full border-4 border-rose text-rose-bold text-[10px] md:text-xs tracking-[0.3em] font-black bg-white shadow-xl uppercase">
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-bold opacity-75" />
                <span className="relative inline-flex rounded-full h-3 w-3 bg-rose-bold" />
              </span>
              Updated {new Date(status.updated_at).toLocaleString()} · auto-refresh {REFRESH_MS / 1000}s
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 md:gap-8 text-left">
              <MetricCard label="Portfolio Value" value={fmtMoney(status.portfolio_value)} accent="border-rose" />
              <MetricCard label="Cash Balance" value={fmtMoney(status.balance)} accent="border-sage" />
              <MetricCard label="Buying Power" value={fmtMoney(status.available_buying_power)} accent="border-lavender" />
              <MetricCard label="Committed Capital" value={fmtMoney(status.committed_capital)} accent="border-sage" />
              <MetricCard label="Open Positions" value={String(status.open_position_count)} accent="border-lavender" />
              <MetricCard label="Closed Trades" value={String(status.closed_trades)} accent="border-rose" />
            </div>

            {status.regime && (status.regime as { regime?: string }).regime && (
              <div className="mt-10 inline-block px-8 py-4 rounded-full border-4 border-sage text-sage-bold text-xs md:text-sm tracking-[0.2em] font-black bg-white shadow-lg uppercase">
                Macro Regime: {(status.regime as { regime?: string }).regime}
                {typeof (status.regime as { position_size_modifier?: number }).position_size_modifier === "number" && (
                  <> — Size ×{(status.regime as { position_size_modifier?: number }).position_size_modifier}</>
                )}
              </div>
            )}

            <div className="mt-16 text-left">
              <h2 className="text-2xl md:text-4xl font-bold text-[#1a1c17] dark:text-white mb-8 tracking-widest text-center">
                Open Positions
              </h2>
              {status.open_positions.length === 0 ? (
                <p className="text-center italic font-botanical text-xl text-[#1a1c17] dark:text-white opacity-70">
                  No open positions — the garden is at rest.
                </p>
              ) : (
                <div className="overflow-x-auto rounded-3xl border-4 border-sage bg-white shadow-xl">
                  <table className="w-full text-left text-sm md:text-base">
                    <thead className="text-sage-bold uppercase text-[10px] md:text-xs tracking-[0.2em]">
                      <tr className="border-b-2 border-sage-soft">
                        <th className="p-4">Symbol</th>
                        <th className="p-4">Side</th>
                        <th className="p-4">Qty</th>
                        <th className="p-4">Entry</th>
                        <th className="p-4">Price</th>
                        <th className="p-4">Unrealized P&L</th>
                      </tr>
                    </thead>
                    <tbody className="text-[#1a1c17] font-medium">
                      {status.open_positions.map((p) => (
                        <tr key={p.symbol} className="border-b border-sage-soft/50">
                          <td className="p-4 font-bold">{p.symbol}</td>
                          <td className="p-4">{p.side}</td>
                          <td className="p-4">{p.amount.toLocaleString(undefined, { maximumFractionDigits: 6 })}</td>
                          <td className="p-4">{fmtMoney(p.entry_price)}</td>
                          <td className="p-4">{fmtMoney(p.current_price)}</td>
                          <td className={`p-4 font-bold ${p.unrealized_pnl >= 0 ? "text-sage-bold" : "text-rose-bold"}`}>
                            {fmtMoney(p.unrealized_pnl)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </>
        )}

        <div className="mt-20">
          <a href="/" className="text-rose-bold hover:scale-110 inline-block transition-all duration-500 uppercase tracking-[0.3em] text-xs font-black">
            ← Back to home
          </a>
        </div>
      </section>
    </main>
  );
}
