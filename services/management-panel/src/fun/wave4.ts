// Welle 4: Widget-Deskriptoren (reine Daten, kein JSX -> build-sicher).
// HINWEIS: Alle Chaos-Aktionen brauchen serverseitig umgebung in {sandbox, staging}.

export interface FunWidget {
  key: string;
  title: string;
  endpoint: string;
  flag: string;
  prodSafe: boolean;
}

export const WAVE4_WIDGETS: FunWidget[] = [
  { key: "chaos-kartenspiel", title: "Chaos-Kartenspiel", endpoint: "/api/fun/chaos-karte", flag: "fun.welle4.chaos", prodSafe: false },
  { key: "branduebung", title: "Brandübung mit Stoppuhr", endpoint: "/api/fun/branduebung", flag: "fun.welle4.brand", prodSafe: false },
  { key: "was-waere-wenn", title: "Was-wäre-wenn-Regler", endpoint: "/api/fun/waswaerewenn", flag: "fun.welle4.simulation", prodSafe: true },
  { key: "domino-vorschau", title: "Domino-Vorschau", endpoint: "/api/fun/domino", flag: "fun.welle4.domino", prodSafe: true },
  { key: "schwarzer-kasten", title: "Schwarzer-Kasten-Modus", endpoint: "/api/fun/flugschreiber", flag: "fun.welle4.flugschreiber", prodSafe: true },
];

export const WAVE4_FLAGS: Record<string, boolean> = Object.fromEntries(
  WAVE4_WIDGETS.map((w) => [w.flag, false]),
);
