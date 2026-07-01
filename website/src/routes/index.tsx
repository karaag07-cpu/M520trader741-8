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
      name: "Momentum Analysis",
      description: "Harnessing directional velocity through high-fidelity volume confirmation and trend alignment.",
      id: "01"
    },
    {
      name: "Relative Strength",
      description: "Discerning superior asset performance by benchmarking against global liquidity indices.",
      id: "02"
    },
    {
      name: "Cross-Asset Intelligence",
      description: "Interpreting subtle lead-lag relationships within the complex tapestry of global markets.",
      id: "03"
    },
    {
      name: "Sentiment & Flow",
      description: "Quantifying collective psychology to exploit contrarian opportunities in capital movement.",
      id: "04"
    },
    {
      name: "Macro Regime Detection",
      description: "Aligning execution with the prevailing economic narrative and central bank policy cycles.",
      id: "05"
    }
  ];

  return (
    <main className="relative min-h-dvh overflow-hidden bg-[#fdfbf7] dark:bg-[#0c0a09] selection:bg-[#c5a059] selection:text-white">
      <div className="vintage-overlay" />
      
      {/* Header Section */}
      <section className="relative flex flex-col items-center pt-24 pb-16 px-6 text-center border-b border-[#c5a059]/20">
        <div className="mb-8 flex items-center gap-4">
          <div className="h-px w-12 bg-[#c5a059]" />
          <span className="text-[#c5a059] tracking-[0.3em] uppercase text-xs font-bold">
            Established MMXXVI
          </span>
          <div className="h-px w-12 bg-[#c5a059]" />
        </div>
        
        <h1 className="max-w-4xl text-6xl md:text-8xl font-normal tracking-tight text-[#1c1917] dark:text-[#f5f5f4] mb-8">
          {businessName || "MinuteTrader"}
        </h1>
        
        <div className="gold-divider" />
        
        <p className="max-w-2xl text-xl italic text-stone-600 dark:text-stone-400 font-serif leading-relaxed">
          "A sophisticated automated pursuit of micro-inefficiencies across the digital and traditional frontiers."
        </p>

        <div className="mt-12 inline-flex items-center gap-3 px-6 py-2 border border-[#c5a059] text-[#c5a059] uppercase tracking-widest text-xs font-bold bg-[#c5a059]/5">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#c5a059] opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-[#c5a059]"></span>
          </span>
          Operational Backtesting in Progress
        </div>
      </section>

      {/* Strategies Section */}
      <section className="max-w-6xl mx-auto px-6 py-24">
        <div className="flex flex-col items-center mb-16 ornate-border">
          <h2 className="text-3xl md:text-4xl font-normal text-[#1c1917] dark:text-[#f5f5f4] uppercase tracking-[0.2em]">
            Core Methodologies
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-12">
          {strategies.map((s, i) => (
            <div key={i} className="gilded-card group">
              <span className="text-[#c5a059]/40 font-serif text-4xl italic absolute top-4 right-6 group-hover:text-[#c5a059] transition-colors duration-500">
                {s.id}
              </span>
              <h3 className="text-2xl mb-6 text-[#1c1917] dark:text-[#f5f5f4] border-b border-[#c5a059]/20 pb-4 pr-12">
                {s.name}
              </h3>
              <p className="text-stone-600 dark:text-stone-400 leading-relaxed italic text-lg">
                {s.description}
              </p>
            </div>
          ))}
          
          {/* Decorative sixth card to balance grid */}
          <div className="hidden lg:flex border-2 border-dashed border-[#c5a059]/20 items-center justify-center p-8 opacity-40">
            <div className="text-[#c5a059] text-6xl">◈</div>
          </div>
        </div>
      </section>

      {/* Status Section */}
      <section className="bg-[#1c1917] text-[#fdfbf7] py-24 px-6 text-center relative overflow-hidden">
        <div className="absolute inset-0 opacity-10 pointer-events-none" 
             style={{backgroundImage: 'radial-gradient(circle at 50% 50%, #c5a059 0%, transparent 70%)'}}></div>
        
        <div className="max-w-3xl mx-auto relative z-10">
          <h2 className="text-4xl md:text-5xl font-normal mb-8 tracking-wide">Awaiting Market Alignment</h2>
          <div className="w-16 h-px bg-[#c5a059] mx-auto mb-8" />
          <p className="text-stone-400 text-xl font-serif leading-relaxed mb-12">
            The core algorithmic architecture is complete. Currently undergoing rigorous walk-forward validation and stress testing to ensure absolute precision upon deployment.
          </p>
          <div className="inline-block px-8 py-4 border-2 border-[#c5a059] text-[#c5a059] uppercase tracking-widest text-sm font-bold hover:bg-[#c5a059] hover:text-[#1c1917] transition-all duration-500 cursor-default">
            Proprietary Restricted Access
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-16 px-6 text-center border-t border-[#c5a059]/10 bg-[#fdfbf7] dark:bg-[#0c0a09]">
        <div className="flex flex-col items-center gap-4 text-stone-500 dark:text-stone-600 uppercase tracking-[0.4em] text-[10px] font-bold">
          <span>Curated with Precision</span>
          <a href="https://cto.new" className="text-[#c5a059] hover:text-[#1c1917] dark:hover:text-[#f5f5f4] transition-colors decoration-none">
            cto.new
          </a>
        </div>
      </footer>
    </main>
  );
}
