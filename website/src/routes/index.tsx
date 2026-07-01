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

function BotanicalArt({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 200 200" className={className} xmlns="http://www.w3.org/2000/svg">
      <path 
        d="M100,180 Q80,120 100,40 Q120,120 100,180" 
        fill="none" 
        stroke="currentColor" 
        strokeWidth="1" 
        opacity="0.6"
      />
      <path 
        d="M100,140 Q60,110 40,80 Q90,90 100,140" 
        fill="currentColor" 
        opacity="0.2"
      />
      <path 
        d="M100,120 Q140,90 160,60 Q110,70 100,120" 
        fill="currentColor" 
        opacity="0.2"
      />
      <circle cx="100" cy="40" r="3" fill="currentColor" opacity="0.4" />
    </svg>
  );
}

function MoonIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
    </svg>
  );
}

function Home() {
  const businessName = Route.useLoaderData();
  
  const strategies = [
    {
      name: "Momentum Protocol",
      description: "Observing the natural ebb and flow of market energy with quiet precision.",
      id: "α",
      color: "text-[#e8a5a5]",
      bg: "bg-[#fdf2f2]",
      shape: "organic-shape-1"
    },
    {
      name: "Relative Strength",
      description: "Identifying the resilient blooms that thrive amidst shifting market seasons.",
      id: "β",
      color: "text-[#a8b08e]",
      bg: "bg-[#f2f4e8]",
      shape: "organic-shape-2"
    },
    {
      name: "Cross-Asset Intelligence",
      description: "Understanding the interconnected roots that bind global digital assets.",
      id: "γ",
      color: "text-[#d6b5ff]",
      bg: "bg-[#f5f0ff]",
      shape: "organic-shape-1"
    },
    {
      name: "Sentiment & Flow",
      description: "Tuning into the collective whisper of the crowd to find hidden paths.",
      id: "δ",
      color: "text-[#f5d0d0]",
      bg: "bg-[#fffafa]",
      shape: "organic-shape-2"
    },
    {
      name: "Macro Regime Analysis",
      description: "Aligning our movement with the grand cycles of the financial environment.",
      id: "ε",
      color: "text-[#b8a5b8]",
      bg: "bg-[#f8f2f8]",
      shape: "organic-shape-1"
    }
  ];

  return (
    <main className="relative min-h-dvh overflow-hidden bg-[#faf7f2] dark:bg-[#1a1c17] selection-botanical pb-32">
      <div className="botanical-pattern absolute inset-0 pointer-events-none opacity-40" />
      
      {/* Layered Decorative Elements */}
      <div className="absolute top-[-10%] -left-[10%] w-[40%] h-[40%] bg-[#f5d0d0] soft-glow rounded-full pointer-events-none animate-drift" />
      <div className="absolute bottom-[-5%] -right-[10%] w-[50%] h-[50%] bg-[#d6b5ff] soft-glow rounded-full pointer-events-none animate-drift" style={{ animationDelay: '-5s' }} />
      <div className="absolute top-[20%] right-[10%] w-[30%] h-[30%] bg-[#a8b08e] soft-glow rounded-full pointer-events-none animate-drift" style={{ animationDelay: '-10s' }} />

      {/* Header Section */}
      <section className="relative flex flex-col items-center pt-32 pb-24 px-6 text-center z-10">
        <div className="mb-16 flex items-center gap-4 text-[#a8b08e]">
           <BotanicalArt className="w-12 h-12 floating-botanical" />
           <div className="h-[1px] w-12 bg-current opacity-30" />
           <span className="text-[10px] tracking-[0.6em] uppercase font-semibold">
             Botanical Intelligence
           </span>
           <div className="h-[1px] w-12 bg-current opacity-30" />
           <MoonIcon className="w-6 h-6 opacity-60" />
        </div>
        
        <h1 className="max-w-4xl text-5xl md:text-8xl font-light tracking-[0.15em] text-[#3d4234] dark:text-[#f2f0e4] mb-12">
          {businessName || "MinuteTrader"}
        </h1>
        
        <div className="w-24 h-[1px] bg-[#c5a059]/30 mx-auto mb-12" />
        
        <p className="max-w-2xl text-2xl font-botanical italic text-[#636b51] dark:text-[#a8b08e] leading-relaxed">
          "A serene sanctuary for high-precision market observation. <br/>
          Monitoring the digital garden with patient wisdom."
        </p>

        <div className="mt-20 inline-flex items-center gap-6 px-10 py-4 rounded-full border border-[#d6cec2] text-[#636b51] dark:text-[#e4e9d6] text-xs tracking-[0.3em] font-medium bg-white/40 backdrop-blur-xl shadow-sm">
          <div className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#e8a5a5] opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-[#e8a5a5]"></span>
          </div>
          Gardening in Progress
        </div>
      </section>

      {/* Organic Strategy Layout */}
      <section className="max-w-7xl mx-auto px-6 py-12 relative z-10">
        <div className="flex flex-wrap justify-center gap-12 lg:gap-20">
          {strategies.map((s, i) => (
            <div 
              key={i} 
              className={`organic-card w-full md:w-[45%] lg:w-[30%] ${s.shape} group hover:-translate-y-2 transition-all duration-700`}
              style={{ marginTop: i % 2 === 1 ? '4rem' : '0' }}
            >
              <div className="flex justify-between items-start mb-10">
                <span className={`font-botanical italic text-3xl ${s.color} opacity-60`}>{s.id}</span>
                <BotanicalArt className={`w-8 h-8 ${s.color} opacity-40 group-hover:opacity-80 transition-opacity`} />
              </div>
              <h3 className="text-2xl font-light text-[#3d4234] dark:text-[#f2f0e4] mb-6 tracking-wider">
                {s.name}
              </h3>
              <p className="text-[#636b51] dark:text-[#a8b08e] leading-relaxed text-base font-light italic font-botanical">
                {s.description}
              </p>
            </div>
          ))}
          
          {/* Large Abstract Motif */}
          <div className="hidden lg:flex w-full justify-end pr-20 -mt-20 opacity-10">
             <BotanicalArt className="w-64 h-64 rotate-45" />
          </div>
        </div>
      </section>

      {/* Philosophy Section */}
      <section className="mt-40 px-6 relative z-10">
        <div className="max-w-5xl mx-auto rounded-[4rem] bg-[#3d4234] dark:bg-[#11130e] text-[#faf7f2] p-20 md:p-32 text-center shadow-2xl overflow-hidden relative">
          {/* Background SVGs */}
          <BotanicalArt className="absolute top-0 left-0 w-96 h-96 -translate-x-1/2 -translate-y-1/2 opacity-5 text-white" />
          <BotanicalArt className="absolute bottom-0 right-0 w-96 h-96 translate-x-1/2 translate-y-1/2 opacity-5 text-white" />
          
          <div className="relative z-10">
            <h2 className="text-4xl md:text-5xl font-light mb-12 tracking-[0.2em] uppercase">Deep Rooted Precision</h2>
            <div className="w-16 h-[1px] bg-[#a8b08e]/40 mx-auto mb-12" />
            <p className="text-[#a8b08e] text-xl font-light leading-relaxed max-w-3xl mx-auto font-botanical italic">
              Our core architecture is complete, yet we allow it time to settle. Currently undergoing rigorous walk-forward validation and stress testing to ensure absolute reliability in the ever-changing market climate.
            </p>
            <div className="mt-20 inline-block px-12 py-5 rounded-full border border-[#a8b08e]/30 text-[#a8b08e] uppercase tracking-[0.4em] text-[10px] font-semibold hover:bg-white/5 transition-all cursor-default backdrop-blur-sm">
              Proprietary Archives Restricted
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="pt-40 px-6 text-center">
        <div className="flex flex-col items-center gap-10">
          <div className="flex gap-8">
            <BotanicalArt className="w-6 h-6 text-[#a8b08e] opacity-30" />
            <MoonIcon className="w-6 h-6 text-[#a8b08e] opacity-30" />
            <BotanicalArt className="w-6 h-6 text-[#a8b08e] opacity-30 rotate-180" />
          </div>
          <div className="flex flex-col items-center gap-3 text-[#a8b08e] uppercase tracking-[0.6em] text-[9px] font-bold">
            <span>Cultivated with Intent</span>
            <a href="https://cto.new" className="text-[#3d4234] dark:text-[#f2f0e4] hover:text-[#e8a5a5] transition-colors">
              cto.new
            </a>
          </div>
        </div>
      </footer>
    </main>
  );
}
