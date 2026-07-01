import { createFileRoute } from "@tanstack/react-router";
import { createServerFn } from "@tanstack/react-start";
import { readFile } from "node:fs/promises";

const getBusinessName = createServerFn({ method: "GET" }).handler(async () => {
  try {
    const cfg = JSON.parse(await readFile("site.json", "utf8")) as {
      businessName?: string;
    };
    return cfg.businessName?.trim() ?? "";
  } catch {
    return "";
  }
});

export const Route = createFileRoute("/")({
  loader: () => getBusinessName(),
  component: Home,
});

function Home() {
  const businessName = Route.useLoaderData();
  
  const strategies = [
    {
      name: "Momentum Protocol",
      description: "A calculated observation of directional force, identified through volume patterns and trend stability.",
      id: "α-1",
      accent: "bg-[#d6b5ff]/10"
    },
    {
      name: "Relative Strength",
      description: "Discerning exceptional asset performance by indexing against global liquidity benchmarks.",
      id: "β-2",
      accent: "bg-[#ffb5d8]/10"
    },
    {
      name: "Cross-Asset Intelligence",
      description: "Interpreting the subtle lead-lag dependencies within the global financial infrastructure.",
      id: "γ-3",
      accent: "bg-[#b5ffed]/10"
    },
    {
      name: "Sentiment & Flow",
      description: "Quantifying collective behavior to identify structural opportunities in capital migration.",
      id: "δ-4",
      accent: "bg-[#e2ffb5]/10"
    },
    {
      name: "Macro Regime Analysis",
      description: "Aligning tactical execution with the broader economic narrative and policy cycles.",
      id: "ε-5",
      accent: "bg-[#ffd8b5]/10"
    }
  ];

  return (
    <main className="relative min-h-dvh overflow-hidden bg-[#f2f0e4] dark:bg-[#1a1c17] selection-60s pb-20">
      <div className="line-art-bg" />
      
      {/* 60s Style Header Section */}
      <section className="relative flex flex-col items-center pt-32 pb-12 px-6 text-center">
        <div className="mb-12 flex items-center gap-6">
          <div className="h-[1px] w-16 bg-[#3d4234]/20" />
          <span className="text-[#a8b08e] tracking-[0.4em] uppercase text-[10px] font-medium">
            System Status: Monitoring
          </span>
          <div className="h-[1px] w-16 bg-[#3d4234]/20" />
        </div>
        
        <h1 className="max-w-4xl text-5xl md:text-7xl font-light tracking-widest text-[#3d4234] dark:text-[#e4e9d6] mb-8">
          {businessName || "MinuteTrader"}
        </h1>
        
        <div className="muted-gold-divider" />
        
        <p className="max-w-2xl text-xl text-[#636b51] dark:text-[#a8b08e] font-light leading-relaxed">
          The intelligent assistant for micro-inefficiency detection. <br/>
          Steady. Precise. Confident.
        </p>

        <div className="mt-16 inline-flex items-center gap-4 px-8 py-3 rounded-full border border-[#a8b08e]/30 text-[#3d4234] dark:text-[#e4e9d6] text-xs tracking-[0.2em] font-medium bg-white/20 backdrop-blur-md">
          <div className="flex gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-[#a8b08e] animate-pulse" />
            <span className="w-1.5 h-1.5 rounded-full bg-[#a8b08e]/40" />
            <span className="w-1.5 h-1.5 rounded-full bg-[#a8b08e]/20" />
          </div>
          Systems Calibration in Progress
        </div>
      </section>

      {/* Modernist Line Art Placeholder */}
      <div className="max-w-4xl mx-auto h-24 flex items-center justify-center opacity-20 pointer-events-none mb-12">
        <svg viewBox="0 0 400 100" className="w-full h-full text-[#a8b08e]">
          <path d="M0,50 Q50,20 100,50 T200,50 T300,50 T400,50" fill="none" stroke="currentColor" strokeWidth="0.5" />
          <circle cx="100" cy="50" r="2" fill="currentColor" />
          <circle cx="200" cy="50" r="2" fill="currentColor" />
          <circle cx="300" cy="50" r="2" fill="currentColor" />
        </svg>
      </div>

      {/* Strategies Section - Pillowy Cards */}
      <section className="max-w-6xl mx-auto px-6 py-12 relative z-10">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-10">
          {strategies.map((s, i) => (
            <div key={i} className={`pillowy-card group ${s.accent}`}>
              <div className="flex justify-between items-start mb-8">
                <span className="text-[#a8b08e] font-medium text-xs tracking-widest">{s.id}</span>
                <div className="w-6 h-6 rounded-full border border-[#a8b08e]/30 flex items-center justify-center group-hover:bg-[#a8b08e]/10 transition-colors">
                  <div className="w-1 h-1 rounded-full bg-[#a8b08e]" />
                </div>
              </div>
              <h3 className="text-xl font-normal text-[#3d4234] dark:text-[#e4e9d6] mb-4">
                {s.name}
              </h3>
              <p className="text-[#636b51] dark:text-[#a8b08e] leading-relaxed text-sm font-light">
                {s.description}
              </p>
            </div>
          ))}
          
          {/* Decorative Command Center Terminal */}
          <div className="pillowy-card bg-[#3d4234]/5 border-dashed border-[#a8b08e]/40 flex flex-col justify-center items-center p-8 gap-4">
            <div className="grid grid-cols-3 gap-2 opacity-30">
               {[...Array(9)].map((_, i) => (
                 <div key={i} className="w-2 h-2 rounded-full bg-[#a8b08e]" />
               ))}
            </div>
            <span className="text-[10px] text-[#a8b08e] tracking-widest font-medium uppercase">Mission Control</span>
          </div>
        </div>
      </section>

      {/* Lower Banner Section */}
      <section className="mt-24 max-w-4xl mx-auto px-6">
        <div className="rounded-[3rem] bg-[#3d4234] dark:bg-[#11130e] text-[#f2f0e4] p-16 text-center shadow-2xl relative overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-white/5 rounded-full -mr-32 -mt-32" />
          <h2 className="text-3xl font-light mb-8 tracking-widest uppercase">Precision Verification</h2>
          <div className="w-12 h-[1px] bg-[#a8b08e]/40 mx-auto mb-10" />
          <p className="text-[#a8b08e] text-lg font-light leading-relaxed max-w-2xl mx-auto">
            The core architecture is finalized. Currently undergoing rigorous walk-forward validation and stress testing to ensure absolute reliability in diverse market conditions.
          </p>
          <div className="mt-12 inline-block px-10 py-4 rounded-full border border-[#a8b08e]/30 text-[#a8b08e] uppercase tracking-[0.3em] text-[10px] font-medium hover:bg-white/5 transition-all cursor-default">
            Restricted Analytical Access
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="pt-24 px-6 text-center">
        <div className="flex flex-col items-center gap-6">
          <div className="muted-gold-divider mb-0" />
          <div className="flex flex-col items-center gap-2 text-[#a8b08e] uppercase tracking-[0.5em] text-[9px] font-semibold">
            <span>Calibrated with Competence</span>
            <a href="https://cto.new" className="text-[#3d4234] dark:text-[#e4e9d6] hover:opacity-70 transition-opacity">
              cto.new
            </a>
          </div>
        </div>
      </footer>
    </main>
  );
}
