import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";

const providers = [
  {
    id: "prov-1", name: "EcoCloud", rank: 1, score: 94,
    sustainability: 96, efficiency: 92, transparency: 95, innovation: 90,
    renewablePct: 95, pue: 1.15, carbonOffset: true,
    certifications: ["ISO 14001", "CarbonNeutral", "RE100"],
    badge: "Gold",
  },
  {
    id: "prov-2", name: "GreenData Corp", rank: 2, score: 88,
    sustainability: 90, efficiency: 85, transparency: 88, innovation: 87,
    renewablePct: 80, pue: 1.22, carbonOffset: true,
    certifications: ["ISO 14001", "CarbonNeutral"],
    badge: "Silver",
  },
  {
    id: "prov-3", name: "AquaHost", rank: 3, score: 82,
    sustainability: 85, efficiency: 80, transparency: 78, innovation: 83,
    renewablePct: 65, pue: 1.30, carbonOffset: false,
    certifications: ["ISO 14001"],
    badge: "Bronze",
  },
  {
    id: "prov-4", name: "Standard DC", rank: 4, score: 71,
    sustainability: 70, efficiency: 72, transparency: 68, innovation: 74,
    renewablePct: 45, pue: 1.42, carbonOffset: false,
    certifications: [],
    badge: "Standard",
  },
  {
    id: "prov-5", name: "Legacy Infra", rank: 5, score: 63,
    sustainability: 60, efficiency: 65, transparency: 62, innovation: 66,
    renewablePct: 30, pue: 1.55, carbonOffset: false,
    certifications: [],
    badge: "Standard",
  },
];

function getBadgeColor(badge: string): string {
  switch (badge) {
    case "Gold": return "bg-yellow-500 text-black";
    case "Silver": return "bg-gray-300 text-black";
    case "Bronze": return "bg-amber-700 text-white";
    default: return "bg-gray-500 text-white";
  }
}

export default function SustainableProviderRanking() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Sustainable Provider Ranking</h1>
        <Badge variant="secondary" className="text-sm">Q3 2026</Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-5">
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm">Avg Score</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">79.6</div></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm">Avg PUE</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">1.33</div></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm">Avg Renewable</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">63%</div></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm">Carbon Neutral</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">2/5</div></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm">Certified</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">3/5</div></CardContent>
        </Card>
      </div>

      <Card>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/50">
                <th className="text-left p-3 font-medium">Rank</th>
                <th className="text-left p-3 font-medium">Provider</th>
                <th className="text-left p-3 font-medium">Badge</th>
                <th className="text-left p-3 font-medium">Score</th>
                <th className="text-left p-3 font-medium">Sustainability</th>
                <th className="text-left p-3 font-medium">Efficiency</th>
                <th className="text-left p-3 font-medium">Transparency</th>
                <th className="text-left p-3 font-medium">Innovation</th>
                <th className="text-left p-3 font-medium">Renewable</th>
                <th className="text-left p-3 font-medium">PUE</th>
                <th className="text-left p-3 font-medium">Certifications</th>
              </tr>
            </thead>
            <tbody>
              {providers.map(p => (
                <tr key={p.id} className="border-b hover:bg-muted/50">
                  <td className="p-3 font-bold text-lg">#{p.rank}</td>
                  <td className="p-3 font-medium">{p.name}</td>
                  <td className="p-3">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${getBadgeColor(p.badge)}`}>
                      {p.badge}
                    </span>
                  </td>
                  <td className="p-3 font-bold">{p.score}</td>
                  <td className="p-3">{p.sustainability}</td>
                  <td className="p-3">{p.efficiency}</td>
                  <td className="p-3">{p.transparency}</td>
                  <td className="p-3">{p.innovation}</td>
                  <td className="p-3">{p.renewablePct}%</td>
                  <td className="p-3 font-mono">{p.pue}</td>
                  <td className="p-3">
                    <div className="flex flex-wrap gap-1">
                      {p.certifications.map(c => (
                        <Badge key={c} variant="outline" className="text-xs">{c}</Badge>
                      ))}
                      {p.certifications.length === 0 && (
                        <span className="text-muted-foreground">None</span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader><CardTitle className="text-lg">Top Performer: EcoCloud</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between text-sm"><span>Sustainability Score</span><span className="font-bold">96/100</span></div>
            <Progress value={96} className="h-2" indicatorClassName="bg-green-500" />
            <div className="flex justify-between text-sm"><span>Energy Efficiency</span><span className="font-bold">92/100</span></div>
            <Progress value={92} className="h-2" indicatorClassName="bg-green-500" />
            <div className="flex justify-between text-sm"><span>Transparency</span><span className="font-bold">95/100</span></div>
            <Progress value={95} className="h-2" indicatorClassName="bg-green-500" />
            <div className="flex justify-between text-sm"><span>Innovation</span><span className="font-bold">90/100</span></div>
            <Progress value={90} className="h-2" indicatorClassName="bg-blue-500" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="text-lg">Recommendations</CardTitle></CardHeader>
          <CardContent>
            <ul className="space-y-2 text-sm">
              <li className="flex items-start gap-2">
                <span className="text-green-500 mt-0.5">✓</span>
                <span>Migrate compute workloads to EcoCloud (94 score)</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-amber-500 mt-0.5">!</span>
                <span>Consider GreenData Corp for storage (88 score)</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-red-500 mt-0.5">✗</span>
                <span>Avoid Legacy Infra until PUE improves below 1.4</span>
              </li>
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
