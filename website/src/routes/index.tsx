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
      image: "/botanical-0.svg",
      shape: "organic-shape-1",
      offset: "md:translate-y-12"
    },
    {
      name: "Relative Strength",
      description: "Identifying the resilient blooms that thrive amidst shifting market seasons.",
      id: "β",
      color: "text-[#a8b08e]",
      image: "/botanical-1.svg",
      shape: "organic-shape-2",
      offset: "md:-translate-y-8"
    },
    {
      name: "Cross-Asset Intelligence",
      description: "Understanding the interconnected roots that bind global digital assets.",
      id: "γ",
      color: "text-[#d6b5ff]",
      image: "/botanical-2.svg",
      shape: "organic-shape-1",
      offset: "md:translate-y-24"
    },
    {
      name: "Sentiment & Flow",
      description: "Tuning into the collective whisper of the crowd to find hidden paths.",
      id: "δ",
      color: "text-[#f5d0d0]",
      image: "/botanical-0.svg",
      shape: "organic-shape-2",
      offset: "md:translate-x-12"
    },
    {
      name: "Macro Regime Analysis",
      description: "Aligning our movement with the grand cycles of the financial environment.",
      id: "ε",
      color: "text-[#b8a5b8]",
      image: "/botanical-1.svg",
      shape: "organic-shape-1",
      offset: "md:-translate-x-8 md:translate-y-12"
    }
  ];

  return (
    <main className="relative min-h-dvh overflow-hidden bg-[#faf7f2] dark:bg-[#1a1c17] selection-botanical pb-32">
      <div className="botanical-pattern absolute inset-0 pointer-events-none opacity-30" />
      
      {/* Background Flowing Art */}
      <img src="/botanical-2.svg" className="absolute top-0 right-0 w-[60%] opacity-10 pointer-events-none" />
      <img src="/botanical-1.svg" className="absolute bottom-0 left-0 w-[50%] opacity-10 pointer-events-none rotate-180" />

      {/* Layered Soft Glows */}
      <div className="absolute top-[-10%] -left-[10%] w-[40%] h-[40%] bg-[#f5d0d0] soft-glow rounded-full pointer-events-none animate-drift" />
      <div className="absolute bottom-[-5%] -right-[10%] w-[50%] h-[50%] bg-[#d6b5ff] soft-glow rounded-full pointer-events-none animate-drift" style={{ animationDelay: '-5s' }} />
      <div className="absolute top-[20%] right-[10%] w-[30%] h-[30%] bg-[#a8b08e] soft-glow rounded-full pointer-events-none animate-drift" style={{ animationDelay: '-10s' }} />

      {/* Header Section */}
      <section className="relative flex flex-col items-center pt-32 pb-32 px-6 text-center z-10">
        <div className="mb-20 flex items-center gap-6 text-[#a8b08e]">
           <MoonIcon className="w-6 h-6 opacity-40 -rotate-12" />
           <div className="h-[1px] w-16 bg-current opacity-20" />
           <span className="text-[9px] tracking-[0.8em] uppercase font-bold text-[#636b51]">
             The Botanical Observatory
           </span>
           <div className="h-[1px] w-16 bg-current opacity-20" />
           <MoonIcon className="w-6 h-6 opacity-40 rotate-12" />
        </div>
        
        <h1 className="max-w-5xl text-6xl md:text-9xl font-light tracking-[0.1em] text-[#3d4234] dark:text-[#f2f0e4] mb-12">
          {businessName || "MinuteTrader"}
        </h1>
        
        <p className="max-w-3xl text-2xl md:text-3xl font-botanical italic text-[#636b51] dark:text-[#a8b08e] leading-relaxed mb-20 px-4">
          Watching the digital garden <br className="hidden md:block" /> 
          where precision meets organic growth.
        </p>

        <div className="inline-flex items-center gap-8 px-12 py-5 rounded-full border border-[#d6cec2] text-[#636b51] dark:text-[#e4e9d6] text-[10px] tracking-[0.4em] font-bold bg-white/30 backdrop-blur-2xl shadow-sm uppercase">
          <div className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#e8a5a5] opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-[#e8a5a5]"></span>
          </div>
          Nurturing Algorithms
        </div>
      </section>

      {/* Anti-Grid Strategy Layout */}
      <section className="max-w-[1400px] mx-auto px-6 py-20 relative z-10">
        <div className="relative min-h-[800px] md:min-h-[1200px]">
          {strategies.map((s, i) => (
            <div 
              key={i} 
              className={`organic-card absolute group hover:-translate-y-4 transition-all duration-1000 ${s.shape} ${s.offset}`}
              style={{ 
                width: 'clamp(300px, 30vw, 450px)',
                top: `${(i % 3) * 30}%`,
                left: i < 3 ? `${i * 30}%` : `${(i - 3) * 40 + 15}%`,
                zIndex: 10 + i
              }}
            >
              <img src={s.image} className="absolute inset-0 w-full h-full object-cover opacity-5 pointer-events-none scale-150" />
              
              <div className="flex justify-between items-start mb-12 relative z-10">
                <span className={`font-botanical italic text-4xl ${s.color} opacity-80`}>{s.id}</span>
                <MoonIcon className={`w-5 h-5 ${s.color} opacity-30 group-hover:opacity-100 transition-opacity duration-1000`} />
              </div>
              
              <h3 className="text-3xl font-light text-[#3d4234] dark:text-[#f2f0e4] mb-8 tracking-widest relative z-10">
                {s.name}
              </h3>
              
              <p className="text-[#636b51] dark:text-[#a8b08e] leading-relaxed text-lg font-light italic font-botanical relative z-10">
                {s.description}
              </p>
            </div>
          ))}
          
          {/* Central Decorative Arches */}
          <div className="hidden lg:block absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] border border-[#a8b08e]/10 rounded-full pointer-events-none" />
          <div className="hidden lg:block absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] border border-[#a8b08e]/5 rounded-full pointer-events-none" />
        </div>
      </section>

      {/* Atmosphere Section */}
      <section className="mt-60 px-6 relative z-10">
        <div className="max-w-6xl mx-auto rounded-[5rem] bg-[#3d4234] dark:bg-[#11130e] text-[#faf7f2] p-24 md:p-40 text-center shadow-[0_50px_100px_-20px_rgba(0,0,0,0.4)] overflow-hidden relative">
          <div className="absolute inset-0 botanical-pattern opacity-10" />
          <img src="/botanical-2.svg" className="absolute top-0 right-0 w-96 h-96 opacity-10 -translate-y-1/2 translate-x-1/2" />
          
          <div className="relative z-10">
            <h2 className="text-4xl md:text-6xl font-light mb-16 tracking-[0.3em] uppercase">The Art of Wait</h2>
            <div className="w-32 h-[1px] bg-[#a8b08e]/40 mx-auto mb-16" />
            <p className="text-[#a8b08e] text-2xl font-light leading-relaxed max-w-4xl mx-auto font-botanical italic">
              "We do not chase the market; we wait for it to reveal its patterns, like a bloom opening to the morning sun. Our architecture is complete, yet we grant it the grace of refinement through rigorous validation."
            </p>
            <div className="mt-24 inline-block px-14 py-6 rounded-full border border-[#a8b08e]/30 text-[#a8b08e] uppercase tracking-[0.5em] text-[10px] font-bold hover:bg-white/5 transition-all duration-700 cursor-default backdrop-blur-md">
              Restricted Archive Access
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="pt-60 pb-20 px-6 text-center">
        <div className="flex flex-col items-center gap-12">
          <div className="flex gap-12 text-[#a8b08e] opacity-40">
            <BotanicalArt className="w-8 h-8" />
            <MoonIcon className="w-8 h-8" />
            <BotanicalArt className="w-8 h-8 rotate-180" />
          </div>
          <div className="flex flex-col items-center gap-4 text-[#a8b08e] uppercase tracking-[0.8em] text-[10px] font-bold">
            <span>Curated with Serenity</span>
            <a href="https://cto.new" className="text-[#3d4234] dark:text-[#f2f0e4] hover:text-[#e8a5a5] transition-all duration-500">
              cto.new
            </a>
          </div>
        </div>
      </footer>
    </main>
  );
}
