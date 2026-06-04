import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Legend } from "recharts";

const leaderboard = [
  { rank: 1, team: "platform-team", score: 92, rating: "elite", freq: "8.2/day", leadTime: "0.5h", mttr: "0.3h", cfRate: "2.1%" },
  { rank: 2, team: "finops-team", score: 85, rating: "high", freq: "4.5/day", leadTime: "2.1h", mttr: "1.2h", cfRate: "4.8%" },
  { rank: 3, team: "data-team", score: 78, rating: "high", freq: "3.0/day", leadTime: "4.5h", mttr: "3.0h", cfRate: "6.2%" },
  { rank: 4, team: "web-team", score: 72, rating: "medium", freq: "2.1/day", leadTime: "8.0h", mttr: "5.5h", cfRate: "8.5%" },
  { rank: 5, team: "security-team", score: 65, rating: "medium", freq: "1.2/day", leadTime: "12.0h", mttr: "4.0h", cfRate: "7.0%" },
];

const doraRadar = [
  { metric: "Deploy Frequency", "platform-team": 95, "finops-team": 80, "data-team": 65, "web-team": 50 },
  { metric: "Lead Time", "platform-team": 90, "finops-team": 75, "data-team": 60, "web-team": 45 },
  { metric: "MTTR", "platform-team": 92, "finops-team": 78, "data-team": 55, "web-team": 40 },
  { metric: "Change Fail Rate", "platform-team": 88, "finops-team": 82, "data-team": 70, "web-team": 55 },
];

const ratingColors: Record<string, string> = { elite: "text-purple-500", high: "text-green-500", medium: "text-yellow-500", low: "text-red-500" };

