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
      name: "Momentum Buddy 🏃‍♂️",
      description: "We follow the crowd when they're excited! Uses EMAs and volume spikes to catch the wave.",
      color: "bg-rose-100 border-rose-200 dark:bg-rose-900/20 dark:border-rose-800",
      icon: "✨"
    },
    {
      name: "The Cool Kid 🕶️",
      description: "Finding the superstars that are doing better than everyone else. Benchmarked against the best.",
      color: "bg-orange-100 border-orange-200 dark:bg-orange-900/20 dark:border-orange-800",
      icon: "🌈"
    },
    {
      name: "Market Whisperer 🤫",
      description: "Listening to what the big players are doing across different assets. A little secret intuition.",
      color: "bg-amber-100 border-amber-200 dark:bg-amber-900/20 dark:border-amber-800",
      icon: "🔮"
    },
    {
      name: "Sentiment Sleuth 🕵️‍♀️",
      description: "Checking if everyone is happy or scared. We like to be a little different from the crowd.",
      color: "bg-emerald-100 border-emerald-200 dark:bg-emerald-900/20 dark:border-emerald-800",
      icon: "🍬"
    },
    {
      name: "Global Guardian 🌍",
      description: "Keeping an eye on the big picture. When the world is happy, we're happy too!",
      color: "bg-sky-100 border-sky-200 dark:bg-sky-900/20 dark:border-sky-800",
      icon: "🌸"
    }
  ];

  return (
    <main className="flex min-h-dvh flex-col items-center justify-start gap-12 px-6 py-20 text-center selection:bg-rose-200 selection:text-rose-900">
      <div className="flex flex-col items-center gap-6">
        <div className="animate-bounce text-6xl">🤖✨</div>
        <span className="rounded-full bg-rose-100 px-4 py-1.5 text-sm font-bold text-rose-600 dark:bg-rose-950 dark:text-rose-300 border border-rose-200 dark:border-rose-800 shadow-sm">
          Currently learning from history 📚✨
        </span>
        <h1 className="max-w-3xl text-5xl font-extrabold tracking-tight sm:text-7xl bg-gradient-to-r from-rose-500 via-orange-400 to-amber-500 bg-clip-text text-transparent">
          {businessName || "MinuteBuddy"}
        </h1>
        <p className="max-w-2xl text-xl text-stone-600 dark:text-stone-400 font-medium">
          Hi! I'm a friendly little bot finding tiny pockets of magic in the markets across crypto, stocks, and forex. 🪄💖
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-6xl w-full">
        {strategies.map((s, i) => (
          <div key={i} className={`cute-card p-8 rounded-3xl border-2 ${s.color} text-left shadow-xl shadow-stone-200/50 dark:shadow-none flex flex-col gap-4 bg-white dark:bg-stone-900`}>
            <div className="text-4xl">{s.icon}</div>
            <h3 className="font-bold text-2xl text-stone-800 dark:text-stone-100">{s.name}</h3>
            <p className="text-stone-600 dark:text-stone-400 leading-relaxed font-medium">{s.description}</p>
          </div>
        ))}
      </div>

      <div className="max-w-3xl w-full p-10 rounded-[3rem] bg-gradient-to-br from-rose-400 to-orange-400 text-white flex flex-col items-center gap-6 shadow-2xl shadow-rose-200 dark:shadow-none">
        <h2 className="text-4xl font-black">Almost ready to play! 🎈</h2>
        <p className="text-rose-50 text-xl font-medium">
          My core brain is all finished. Right now, I'm doing lots of practice runs (backtesting!) to make sure I'm the smartest buddy I can be before we go live.
        </p>
      </div>

      <footer className="text-sm text-stone-400 dark:text-stone-600 font-bold pb-8">
        Crafted with love and ✨{" "}
        <a href="https://cto.new" className="underline decoration-rose-300 hover:text-rose-400 transition-colors">
          cto.new
        </a>
      </footer>
    </main>
  );
}
