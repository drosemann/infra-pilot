// Welle 5: Widget-Deskriptoren (reine Daten, kein JSX -> build-sicher).

export interface FunWidget {
  key: string;
  title: string;
  endpoint: string;
  flag: string;
}

export const WAVE5_WIDGETS: FunWidget[] = [
  { key: "staffelstab", title: "On-Call-Staffelstab", endpoint: "/api/fun/staffelstab", flag: "fun.welle5.staffelstab" },
  { key: "incident-krimi", title: "Incident-Krimi", endpoint: "/api/fun/krimi", flag: "fun.welle5.krimi" },
  { key: "tagebuch", title: "Deploy-Tagebuch", endpoint: "/api/fun/tagebuch/:app", flag: "fun.welle5.tagebuch" },
  { key: "wappen", title: "Flotten-Wappen & Titel", endpoint: "/api/fun/wappen", flag: "fun.welle5.wappen" },
  { key: "wunschbrunnen", title: "Wunschbrunnen", endpoint: "/api/fun/wunschbrunnen", flag: "fun.welle5.wunschbrunnen" },
  { key: "memorial", title: "Flotten-Memorial & Museum", endpoint: "/api/fun/memorial", flag: "fun.welle5.memorial" },
  { key: "neuling", title: "Neuling-Modus", endpoint: "/api/fun/erklaeren", flag: "fun.welle5.neuling" },
];

export const WAVE5_FLAGS: Record<string, boolean> = Object.fromEntries(
  WAVE5_WIDGETS.map((w) => [w.flag, false]),
);
