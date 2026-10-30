// Welle 2: Widget-Deskriptoren (reine Daten, kein JSX -> build-sicher).

export interface FunWidget {
  key: string;
  title: string;
  endpoint: string;
  flag: string;
}

export const WAVE2_WIDGETS: FunWidget[] = [
  { key: "sternenkarte", title: "Flotte als Sternenkarte", endpoint: "/api/fun/sternbild", flag: "fun.welle2.sternenkarte" },
  { key: "waermebild", title: "Wärmebild-Modus", endpoint: "/api/fun/waermebild", flag: "fun.welle2.waermebild" },
  { key: "aquarium", title: "Aquarium-Ansicht", endpoint: "/api/fun/aquarium", flag: "fun.welle2.aquarium" },
  { key: "metroplan", title: "Metroplan der Deployments", endpoint: "/api/fun/metroplan", flag: "fun.welle2.metroplan" },
  { key: "latenz-wetterkarte", title: "Wetterkarte der Latenz", endpoint: "/api/fun/latenz", flag: "fun.welle2.latenz" },
  { key: "schallplatte", title: "Schallplatten-Ansicht", endpoint: "/api/fun/vinyl", flag: "fun.welle2.vinyl" },
  { key: "morse-status", title: "Morsecode-Statuslinie", endpoint: "/api/fun/morse", flag: "fun.welle2.morse" },
  { key: "fleet-wrapped", title: "Fleet Wrapped", endpoint: "/api/fun/wrapped", flag: "fun.welle2.wrapped" },
];

export const WAVE2_FLAGS: Record<string, boolean> = Object.fromEntries(
  WAVE2_WIDGETS.map((w) => [w.flag, false]),
);
