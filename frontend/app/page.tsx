import ChatWindow from "@/components/ChatWindow";
import Disclaimer from "@/components/Disclaimer";

export default function Home() {
  return (
    <div className="flex flex-col min-h-full">
      <header className="border-b border-ink/10 bg-paper px-6 py-4 shrink-0">
        <div className="max-w-3xl mx-auto">
          <h1 className="font-display text-2xl font-bold text-ink tracking-tight">
            Dalil Route
          </h1>
          <p className="text-sm text-muted mt-0.5">
            Comprendre le Code de la route marocain
          </p>
        </div>
      </header>

      <div className="bg-gold/20 border-b border-gold/40 px-6 py-2.5 shrink-0">
        <p className="text-xs text-ink/70 max-w-3xl mx-auto">
          Ne saisissez pas d&apos;informations personnelles (CIN, plaque
          d&apos;immatriculation, numéro PV).
        </p>
      </div>

      <main className="flex flex-col flex-1 min-h-0">
        <ChatWindow />
      </main>

      <Disclaimer />
    </div>
  );
}
