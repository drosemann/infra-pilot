// Welle 1: Widget-Deskriptoren (reine Daten, kein JSX -> build-sicher).
// Panel bindet diese spaeter an echte Karten an.

export interface FunWidget {
  key: string;
  title: string;
  endpoint: string;
  flag: string;
}

export const WAVE1_WIDGETS: FunWidget[] = [
  { key: "deploy-wetterbericht", title: "Deploy-Wetter", endpoint: "/api/fun/wetter", flag: "fun.welle1.wetter" },
  { key: "container-horoskope", title: "Container-Horoskop", endpoint: "/api/fun/horoskop/:app", flag: "fun.welle1.horoskop" },
  { key: "seismograph", title: "Flotten-Seismograph", endpoint: "/api/fun/seismograph", flag: "fun.welle1.seismograph" },
  { key: "flotten-radio", title: "Flotten-Radio", endpoint: "/api/fun/radio", flag: "fun.welle1.radio" },
  { key: "muellcontainer", title: "Müllcontainer des Tages", endpoint: "/api/fun/muell", flag: "fun.welle1.muell" },
  { key: "uptime-geburtstage", title: "Uptime-Geburtstage", endpoint: "/api/fun/geburtstage", flag: "fun.welle1.geburtstage" },
];

export const WAVE1_FLAGS: Record<string, boolean> = Object.fromEntries(
  WAVE1_WIDGETS.map((w) => [w.flag, false]),
);
