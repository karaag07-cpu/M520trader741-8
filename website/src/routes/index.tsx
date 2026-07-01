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
    <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="2.5">
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
      offset: "md:translate-y-12",
      desktopStyle: { top: "5%", left: "5%" }
    },
    {
      name: "Relative Strength",
      description: "Spotting the most vibrant blooms in the digital market landscape.",
      id: "β",
      color: "text-sage-bold",
      borderColor: "border-sage",
      flower: "/flower-sage.svg",
      shape: "organic-shape-2",
      offset: "md:-translate-y-8",
      desktopStyle: { top: "35%", left: "35%" }
    },
    {
      name: "Cross-Asset Intelligence",
      description: "Mapping the deep roots that connect every asset in our ecosystem.",
      id: "γ",
      color: "text-lavender-bold",
      borderColor: "border-lavender",
      flower: "/flower-lavender.svg",
      shape: "organic-shape-1",
      offset: "md:translate-y-24",
      desktopStyle: { top: "65%", left: "60%" }
    },
    {
      name: "Sentiment & Flow",
      description: "Feeling the breeze of public opinion to navigate hidden currents.",
      id: "δ",
      color: "text-rose-bold",
      borderColor: "border-blush",
      flower: "/flower-wildflower.svg",
      shape: "organic-shape-2",
      offset: "md:translate-x-12",
      desktopStyle: { top: "10%", left: "55%" }
    },
    {
      name: "Macro Regime Analysis",
      description: "Aligning with the grand seasonal shifts of the global economy.",
      id: "ε",
      color: "text-lavender-bold",
      borderColor: "border-lavender",
      flower: "/flower-rose.svg",
      shape: "organic-shape-1",
      offset: "md:-translate-x-8 md:translate-y-12",
      desktopStyle: { top: "55%", left: "10%" }
    }
  ];

  return (
    <main className="relative min-h-dvh overflow-x-hidden bg-[#faf7f2] dark:bg-[#0d0e0a] selection-botanical pb-32">
      <div className="botanical-pattern absolute inset-0 pointer-events-none opacity-40" />
      
      {/* Background Floral Art */}
      <FlowerIcon src="/flower-rose.svg" className="absolute -top-20 -right-20 w-[60%] md:w-[40%] opacity-20 pointer-events-none rotate-12" />
      <FlowerIcon src="/flower-sage.svg" className="absolute -bottom-20 -left-20 w-[60%] md:w-[40%] opacity-20 pointer-events-none -rotate-12" />
      <FlowerIcon src="/flower-lavender.svg" className="absolute top-[40%] left-[-15%] w-[40%] md:w-[30%] opacity-15 pointer-events-none" />

      {/* Saturated Soft Glows */}
      <div className="absolute top-[-10%] -left-[10%] w-[40%] h-[40%] bg-[#e8a5a5] soft-glow rounded-full pointer-events-none animate-drift" />
      <div className="absolute bottom-[-5%] -right-[10%] w-[50%] h-[50%] bg-[#d6b5ff] soft-glow rounded-full pointer-events-none animate-drift" style={{ animationDelay: '-5s' }} />
      <div className="absolute top-[20%] right-[10%] w-[30%] h-[30%] bg-[#a8b08e] soft-glow rounded-full pointer-events-none animate-drift" style={{ animationDelay: '-10s' }} />

      {/* Header Section */}
      <header className="relative z-20 pt-12 px-6 flex justify-center">
        <div className="flex flex-wrap justify-center items-center gap-4 md:gap-6 text-sage-bold">
          <FlowerIcon src="/flower-rose.svg" className="w-8 h-8 md:w-10 md:h-10" />
          <span className="text-[10px] md:text-sm tracking-[0.4em] md:tracking-[0.6em] font-bold uppercase">Floral Analytics</span>
          <FlowerIcon src="/flower-lavender.svg" className="w-8 h-8 md:w-10 md:h-10" />
        </div>
      </header>

      <section className="relative flex flex-col items-center pt-24 pb-32 px-4 md:px-6 text-center z-10">
        <div className="mb-16 flex flex-wrap justify-center items-center gap-4 md:gap-8 text-rose-bold">
           <MoonIcon className="w-8 h-8 md:w-10 md:h-10 -rotate-12" />
           <div className="hidden sm:block h-[3px] w-16 md:w-32 bg-current" />
           <span className="text-[10px] md:text-[12px] tracking-[0.5em] md:tracking-[1em] uppercase font-black">
             The Botanical Observatory
           </span>
           <div className="hidden sm:block h-[3px] w-16 md:w-32 bg-current" />
           <MoonIcon className="w-8 h-8 md:w-10 md:h-10 rotate-12" />
        </div>
        
        <h1 className="max-w-6xl text-5xl md:text-7xl lg:text-9xl font-bold tracking-tight text-[#1a1c17] dark:text-white mb-12 px-2">
          {businessName || "MinuteTrader"}
        </h1>
        
        <p className="max-w-4xl text-2xl md:text-3xl lg:text-5xl font-botanical italic text-[#1a1c17] dark:text-[#ffffff] leading-tight mb-20 px-4">
          Nurturing digital assets <br className="hidden md:block" /> 
          with the precision of a master gardener.
        </p>

        <div className="inline-flex items-center gap-6 md:gap-10 px-8 md:px-16 py-6 md:py-8 rounded-full border-4 border-rose text-rose-bold text-[10px] md:text-[14px] tracking-[0.3em] md:tracking-[0.5em] font-black bg-white shadow-2xl uppercase">
          <div className="relative flex h-3 w-3 md:h-4 md:w-4">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-bold opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 md:h-4 md:w-4 bg-rose-bold"></span>
          </div>
          Vibrant Growth Active
        </div>
      </section>

      {/* Strategy Layout */}
      <section className="max-w-[1500px] mx-auto px-4 md:px-6 py-20 relative z-10">
        <div className="flex flex-col md:block items-center gap-8 md:gap-0 relative min-h-0 md:min-h-[1400px]">
          {strategies.map((s, i) => (
            <div 
              key={i} 
              className={`organic-card w-full max-w-md md:max-w-none md:absolute group hover:-translate-y-8 transition-all duration-1000 ${s.shape} ${s.offset} ${s.borderColor}`}
              style={{ 
                zIndex: 10 + i,
                // Inlined media query equivalent for desktop absolute positioning
                ...(typeof window !== 'undefined' && window.innerWidth >= 768 ? {
                  top: s.desktopStyle.top,
                  left: s.desktopStyle.left,
                  width: 'min(520px, 35vw)',
                  position: 'absolute'
                } : {})
              }}
            >
              {/* CSS Injection for Desktop positioning to avoid hydration issues */}
              <style dangerouslySetInnerHTML={{ __html: `
                @media (min-width: 768px) {
                  .strategy-card-${i} {
                    top: ${s.desktopStyle.top} !important;
                    left: ${s.desktopStyle.left} !important;
                    width: min(520px, 35vw) !important;
                    position: absolute !important;
                  }
                }
              `}} />
              
              <div className={`w-full flex flex-col items-center justify-center strategy-card-${i}`}>
                {/* Floral Corner Accent */}
                <FlowerIcon src={s.flower} className="flower-accent -top-12 -right-12 md:-top-16 md:-right-16 w-32 h-32 md:w-40 md:h-40 opacity-100" />
                
                <div className="flex justify-center items-center mb-8 md:mb-14 relative z-10 w-full">
                  <span className={`font-botanical italic text-4xl md:text-6xl ${s.color} mr-6`}>{s.id}</span>
                  <MoonIcon className={`w-6 h-6 md:w-8 md:h-8 ${s.color}`} />
                </div>
                
                <h3 className="text-3xl md:text-5xl font-bold text-[#1a1c17] dark:text-white mb-6 md:mb-10 tracking-widest relative z-10 px-4 text-center">
                  {s.name}
                </h3>
                
                <p className="text-[#1a1c17] dark:text-[#ffffff] leading-relaxed text-lg md:text-2xl font-medium italic font-botanical relative z-10 px-6 text-center">
                  {s.description}
                </p>
              </div>
            </div>
          ))}
          
          {/* Central Decorative Elements */}
          <div className="hidden lg:block absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] border-[6px] border-sage-soft rounded-full pointer-events-none" />
          <div className="hidden lg:block absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] border-[3px] border-rose-soft rounded-full pointer-events-none" />
          <FlowerIcon src="/flower-wildflower.svg" className="hidden lg:block absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-80 h-80 opacity-30" />
        </div>
      </section>

      {/* Vibrant Atmosphere Section */}
      <section className="mt-40 md:mt-80 px-4 md:px-6 relative z-10">
        <div className="max-w-7xl mx-auto rounded-[3rem] md:rounded-[6rem] bg-rose-bold text-white p-12 md:p-48 text-center shadow-[0_80px_150px_-30px_rgba(138,74,74,0.6)] overflow-hidden relative">
          <div className="absolute inset-0 botanical-pattern opacity-30" />
          <FlowerIcon src="/flower-rose.svg" className="absolute top-0 right-0 w-[50%] h-[50%] opacity-20 -translate-y-1/3 translate-x-1/3 rotate-45" />
          <FlowerIcon src="/flower-lavender.svg" className="absolute bottom-0 left-0 w-[40%] h-[40%] opacity-20 translate-y-1/4 -translate-x-1/4 -rotate-12" />
          
          <div className="relative z-10">
            <h2 className="text-4xl md:text-9xl font-bold mb-8 md:mb-16 tracking-tight uppercase px-4">Vibrant Precision</h2>
            <div className="w-32 md:w-64 h-[2px] md:h-[4px] bg-white mx-auto mb-8 md:mb-16" />
            <p className="text-white text-xl md:text-5xl font-medium leading-tight max-w-5xl mx-auto font-botanical italic px-4">
              "We embrace the bold vitality of the markets. Our algorithms don't just survive; they bloom. Every trade is a carefully cultivated moment of growth in our digital garden."
            </p>
            <div className="mt-12 md:mt-28 inline-block px-10 md:px-20 py-5 md:py-10 rounded-full border-2 md:border-4 border-white text-white uppercase tracking-[0.3em] md:tracking-[0.6em] text-[12px] md:text-[16px] font-black hover:bg-white hover:text-rose-bold transition-all duration-700 cursor-default backdrop-blur-md">
              Secure Garden Portal
            </div>
          </div>
        </div>
      </section>

      {/* Footer Section */}
      <footer className="pt-40 md:pt-80 pb-20 px-6 text-center relative">
        <div className="absolute top-20 md:top-40 left-1/2 -translate-x-1/2 w-full flex justify-center gap-8 md:gap-16">
           <FlowerIcon src="/flower-rose.svg" className="w-16 h-16 md:w-32 md:h-32" />
           <FlowerIcon src="/flower-lavender.svg" className="w-16 h-16 md:w-32 md:h-32" />
           <FlowerIcon src="/flower-sage.svg" className="w-16 h-16 md:w-32 md:h-32" />
        </div>
        
        <div className="flex flex-col items-center gap-12 md:gap-16 relative z-10">
          <div className="flex gap-10 md:gap-20 text-rose-bold">
            <MoonIcon className="w-10 h-10 md:w-14 md:h-14" />
            <FlowerIcon src="/flower-wildflower.svg" className="w-10 h-10 md:w-14 md:h-14" />
            <MoonIcon className="w-10 h-10 md:w-14 md:h-14 rotate-180" />
          </div>
          <div className="flex flex-col items-center gap-4 md:gap-8 text-[#1a1c17] dark:text-[#ffffff] uppercase tracking-[0.5em] md:tracking-[1em] text-[10px] md:text-[14px] font-black">
            <span>Cultivated with Passion</span>
            <a href="https://cto.new" className="text-rose-bold hover:scale-110 transition-all duration-500 text-xl md:text-2xl tracking-normal">
              cto.new
            </a>
          </div>
        </div>
      </footer>
    </main>
  );
}
