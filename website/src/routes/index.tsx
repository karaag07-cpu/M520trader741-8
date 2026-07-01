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

function FlowerIcon({ src, className }: { src: string; className?: string }) {
  return <img src={src} className={className} alt="Flower accent" />;
}

function MoonIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
    </svg>
  );
}

function Home() {
  const businessName = Route.useLoaderData();
  
  const strategies = [
    {
      name: "Momentum Protocol",
      description: "Harnessing the vital energy of market cycles with vivid precision.",
      id: "α",
      color: "text-rose-bold",
      borderColor: "border-rose",
      flower: "/flower-rose.svg",
      shape: "organic-shape-1",
      offset: "md:translate-y-12"
    },
    {
      name: "Relative Strength",
      description: "Spotting the most vibrant blooms in the digital market landscape.",
      id: "β",
      color: "text-sage-bold",
      borderColor: "border-sage",
      flower: "/flower-sage.svg",
      shape: "organic-shape-2",
      offset: "md:-translate-y-8"
    },
    {
      name: "Cross-Asset Intelligence",
      description: "Mapping the deep roots that connect every asset in our ecosystem.",
      id: "γ",
      color: "text-lavender-bold",
      borderColor: "border-lavender",
      flower: "/flower-lavender.svg",
      shape: "organic-shape-1",
      offset: "md:translate-y-24"
    },
    {
      name: "Sentiment & Flow",
      description: "Feeling the breeze of public opinion to navigate hidden currents.",
      id: "δ",
      color: "text-rose-bold",
      borderColor: "border-blush",
      flower: "/flower-wildflower.svg",
      shape: "organic-shape-2",
      offset: "md:translate-x-12"
    },
    {
      name: "Macro Regime Analysis",
      description: "Aligning with the grand seasonal shifts of the global economy.",
      id: "ε",
      color: "text-lavender-bold",
      borderColor: "border-lavender",
      flower: "/flower-rose.svg",
      shape: "organic-shape-1",
      offset: "md:-translate-x-8 md:translate-y-12"
    }
  ];

  return (
    <main className="relative min-h-dvh overflow-hidden bg-[#faf7f2] dark:bg-[#1a1c17] selection-botanical pb-32">
      <div className="botanical-pattern absolute inset-0 pointer-events-none opacity-40" />
      
      {/* Background Floral Art - Bolder */}
      <FlowerIcon src="/flower-rose.svg" className="absolute -top-20 -right-20 w-[40%] opacity-20 pointer-events-none rotate-12" />
      <FlowerIcon src="/flower-sage.svg" className="absolute -bottom-20 -left-20 w-[40%] opacity-20 pointer-events-none -rotate-12" />
      <FlowerIcon src="/flower-lavender.svg" className="absolute top-[40%] left-[-10%] w-[30%] opacity-15 pointer-events-none" />

      {/* Saturated Soft Glows */}
      <div className="absolute top-[-10%] -left-[10%] w-[40%] h-[40%] bg-[#e8a5a5] soft-glow rounded-full pointer-events-none animate-drift" />
      <div className="absolute bottom-[-5%] -right-[10%] w-[50%] h-[50%] bg-[#d6b5ff] soft-glow rounded-full pointer-events-none animate-drift" style={{ animationDelay: '-5s' }} />
      <div className="absolute top-[20%] right-[10%] w-[30%] h-[30%] bg-[#a8b08e] soft-glow rounded-full pointer-events-none animate-drift" style={{ animationDelay: '-10s' }} />

      {/* Header Section */}
      <header className="relative z-20 pt-12 px-6 flex justify-center">
        <div className="flex items-center gap-4 text-sage-bold">
          <FlowerIcon src="/flower-rose.svg" className="w-8 h-8" />
          <span className="text-xs tracking-[0.6em] font-bold uppercase">Floral Analytics</span>
          <FlowerIcon src="/flower-lavender.svg" className="w-8 h-8" />
        </div>
      </header>

      <section className="relative flex flex-col items-center pt-24 pb-32 px-6 text-center z-10">
        <div className="mb-16 flex items-center gap-6 text-rose-bold">
           <MoonIcon className="w-8 h-8 -rotate-12" />
           <div className="h-[2px] w-24 bg-current opacity-40" />
           <span className="text-[11px] tracking-[1em] uppercase font-bold">
             The Botanical Observatory
           </span>
           <div className="h-[2px] w-24 bg-current opacity-40" />
           <MoonIcon className="w-8 h-8 rotate-12" />
        </div>
        
        <h1 className="max-w-5xl text-7xl md:text-9xl font-light tracking-[0.05em] text-[#3d4234] dark:text-[#f2f0e4] mb-12">
          {businessName || "MinuteTrader"}
        </h1>
        
        <p className="max-w-3xl text-3xl md:text-4xl font-botanical italic text-sage-bold leading-relaxed mb-20 px-4">
          Nurturing digital assets <br className="hidden md:block" /> 
          with the precision of a master gardener.
        </p>

        <div className="inline-flex items-center gap-8 px-14 py-6 rounded-full border-2 border-rose text-rose-bold text-[12px] tracking-[0.5em] font-bold bg-white/60 backdrop-blur-3xl shadow-xl uppercase">
          <div className="relative flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-bold opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-rose-bold"></span>
          </div>
          Vibrant Growth Active
        </div>
      </section>

      {/* Anti-Grid Strategy Layout with Bold Flowers */}
      <section className="max-w-[1400px] mx-auto px-6 py-20 relative z-10">
        <div className="relative min-h-[1000px] md:min-h-[1400px]">
          {strategies.map((s, i) => (
            <div 
              key={i} 
              className={`organic-card absolute group hover:-translate-y-6 transition-all duration-1000 ${s.shape} ${s.offset} ${s.borderColor}`}
              style={{ 
                width: 'clamp(320px, 35vw, 480px)',
                top: `${(i % 3) * 35}%`,
                left: i < 3 ? `${i * 32}%` : `${(i - 3) * 45 + 10}%`,
                zIndex: 10 + i
              }}
            >
              {/* Floral Corner Accent */}
              <FlowerIcon src={s.flower} className="flower-accent -top-12 -right-12 w-32 h-32" />
              
              <div className="flex justify-between items-start mb-12 relative z-10">
                <span className={`font-botanical italic text-5xl ${s.color}`}>{s.id}</span>
                <MoonIcon className={`w-6 h-6 ${s.color} opacity-60 group-hover:opacity-100 transition-opacity duration-700`} />
              </div>
              
              <h3 className="text-4xl font-light text-[#3d4234] dark:text-[#f2f0e4] mb-8 tracking-widest relative z-10">
                {s.name}
              </h3>
              
              <p className="text-[#636b51] dark:text-[#a8b08e] leading-relaxed text-xl font-light italic font-botanical relative z-10">
                {s.description}
              </p>
            </div>
          ))}
          
          {/* Central Decorative Elements */}
          <div className="hidden lg:block absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] border-4 border-sage-soft rounded-full pointer-events-none" />
          <div className="hidden lg:block absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] border-2 border-rose-soft rounded-full pointer-events-none" />
          <FlowerIcon src="/flower-wildflower.svg" className="hidden lg:block absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 opacity-20" />
        </div>
      </section>

      {/* Vibrant Atmosphere Section */}
      <section className="mt-80 px-6 relative z-10">
        <div className="max-w-6xl mx-auto rounded-[6rem] bg-rose-bold text-[#faf7f2] p-24 md:p-40 text-center shadow-[0_60px_120px_-30px_rgba(214,133,133,0.5)] overflow-hidden relative">
          <div className="absolute inset-0 botanical-pattern opacity-20" />
          <FlowerIcon src="/flower-rose.svg" className="absolute top-0 right-0 w-[50%] h-[50%] opacity-20 -translate-y-1/3 translate-x-1/3 rotate-45" />
          <FlowerIcon src="/flower-lavender.svg" className="absolute bottom-0 left-0 w-[40%] h-[40%] opacity-20 translate-y-1/4 -translate-x-1/4 -rotate-12" />
          
          <div className="relative z-10">
            <h2 className="text-5xl md:text-8xl font-light mb-16 tracking-[0.2em] uppercase">Vibrant Precision</h2>
            <div className="w-48 h-[2px] bg-white opacity-40 mx-auto mb-16" />
            <p className="text-white text-3xl font-light leading-relaxed max-w-4xl mx-auto font-botanical italic">
              "We embrace the bold vitality of the markets. Our algorithms don't just survive; they bloom. Every trade is a carefully cultivated moment of growth in our digital garden."
            </p>
            <div className="mt-24 inline-block px-16 py-8 rounded-full border-2 border-white/40 text-white uppercase tracking-[0.6em] text-[12px] font-bold hover:bg-white/10 transition-all duration-700 cursor-default backdrop-blur-md">
              Secure Garden Portal
            </div>
          </div>
        </div>
      </section>

      {/* Footer with Floral Header */}
      <footer className="pt-80 pb-20 px-6 text-center relative">
        <div className="absolute top-40 left-1/2 -translate-x-1/2 w-full flex justify-center gap-12 opacity-40">
           <FlowerIcon src="/flower-rose.svg" className="w-24 h-24" />
           <FlowerIcon src="/flower-lavender.svg" className="w-24 h-24" />
           <FlowerIcon src="/flower-sage.svg" className="w-24 h-24" />
        </div>
        
        <div className="flex flex-col items-center gap-12 relative z-10">
          <div className="flex gap-16 text-rose-bold">
            <MoonIcon className="w-10 h-10" />
            <FlowerIcon src="/flower-wildflower.svg" className="w-10 h-10" />
            <MoonIcon className="w-10 h-10 rotate-180" />
          </div>
          <div className="flex flex-col items-center gap-6 text-sage-bold uppercase tracking-[1em] text-[12px] font-bold">
            <span>Cultivated with Passion</span>
            <a href="https://cto.new" className="text-rose-bold hover:text-rose-bold/80 transition-all duration-500 scale-125">
              cto.new
            </a>
          </div>
        </div>
      </footer>
    </main>
  );
}