function ScoreSnapshotModal({ onClose }: { onClose: () => void }) {
  const [teamId, setTeamId] = useState("platform-team");
  const [deployCount, setDeployCount] = useState("0");
  const [leadTime, setLeadTime] = useState("0");
  const [incidents, setIncidents] = useState("0");
  const [mttr, setMttr] = useState("0");
  const [failures, setFailures] = useState("0");
  const [changes, setChanges] = useState("0");
  const handleSubmit = () => {
    onClose();
  };
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={onClose}>
      <div className="bg-white dark:bg-gray-900 rounded-lg p-6 w-full max-w-md" onClick={e => e.stopPropagation()}>
        <h2 className="text-lg font-semibold mb-4">Record DORA Snapshot</h2>
        <div className="space-y-3">
          <select value={teamId} onChange={e => setTeamId(e.target.value)} className="w-full border rounded px-3 py-2 text-sm"><option value="platform-team">Platform Team</option><option value="finops-team">FinOps Team</option><option value="data-team">Data Team</option><option value="web-team">Web Team</option></select>
          <Input type="number" placeholder="Deploy count" value={deployCount} onChange={e => setDeployCount(e.target.value)} />
          <Input type="number" step="0.1" placeholder="Lead time (hours)" value={leadTime} onChange={e => setLeadTime(e.target.value)} />
          <Input type="number" placeholder="Incident count" value={incidents} onChange={e => setIncidents(e.target.value)} />
          <Input type="number" step="0.1" placeholder="MTTR (hours)" value={mttr} onChange={e => setMttr(e.target.value)} />
          <Input type="number" placeholder="Change failures" value={failures} onChange={e => setFailures(e.target.value)} />
          <Input type="number" placeholder="Total changes" value={changes} onChange={e => setChanges(e.target.value)} />
          <div className="flex gap-2 justify-end">
            <Button variant="outline" onClick={onClose}>Cancel</Button>
            <Button onClick={handleSubmit}>Record</Button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function Scorecards() {
  const [showSnapshot, setShowSnapshot] = useState(false);
  return (
    <div className="space-y-6">
      {showSnapshot && <ScoreSnapshotModal onClose={() => setShowSnapshot(false)} />}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Developer Scorecards</h1>
        <div className="flex gap-2">
          <Badge variant="outline" className="text-sm">DORA Metrics</Badge>
          <Button size="sm" onClick={() => setShowSnapshot(true)}>Record Snapshot</Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Teams Tracked</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">5</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Avg DORA Score</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">78.4</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Elite Performers</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-purple-500">1</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Needs Improvement</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-red-500">1</div></CardContent></Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>DORA Radar</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <RadarChart data={doraRadar}>
                <PolarGrid />
                <PolarAngleAxis dataKey="metric" />
                <PolarRadiusAxis angle={30} domain={[0, 100]} />
                <Radar name="Platform" dataKey="platform-team" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.2} />
                <Radar name="FinOps" dataKey="finops-team" stroke="#10b981" fill="#10b981" fillOpacity={0.2} />
                <Radar name="Data" dataKey="data-team" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.2} />
                <Legend />
              </RadarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Score Distribution</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={leaderboard}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="team" tick={{ fontSize: 10 }} />
                <YAxis domain={[0, 100]} />
                <Tooltip />
                <Bar dataKey="score" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader><CardTitle>DORA Leaderboard</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-2">
            {leaderboard.map(e => (
              <div key={e.rank} className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center gap-3">
                  <span className="text-lg font-bold text-muted-foreground">#{e.rank}</span>
                  <div><p className="font-medium">{e.team}</p><p className="text-sm text-muted-foreground">Deploy: {e.freq} &middot; Lead: {e.leadTime} &middot; MTTR: {e.mttr}</p></div>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`font-bold ${ratingColors[e.rating] || ""}`}>{e.score}</span>
                  <Badge variant={e.rating === "elite" ? "default" : "secondary"}>{e.rating}</Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader><CardTitle>Benchmarks</CardTitle></CardHeader>
        <CardContent>
          <div className="grid gap-3 md:grid-cols-4">
            {Object.entries({ elite: "Multiple/day", high: "Daily-Weekly", medium: "Weekly", low: "Monthly" }).map(([rating, freq]) => (
              <div key={rating} className="border rounded-lg p-3 text-center">
                <p className={`font-bold capitalize ${ratingColors[rating] || ""}`}>{rating}</p>
                <p className="text-xs text-muted-foreground mt-1">{freq}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Team Goals & Predictions</CardTitle></CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="border rounded-lg p-4">
              <p className="font-medium text-sm">Set Goal</p>
              <div className="mt-2 space-y-2">
                <select className="border rounded px-2 py-1 w-full text-sm"><option>Select team...</option>{leaderboard.map(e => <option key={e.team}>{e.team}</option>)}</select>
                <select className="border rounded px-2 py-1 w-full text-sm"><option value="deployment_frequency">Deployment Frequency</option><option value="lead_time">Lead Time</option><option value="mttr">MTTR</option><option value="change_failure_rate">Change Failure Rate</option></select>
                <Input placeholder="Target value" type="number" />
                <Button size="sm" className="w-full">Set Goal</Button>
              </div>
            </div>
            <div className="border rounded-lg p-4">
              <p className="font-medium text-sm">Trend Prediction</p>
              <div className="mt-2 space-y-2">
                <select className="border rounded px-2 py-1 w-full text-sm"><option>Select team...</option>{leaderboard.map(e => <option key={e.team}>{e.team}</option>)}</select>
                <div className="flex gap-2">
                  <Input placeholder="Weeks ahead" type="number" defaultValue={4} />
                  <Button variant="outline" size="sm">Predict</Button>
                </div>
              </div>
            </div>
          </div>
          <div className="mt-4 flex gap-2">
            <Button variant="outline" size="sm">Compare Teams</Button>
            <Button variant="outline" size="sm">Ingest DORA Data</Button>
            <Button variant="outline" size="sm">Organization Summary</Button>
            <Button variant="outline" size="sm">Export Scores</Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Score History</CardTitle></CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={leaderboard.map(e => ({ name: e.team, current: e.score, target: 80 }))}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" tick={{ fontSize: 10 }} />
              <YAxis domain={[0, 100]} />
              <Tooltip />
              <Line type="monotone" dataKey="current" stroke="#3b82f6" name="Current" />
              <Line type="monotone" dataKey="target" stroke="#10b981" strokeDasharray="5 5" name="Target" />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}
