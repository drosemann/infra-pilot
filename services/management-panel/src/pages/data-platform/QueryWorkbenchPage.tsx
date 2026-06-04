import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Play, Save, Clock, Share2, Database, FileText, BookOpen, Search, Trash2, History } from 'lucide-react';

interface SavedQuery { id: string; name: string; sql: string; database: string; created: string; rows: number; duration: string; }

const mockQueries: SavedQuery[] = [
  { id: 'q-1', name: 'Active Users', sql: 'SELECT COUNT(*) FROM users WHERE last_login > NOW() - INTERVAL 7 DAY', database: 'analytics', created: '2026-05-29T10:00:00Z', rows: 1, duration: '0.32s' },
  { id: 'q-2', name: 'Revenue by Month', sql: 'SELECT DATE_TRUNC(\'month\', created_at) as month, SUM(amount) FROM orders GROUP BY 1 ORDER BY 1', database: 'analytics', created: '2026-05-28T14:00:00Z', rows: 12, duration: '1.45s' },
];

const QueryWorkbenchPage: React.FC = () => {
  const [queries, setQueries] = useState(mockQueries);
  const [sql, setSql] = useState('SELECT * FROM users LIMIT 50');
  const [results, setResults] = useState<{ columns: string[]; rows: string[][] } | null>(null);
  const [selectedDb, setSelectedDb] = useState('analytics');
  const [saveOpen, setSaveOpen] = useState(false);
  const [shareOpen, setShareOpen] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [saveName, setSaveName] = useState('');
  const [tab, setTab] = useState('editor');

  const executeQuery = () => {
    const mockResults: Record<string, { columns: string[]; rows: string[][] }> = {
      'SELECT * FROM users LIMIT 50': {
        columns: ['id', 'name', 'email', 'created_at'],
        rows: [['1', 'Alice', 'alice@example.com', '2026-01-15'], ['2', 'Bob', 'bob@example.com', '2026-02-20'], ['3', 'Charlie', 'charlie@example.com', '2026-03-10']],
      },
      'SELECT COUNT(*) FROM users': { columns: ['count'], rows: [['15000']] },
    };
    setResults(mockResults[sql] || { columns: ['message'], rows: [[`Executed query (${sql.slice(0, 30)}...)`]] });
  };

  const handleSave = () => {
    const q: SavedQuery = { id: `q-${Date.now()}`, name: saveName, sql, database: selectedDb, created: new Date().toISOString(), rows: results?.rows.length || 0, duration: `${(Math.random() * 3).toFixed(2)}s` };
    setQueries([...queries, q]);
    setSaveOpen(false);
    setSaveName('');
  };

  const loadQuery = (q: SavedQuery) => {
    setSql(q.sql);
    setResults(null);
  };

  const deleteQuery = (id: string) => {
    setQueries(queries.filter(q => q.id !== id));
  };

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Analytics Query Workbench</h1>
          <p className="text-muted-foreground">Web-based SQL editor with schema browser, query history, and visualizations</p>
        </div>
      </div>

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList>
          <TabsTrigger value="editor"><FileText className="mr-2 h-4 w-4" />Editor</TabsTrigger>
          <TabsTrigger value="saved"><Save className="mr-2 h-4 w-4" />Saved Queries</TabsTrigger>
          <TabsTrigger value="history"><History className="mr-2 h-4 w-4" />History</TabsTrigger>
        </TabsList>

        <TabsContent value="editor">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mt-4">
            <div className="lg:col-span-3 space-y-4">
              <Card>
                <CardHeader className="pb-2"><CardTitle>SQL Editor</CardTitle></CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex gap-2">
                    <Select value={selectedDb} onValueChange={setSelectedDb}>
                      <SelectTrigger className="w-48"><SelectValue /></SelectTrigger>
                      <SelectContent><SelectItem value="analytics">analytics</SelectItem><SelectItem value="lakehouse">lakehouse</SelectItem><SelectItem value="streaming">streaming</SelectItem></SelectContent>
                    </Select>
                    <Badge variant="outline" className="text-xs">{selectedDb}</Badge>
                  </div>
                  <textarea className="w-full h-36 bg-gray-900 text-gray-100 p-4 rounded border border-gray-700 font-mono text-sm" value={sql} onChange={e => setSql(e.target.value)} />
                  <div className="flex gap-2">
                    <Button onClick={executeQuery}><Play className="mr-2 h-4 w-4" />Execute</Button>
                    <Dialog open={saveOpen} onOpenChange={setSaveOpen}>
                      <DialogTrigger asChild><Button variant="outline"><Save className="mr-2 h-4 w-4" />Save</Button></DialogTrigger>
                      <DialogContent>
                        <DialogHeader><DialogTitle>Save Query</DialogTitle></DialogHeader>
                        <div className="space-y-4">
                          <div><Label>Name</Label><Input value={saveName} onChange={e => setSaveName(e.target.value)} placeholder="e.g. Active Users" /></div>
                          <div><Label>SQL</Label><pre className="bg-gray-900 p-3 rounded text-xs overflow-x-auto max-h-32">{sql.slice(0, 200)}{sql.length > 200 ? '...' : ''}</pre></div>
                          <Button className="w-full" onClick={handleSave}>Save</Button>
                        </div>
                      </DialogContent>
                    </Dialog>
                    <Dialog open={shareOpen} onOpenChange={setShareOpen}>
                      <DialogTrigger asChild><Button variant="outline"><Share2 className="mr-2 h-4 w-4" />Share</Button></DialogTrigger>
                      <DialogContent>
                        <DialogHeader><DialogTitle>Share Query</DialogTitle></DialogHeader>
                        <div className="space-y-4">
                          <div><Label>Share Link</Label><Input value={`https://infrapilot.io/queries/share/${Date.now()}`} readOnly /></div>
                          <div><Label>Permissions</Label>
                            <select className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm">
                              <option>View only</option><option>Can edit</option>
                            </select>
                          </div>
                          <Button className="w-full" onClick={() => navigator.clipboard.writeText(`https://infrapilot.io/queries/share/${Date.now()}`)}>Copy Link</Button>
                        </div>
                      </DialogContent>
                    </Dialog>
                    <Button variant="outline" onClick={() => setHistoryOpen(!historyOpen)}><History className="mr-2 h-4 w-4" />History</Button>
                  </div>
                </CardContent>
              </Card>

              {results && (
                <Card>
                  <CardHeader className="pb-2"><CardTitle>Results <span className="text-sm font-normal text-muted-foreground">— {results.rows.length} rows in {(Math.random() * 0.5 + 0.1).toFixed(2)}s</span></CardTitle></CardHeader>
                  <CardContent className="overflow-x-auto">
                    <Table>
                      <TableHeader><TableRow>{results.columns.map(c => <TableHead key={c}>{c}</TableHead>)}</TableRow></TableHeader>
                      <TableBody>{results.rows.map((row, i) => <TableRow key={i}>{row.map((cell, j) => <TableCell key={j}>{cell}</TableCell>)}</TableRow>)}</TableBody>
                    </Table>
                    <div className="mt-2 text-sm text-muted-foreground flex justify-between">
                      <span>{results.rows.length} row(s) returned</span>
                      <Button size="sm" variant="ghost" onClick={() => setResults(null)}>Clear</Button>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>

            <div className="space-y-4">
              <Card>
                <CardHeader><CardTitle><Database className="mr-2 h-4 w-4 inline" />Schema Browser</CardTitle></CardHeader>
                <CardContent>
                  <div className="space-y-1 text-sm">
                    <div className="font-medium text-blue-400">public</div>
                    <div className="pl-3 space-y-1">
                      {[
                        { name: 'users', type: 'table', columns: 8 },
                        { name: 'orders', type: 'table', columns: 12 },
                        { name: 'products', type: 'table', columns: 6 },
                        { name: 'get_stats', type: 'function' },
                        { name: 'user_view', type: 'view' },
                      ].map(obj => (
                        <div key={obj.name} className="cursor-pointer hover:text-blue-300 flex justify-between">
                          <span>{obj.name} <span className="text-muted-foreground">({obj.type})</span></span>
                          {obj.columns && <span className="text-xs text-muted-foreground">{obj.columns} cols</span>}
                        </div>
                      ))}
                    </div>
                    <div className="font-medium text-blue-400 mt-2">analytics</div>
                    <div className="pl-3 space-y-1">
                      <div className="cursor-pointer hover:text-blue-300">events <span className="text-muted-foreground">(table)</span></div>
                      <div className="cursor-pointer hover:text-blue-300">sessions <span className="text-muted-foreground">(table)</span></div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader><CardTitle><Clock className="mr-2 h-4 w-4 inline" />Recent Queries</CardTitle></CardHeader>
                <CardContent className="space-y-2">
                  {queries.slice(0, 3).map(q => (
                    <div key={q.id} className="p-2 rounded bg-gray-800 cursor-pointer hover:bg-gray-700" onClick={() => loadQuery(q)}>
                      <div className="text-sm font-medium">{q.name}</div>
                      <div className="text-xs text-muted-foreground truncate">{q.sql}</div>
                      <div className="text-xs text-muted-foreground mt-1">{q.duration} · {q.rows} rows · {new Date(q.created).toLocaleDateString()}</div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="saved">
          <Table>
            <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>SQL</TableHead><TableHead>Database</TableHead><TableHead>Rows</TableHead><TableHead>Duration</TableHead><TableHead>Created</TableHead><TableHead>Actions</TableHead></TableRow></TableHeader>
            <TableBody>
              {queries.map(q => (
                <TableRow key={q.id}>
                  <TableCell className="font-medium">{q.name}</TableCell>
                  <TableCell className="text-xs font-mono max-w-[300px] truncate">{q.sql}</TableCell>
                  <TableCell><Badge variant="outline">{q.database}</Badge></TableCell>
                  <TableCell>{q.rows}</TableCell>
                  <TableCell className="font-mono text-xs">{q.duration}</TableCell>
                  <TableCell className="text-sm">{new Date(q.created).toLocaleDateString()}</TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      <Button size="sm" variant="ghost" onClick={() => loadQuery(q)}>Open</Button>
                      <Button size="sm" variant="ghost" className="text-red-400" onClick={() => deleteQuery(q.id)}><Trash2 className="h-4 w-4" /></Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TabsContent>

        <TabsContent value="history">
          <div className="space-y-3">
            {['SELECT * FROM users LIMIT 50', 'SELECT COUNT(*) FROM orders', 'SHOW TABLES', 'SELECT date_trunc(\'day\', ts) as day, count(*) FROM events GROUP BY 1', 'SELECT table_name, row_count FROM information_schema.tables'].map((q, i) => (
              <div key={i} className="p-3 bg-gray-800 rounded flex justify-between items-center">
                <div>
                  <div className="text-sm font-mono">{q}</div>
                  <div className="text-xs text-muted-foreground">{`${i + 1}h ago`} · analytics · {(Math.random() * 2 + 0.1).toFixed(2)}s</div>
                </div>
                <Button size="sm" variant="ghost" onClick={() => { setSql(q); setTab('editor'); }}><Play className="h-3 w-3" /></Button>
              </div>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default QueryWorkbenchPage;
