import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";

const scorecards = [
  {
    id: "dc-1", name: "DataCenter East", overall: 87,
    categories: [
      { name: "PUE Efficiency", score: 92, target: 1.2, actual: 1.25 },
      { name: "Cooling Efficiency", score: 85, target: 1.0, actual: 1.1 },
      { name: "Power Usage", score: 78, target: 500, actual: 580 },
      { name: "Renewable Mix", score: 95, target: 60, actual: 72 },
      { name: "Carbon Footprint", score: 82, target: 100, actual: 85 },
    ],
    lastUpdated: "2h ago",
  },
  {
    id: "dc-2", name: "DataCenter West", overall: 73,
    categories: [
      { name: "PUE Efficiency", score: 75, target: 1.2, actual: 1.35 },
      { name: "Cooling Efficiency", score: 68, target: 1.0, actual: 1.25 },
      { name: "Power Usage", score: 70, target: 500, actual: 540 },
      { name: "Renewable Mix", score: 65, target: 60, actual: 42 },
      { name: "Carbon Footprint", score: 88, target: 100, actual: 62 },
    ],
    lastUpdated: "1h ago",
  },
  {
    id: "dc-3", name: "DataCenter EU", overall: 94,
    categories: [
      { name: "PUE Efficiency", score: 96, target: 1.2, actual: 1.18 },
      { name: "Cooling Efficiency", score: 92, target: 1.0, actual: 1.05 },
      { name: "Power Usage", score: 90, target: 500, actual: 510 },
      { name: "Renewable Mix", score: 98, target: 60, actual: 85 },
      { name: "Carbon Footprint", score: 95, target: 100, actual: 45 },
    ],
    lastUpdated: "30m ago",
  },
];

function getScoreColor(score: number): string {
  if (score >= 90) return "text-green-500";
  if (score >= 75) return "text-amber-500";
  return "text-red-500";
}

function getProgressColor(score: number): string {
  if (score >= 90) return "bg-green-500";
  if (score >= 75) return "bg-amber-500";
  return "bg-red-500";
}

export default function EfficiencyScorecards() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Efficiency Scorecards</h1>
        <Badge variant="outline" className="text-sm">Real-time</Badge>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {scorecards.map(dc => (
          <Card key={dc.id} className="overflow-hidden">
            <CardHeader className="pb-2 border-b">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">{dc.name}</CardTitle>
                <span className={`text-3xl font-bold ${getScoreColor(dc.overall)}`}>
                  {dc.overall}
                </span>
              </div>
              <p className="text-xs text-muted-foreground">Updated {dc.lastUpdated}</p>
            </CardHeader>
            <CardContent className="pt-4 space-y-3">
              {dc.categories.map(cat => (
                <div key={cat.name} className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <span>{cat.name}</span>
                    <span className={`font-medium ${getScoreColor(cat.score)}`}>
                      {cat.score}/100
                    </span>
                  </div>
                  <Progress value={cat.score} className="h-2"
                    indicatorClassName={getProgressColor(cat.score)} />
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>Target: {cat.target}</span>
                    <span>Actual: {cat.actual}</span>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
