// Welle 3: Widget-Deskriptoren (reine Daten, kein JSX -> build-sicher).

export interface FunWidget {
  key: string;
  title: string;
  endpoint: string;
  flag: string;
}

export const WAVE3_WIDGETS: FunWidget[] = [
  { key: "zeitmaschine", title: "Zeitmaschinen-Slider", endpoint: "/api/fun/zeitmaschine", flag: "fun.welle3.zeitmaschine" },
  { key: "tatort", title: "Was war um 3 Uhr nachts?", endpoint: "/api/fun/tatort", flag: "fun.welle3.tatort" },
  { key: "genealogie", title: "Deploy-Genealogie", endpoint: "/api/fun/genealogie", flag: "fun.welle3.genealogie" },
  { key: "karteileichen", title: "Vergessene Container", endpoint: "/api/fun/karteileichen", flag: "fun.welle3.karteileichen" },
  { key: "prophezeiungen", title: "Prophezeiungs-Protokoll", endpoint: "/api/fun/prophezeiungen", flag: "fun.welle3.prophezeiungen" },
  { key: "ahnenpass", title: "Ahnenpass für Secrets", endpoint: "/api/fun/ahnenpass/:name", flag: "fun.welle3.ahnenpass" },
  { key: "echolot", title: "Echolot", endpoint: "/api/fun/echolot", flag: "fun.welle3.echolot" },
];

export const WAVE3_FLAGS: Record<string, boolean> = Object.fromEntries(
  WAVE3_WIDGETS.map((w) => [w.flag, false]),
);
