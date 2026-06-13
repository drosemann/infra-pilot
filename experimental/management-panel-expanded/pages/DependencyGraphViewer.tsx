import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { toast } from 'sonner';
import { apiClient } from '../lib/api';
import type { DependencyGraph, DependencyNode, DependencyEdge, EdgeType, ImpactAnalysis } from '../lib/types';

const EDGE_COLORS: Record<EdgeType, string> = {
  http: '#3b82f6',
  grpc: '#10b981',
  database: '#f59e0b',
  message_queue: '#8b5cf6',
  file_system: '#ef4444',
};

const EDGE_LABELS: Record<EdgeType, string> = {
  http: 'HTTP',
  grpc: 'gRPC',
  database: 'DB',
  message_queue: 'MQ',
  file_system: 'FS',
};

const NODE_COLORS: Record<string, string> = {
  service: '#1e40af',
  database: '#92400e',
  queue: '#6d28d9',
  cache: '#0f766e',
  storage: '#7c3aed',
  external: '#4b5563',
};

const STATUS_COLORS: Record<string, string> = {
  healthy: '#10b981',
  degraded: '#f59e0b',
  down: '#ef4444',
  unknown: '#6b7280',
};

interface LayoutNode extends DependencyNode {
  x: number;
  y: number;
  vx: number;
  vy: number;
  pinned: boolean;
}

const NODE_RADIUS = 28;
const REPULSION = 8000;
const ATTRACTION = 0.005;
const DAMPING = 0.85;

function forceSimulation(nodes: LayoutNode[], edges: DependencyEdge[], width: number, height: number, iterations: number): LayoutNode[] {
  const result = nodes.map(n => ({ ...n }));

  for (let iter = 0; iter < iterations; iter++) {
    // Repulsion between all nodes
    for (let i = 0; i < result.length; i++) {
      for (let j = i + 1; j < result.length; j++) {
        const dx = result[j].x - result[i].x;
        const dy = result[j].y - result[i].y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const force = REPULSION / (dist * dist);
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;
        if (!result[i].pinned) { result[i].vx -= fx; result[i].vy -= fy; }
        if (!result[j].pinned) { result[j].vx += fx; result[j].vy += fy; }
      }
    }

    // Attraction along edges
    for (const edge of edges) {
      const src = result.findIndex(n => n.id === edge.source);
      const tgt = result.findIndex(n => n.id === edge.target);
      if (src < 0 || tgt < 0) continue;
      const dx = result[tgt].x - result[src].x;
      const dy = result[tgt].y - result[src].y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 1;
      const force = ATTRACTION * dist;
      const fx = (dx / dist) * force;
      const fy = (dy / dist) * force;
      if (!result[src].pinned) { result[src].vx += fx; result[src].vy += fy; }
      if (!result[tgt].pinned) { result[tgt].vx -= fx; result[tgt].vy -= fy; }
    }

    // Apply velocity and damping
    for (const n of result) {
      if (n.pinned) continue;
      n.vx *= DAMPING;
      n.vy *= DAMPING;
      n.x += n.vx;
      n.y += n.vy;
      // Boundary
      n.x = Math.max(NODE_RADIUS, Math.min(width - NODE_RADIUS, n.x));
      n.y = Math.max(NODE_RADIUS, Math.min(height - NODE_RADIUS, n.y));
    }
  }
  return result;
}

export default function DependencyGraphViewer() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const projectedRef = useRef<any[]>([]);
  const [graph, setGraph] = useState<DependencyGraph | null>(null);
  const [layoutNodes, setLayoutNodes] = useState<LayoutNode[]>([]);
  const [selectedNode, setSelectedNode] = useState<DependencyNode | null>(null);
  const [impact, setImpact] = useState<ImpactAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [dimensions, setDimensions] = useState({ w: 900, h: 600 });
  const [showLegend, setShowLegend] = useState(true);

  const loadGraph = useCallback(async () => {
    setLoading(true);
    try {
      const data = await apiClient.getDependencyGraph();
      setGraph(data);
    } catch { toast.error('Failed to load dependency graph'); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { loadGraph(); }, [loadGraph]);

  // Paint event for HTML-in-Canvas labels
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    canvas.setAttribute('layoutsubtree', '');
    const onPaint = () => {
      const ctx = canvas.getContext('2d');
      if (!ctx || typeof (ctx as any).drawElementImage !== 'function') return;
      const projected = projectedRef.current;
      if (projected.length === 0) return;
      const dpr = window.devicePixelRatio || 1;
      const w = dimensions.w || 900;
      ctx.save();
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      for (const node of projected) {
        const el = canvas.querySelector<HTMLDivElement>(`[data-dgv="${node.id}"]`);
        if (!el) continue;
        try {
          const r = 28 + 4;
          const transform = (ctx as any).drawElementImage(el, node.x, node.y + r + 14);
          if (transform) el.style.transform = transform.toString();
        } catch {}
      }
      if (graph) {
        for (const edge of graph.edges) {
          const src = projected.find(n => n.id === edge.source);
          const tgt = projected.find(n => n.id === edge.target);
          if (!src || !tgt || !edge.label) continue;
          const midX = (src.x + tgt.x) / 2;
          const midY = (src.y + tgt.y) / 2;
          const dy = tgt.y - src.y;
          const dx = tgt.x - src.x;
          const dist = Math.sqrt(dx * dx + dy * dy);
          const nx = -dy / dist;
          const ny = dx / dist;
          const eSpan = canvas.querySelector<HTMLSpanElement>(`[data-dgv-e="${edge.id}"]`);
          if (!eSpan) continue;
          try {
            const transform = (ctx as any).drawElementImage(eSpan, midX + nx * 12, midY + ny * 12);
            if (transform) eSpan.style.transform = transform.toString();
          } catch {}
        }
      }
      const zoomEl = canvas.querySelector<HTMLSpanElement>('[data-dgv-zoom]');
      if (zoomEl) {
        try {
          const transform = (ctx as any).drawElementImage(zoomEl, w - 12, 20);
          if (transform) zoomEl.style.transform = transform.toString();
        } catch {}
      }
      ctx.restore();
    };
    canvas.addEventListener('paint', onPaint);
    return () => canvas.removeEventListener('paint', onPaint);
  }, [graph]);

  // Compute layout when graph changes
  useEffect(() => {
    if (!graph || graph.nodes.length === 0) return;
    const w = containerRef.current?.clientWidth || 900;
    const h = 600;
    setDimensions({ w, h });

    const initialNodes: LayoutNode[] = graph.nodes.map((n, i) => {
      const angle = (i / graph.nodes.length) * Math.PI * 2;
      const radius = Math.min(w, h) * 0.3;
      return {
        ...n,
        x: w / 2 + Math.cos(angle) * radius,
        y: h / 2 + Math.sin(angle) * radius,
        vx: 0, vy: 0, pinned: false,
      };
    });

    const simNodes = forceSimulation(initialNodes, graph.edges, w, h, 100);
    setLayoutNodes(simNodes);
  }, [graph]);

  // Canvas rendering
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || layoutNodes.length === 0) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = dimensions.w * dpr;
    canvas.height = dimensions.h * dpr;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, dimensions.w, dimensions.h);
    ctx.fillStyle = '#0f172a';
    ctx.fillRect(0, 0, dimensions.w, dimensions.h);

    // Store projected for paint event + update HTML labels
    projectedRef.current = layoutNodes;
    const supportsHtml = typeof (ctx as any).drawElementImage === 'function';
    if (supportsHtml) {
      const existing = canvas.querySelectorAll('[data-dgv]');
      const ids = new Set(layoutNodes.map(n => n.id));
      for (const el of existing) { if (!ids.has(el.getAttribute('data-dgv')!)) el.remove(); }
      layoutNodes.forEach(node => {
        let div = canvas.querySelector<HTMLDivElement>(`[data-dgv="${node.id}"]`);
        if (!div) { div = document.createElement('div'); div.setAttribute('data-dgv', node.id); canvas.appendChild(div); }
        div.style.cssText = 'position:absolute;left:0;top:0;pointer-events:none;text-align:center;';
        div.innerHTML = `<div style="font:${selectedNode?.id === node.id ? 'bold 10px sans-serif' : '9px sans-serif'};color:#e2e8f0">${node.name}</div><div style="font:7px sans-serif;color:#64748b">${node.type}</div>`;
      });
      if (graph) {
        const eExisting = canvas.querySelectorAll('[data-dgv-e]');
        const eIds = new Set(graph.edges.map(e => e.id));
        for (const el of eExisting) { if (!eIds.has(el.getAttribute('data-dgv-e')!)) el.remove(); }
        graph.edges.forEach(edge => {
          if (!edge.label) return;
          let span = canvas.querySelector<HTMLSpanElement>(`[data-dgv-e="${edge.id}"]`);
          if (!span) { span = document.createElement('span'); span.setAttribute('data-dgv-e', edge.id); canvas.appendChild(span); }
          span.textContent = edge.label;
          span.style.cssText = 'position:absolute;left:0;top:0;pointer-events:none;font:9px sans-serif;color:#94a3b8;white-space:nowrap;';
        });
      }
      let zoomEl = canvas.querySelector<HTMLSpanElement>('[data-dgv-zoom]');
      if (!zoomEl) { zoomEl = document.createElement('span'); zoomEl.setAttribute('data-dgv-zoom', ''); canvas.appendChild(zoomEl); }
      zoomEl.textContent = `${Math.round(zoom * 100)}% | ${layoutNodes.length} nodes | ${graph?.edges.length || 0} edges`;
      zoomEl.style.cssText = 'position:absolute;left:0;top:0;pointer-events:none;font:11px sans-serif;color:#94a3b8;white-space:nowrap;';
      if (typeof (canvas as any).requestPaint === 'function') (canvas as any).requestPaint();
    }

    ctx.save();
    ctx.translate(pan.x, pan.y);
    ctx.scale(zoom, zoom);

    // Center offset for layout
    const cx = dimensions.w / 2;
    const cy = dimensions.h / 2;

    // Draw edges
    if (graph) {
      for (const edge of graph.edges) {
        const src = layoutNodes.find(n => n.id === edge.source);
        const tgt = layoutNodes.find(n => n.id === edge.target);
        if (!src || !tgt) continue;

        const dx = tgt.x - src.x;
        const dy = tgt.y - src.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        const nx = -dy / dist;
        const ny = dx / dist;

        ctx.beginPath();
        ctx.moveTo(src.x + nx * NODE_RADIUS * 0.3, src.y + ny * NODE_RADIUS * 0.3);
        ctx.lineTo(tgt.x - nx * NODE_RADIUS * 0.3, tgt.y - ny * NODE_RADIUS * 0.3);

        const color = EDGE_COLORS[edge.type] || '#6b7280';
        ctx.strokeStyle = color;
        ctx.lineWidth = Math.max(1, Math.min(8, edge.weight * 3));
        ctx.globalAlpha = 0.6;
        ctx.stroke();
        ctx.globalAlpha = 1;

        // Arrow
        const midX = (src.x + tgt.x) / 2;
        const midY = (src.y + tgt.y) / 2;
        const angle = Math.atan2(dy, dx);

        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.moveTo(midX + nx * 4, midY + ny * 4);
        ctx.lineTo(midX + Math.cos(angle) * 10, midY + Math.sin(angle) * 10);
        ctx.lineTo(midX - nx * 4, midY - ny * 4);
        ctx.closePath();
        ctx.fill();

        // Edge label — HTML-in-Canvas via paint event, fillText fallback
        if (edge.label && !supportsHtml) {
          ctx.fillStyle = '#94a3b8';
          ctx.font = '9px sans-serif';
          ctx.textAlign = 'center';
          ctx.fillText(edge.label, midX + nx * 12, midY + ny * 12);
        }
      }
    }

    // Draw nodes
    for (const node of layoutNodes) {
      const isSelected = selectedNode?.id === node.id;
      const x = node.x;
      const y = node.y;
      const r = isSelected ? NODE_RADIUS + 4 : NODE_RADIUS;

      // Glow for selected
      if (isSelected) {
        ctx.beginPath();
        ctx.arc(x, y, r + 6, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(59,130,246,0.2)';
        ctx.fill();
      }

      // Node circle
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fillStyle = NODE_COLORS[node.type] || '#4b5563';
      ctx.fill();
      ctx.strokeStyle = STATUS_COLORS[node.status] || '#6b7280';
      ctx.lineWidth = isSelected ? 3 : 2;
      ctx.stroke();

      // Status indicator dot
      ctx.beginPath();
      ctx.arc(x + r * 0.6, y - r * 0.6, 5, 0, Math.PI * 2);
      ctx.fillStyle = STATUS_COLORS[node.status] || '#6b7280';
      ctx.fill();
      ctx.strokeStyle = '#0f172a';
      ctx.lineWidth = 1.5;
      ctx.stroke();

      // Node label — HTML-in-Canvas via paint event, fillText fallback
      if (!supportsHtml) {
        ctx.fillStyle = '#e2e8f0';
        ctx.font = isSelected ? 'bold 10px sans-serif' : '9px sans-serif';
        ctx.textAlign = 'center';
        const label = node.name.length > 14 ? node.name.slice(0, 12) + '..' : node.name;
        ctx.fillText(label, x, y + r + 14);
        ctx.fillStyle = '#64748b';
        ctx.font = '7px sans-serif';
        ctx.fillText(node.type, x, y + r + 24);
      }
    }

    ctx.restore();

    // Zoom indicator — HTML-in-Canvas via paint event, fillText fallback
    if (!supportsHtml) {
      ctx.fillStyle = '#94a3b8';
      ctx.font = '11px sans-serif';
      ctx.textAlign = 'right';
      ctx.fillText(`${Math.round(zoom * 100)}% | ${layoutNodes.length} nodes | ${graph?.edges.length || 0} edges`, dimensions.w - 12, 20);
    }

  }, [layoutNodes, graph, selectedNode, zoom, pan, dimensions]);

  // Filter nodes
  const filteredNodes = useMemo(() => {
    if (!graph) return [];
    return graph.nodes.filter(n => {
      if (searchQuery && !n.name.toLowerCase().includes(searchQuery.toLowerCase()) && !n.id.toLowerCase().includes(searchQuery.toLowerCase())) return false;
      if (filterType !== 'all' && n.type !== filterType) return false;
      if (filterStatus !== 'all' && n.status !== filterStatus) return false;
      return true;
    });
  }, [graph, searchQuery, filterType, filterStatus]);

  const handleCanvasClick = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!canvasRef.current || layoutNodes.length === 0) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const mx = (e.clientX - rect.left - pan.x) / zoom;
    const my = (e.clientY - rect.top - pan.y) / zoom;

    // Find closest node
    let closest: DependencyNode | null = null;
    let minDist = Infinity;
    for (const node of layoutNodes) {
      const dx = mx - (node.x - dimensions.w / 2 + dimensions.w / 2);
      const dy = my - (node.y - dimensions.h / 2 + dimensions.h / 2);
      // Actually we need to account for the canvas being centered
      const ndx = mx - node.x;
      const ndy = my - node.y;
      const d = Math.sqrt(ndx * ndx + ndy * ndy);
      if (d < NODE_RADIUS + 5 && d < minDist) {
        minDist = d;
        closest = node;
      }
    }

    if (closest) {
      setSelectedNode(closest);
      apiClient.getImpactAnalysis(closest.id)
        .then(setImpact)
        .catch(() => setImpact(null));
    } else {
      setSelectedNode(null);
      setImpact(null);
    }
  }, [layoutNodes, zoom, pan, dimensions]);

  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    setZoom(prev => Math.max(0.1, Math.min(5, prev * delta)));
  }, []);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (e.button === 1 || e.button === 0) {
      setIsDragging(true);
      setDragStart({ x: e.clientX, y: e.clientY });
    }
  }, []);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!isDragging) return;
    const dx = e.clientX - dragStart.x;
    const dy = e.clientY - dragStart.y;
    setPan(prev => ({ x: prev.x + dx, y: prev.y + dy }));
    setDragStart({ x: e.clientX, y: e.clientY });
  }, [isDragging, dragStart]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleExport = useCallback((format: 'png' | 'svg') => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    if (format === 'png') {
      const link = document.createElement('a');
      link.download = 'dependency-graph.png';
      link.href = canvas.toDataURL('image/png');
      link.click();
      toast.success('Graph exported as PNG');
    } else {
      toast.info('SVG export requires server-side rendering');
    }
  }, []);

  const handleDiscover = async () => {
    try {
      const data = await apiClient.discoverDependencies();
      setGraph(data);
      toast.success('Dependencies discovered');
    } catch { toast.error('Discovery failed'); }
  };

  const handleResetView = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  const nodeTypeCounts = useMemo(() => {
    if (!graph) return {};
    const counts: Record<string, number> = {};
    for (const n of graph.nodes) {
      counts[n.type] = (counts[n.type] || 0) + 1;
    }
    return counts;
  }, [graph]);

  const edgeTypeCounts = useMemo(() => {
    if (!graph) return {};
    const counts: Record<string, number> = {};
    for (const e of graph.edges) {
      counts[e.type] = (counts[e.type] || 0) + 1;
    }
    return counts;
  }, [graph]);

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Dependency Graph</h1>
          <p className="text-slate-400">Visualize service dependencies, data flows, and API relationships</p>
        </div>
      </div>

      {/* Stats */}
      {graph && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-3">
            <p className="text-xs text-slate-400">Services</p>
            <p className="text-lg font-bold text-white">{graph.nodes.filter(n => n.type === 'service').length}</p>
          </div>
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-3">
            <p className="text-xs text-slate-400">Databases</p>
            <p className="text-lg font-bold text-white">{graph.nodes.filter(n => n.type === 'database').length}</p>
          </div>
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-3">
            <p className="text-xs text-slate-400">Edges</p>
            <p className="text-lg font-bold text-white">{graph.edges.length}</p>
          </div>
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-3">
            <p className="text-xs text-slate-400">Degraded</p>
            <p className="text-lg font-bold text-yellow-400">{graph.nodes.filter(n => n.status === 'degraded').length}</p>
          </div>
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-3">
            <p className="text-xs text-slate-400">Down</p>
            <p className="text-lg font-bold text-red-400">{graph.nodes.filter(n => n.status === 'down').length}</p>
          </div>
        </div>
      )}

      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative">
          <input type="text" value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
            placeholder="Search services..."
            className="w-48 px-3 py-1.5 bg-slate-800 border border-slate-700 rounded text-sm text-white outline-none focus:border-blue-500 pl-8" />
          <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400 text-xs">🔍</span>
        </div>

        <select value={filterType} onChange={e => setFilterType(e.target.value)}
          className="px-3 py-1.5 bg-slate-800 border border-slate-700 rounded text-sm text-white outline-none focus:border-blue-500">
          <option value="all">All Types</option>
          <option value="service">Services</option>
          <option value="database">Databases</option>
          <option value="queue">Queues</option>
          <option value="cache">Caches</option>
          <option value="storage">Storage</option>
          <option value="external">External</option>
        </select>

        <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)}
          className="px-3 py-1.5 bg-slate-800 border border-slate-700 rounded text-sm text-white outline-none focus:border-blue-500">
          <option value="all">All Status</option>
          <option value="healthy">Healthy</option>
          <option value="degraded">Degraded</option>
          <option value="down">Down</option>
        </select>

        <button onClick={handleResetView}
          className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-white text-sm rounded transition-colors">
          Reset View
        </button>
        <button onClick={() => setShowLegend(!showLegend)}
          className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-white text-sm rounded transition-colors">
          {showLegend ? 'Hide' : 'Show'} Legend
        </button>
        <button onClick={handleDiscover}
          className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded transition-colors">
          🔍 Auto-Discover
        </button>
        <button onClick={() => handleExport('png')}
          className="px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white text-sm rounded transition-colors">
          📷 Export PNG
        </button>
      </div>

      {/* Main layout */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {/* Graph canvas */}
        <div className="lg:col-span-3">
          <div ref={containerRef} className="relative bg-slate-900 border border-slate-700 rounded-lg overflow-hidden" style={{ minHeight: '600px' }}>
            {loading ? (
              <div className="absolute inset-0 flex items-center justify-center text-slate-400">Loading graph...</div>
            ) : (
              <canvas
                ref={canvasRef}
                className="w-full cursor-grab active:cursor-grabbing"
                style={{ minHeight: '600px' }}
                onClick={handleCanvasClick}
                onWheel={handleWheel}
                onMouseDown={handleMouseDown}
                onMouseMove={handleMouseMove}
                onMouseUp={handleMouseUp}
                onMouseLeave={handleMouseUp}
              />
            )}

            {/* Legend overlay */}
            {showLegend && (
              <div className="absolute top-3 left-3 bg-slate-800/90 border border-slate-700 rounded-lg p-3 text-xs z-10">
                <p className="text-white font-semibold mb-2">Edge Types</p>
                {(Object.keys(EDGE_COLORS) as EdgeType[]).map(type => (
                  <div key={type} className="flex items-center gap-2 mb-1">
                    <div className="w-4 h-0.5" style={{ backgroundColor: EDGE_COLORS[type] }} />
                    <span className="text-slate-300">{EDGE_LABELS[type]}</span>
                  </div>
                ))}
                <p className="text-white font-semibold mt-3 mb-2">Node Types</p>
                {Object.entries(NODE_COLORS).map(([type, color]) => (
                  <div key={type} className="flex items-center gap-2 mb-1">
                    <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
                    <span className="text-slate-300 capitalize">{type}</span>
                  </div>
                ))}
                <p className="text-white font-semibold mt-3 mb-2">Status</p>
                {Object.entries(STATUS_COLORS).map(([status, color]) => (
                  <div key={status} className="flex items-center gap-2 mb-1">
                    <div className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
                    <span className="text-slate-300 capitalize">{status}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Filtered node count */}
            {searchQuery && (
              <div className="absolute top-3 right-3 bg-slate-800/90 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-300 z-10">
                Found {filteredNodes.length} / {graph?.nodes.length || 0} nodes
              </div>
            )}
          </div>
        </div>

        {/* Detail panel */}
        <div className="space-y-4">
          {selectedNode ? (
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-white mb-3">{selectedNode.name}</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400">ID</span>
                  <span className="text-xs text-slate-300 font-mono">{selectedNode.id}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400">Type</span>
                  <span className="text-xs text-white capitalize">{selectedNode.type}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400">Status</span>
                  <span className={`text-xs font-medium ${STATUS_COLORS[selectedNode.status] ? `text-${STATUS_COLORS[selectedNode.status].replace('#', '')}` : ''}`}
                    style={{ color: STATUS_COLORS[selectedNode.status] }}>
                    {selectedNode.status}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400">Version</span>
                  <span className="text-xs text-slate-300">{selectedNode.version}</span>
                </div>
                <hr className="border-slate-700" />
                <p className="text-xs text-slate-400 font-semibold">Metrics</p>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400">Latency</span>
                  <span className="text-xs text-yellow-400">{selectedNode.metrics.latency_ms}ms</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400">Error Rate</span>
                  <span className="text-xs text-red-400">{(selectedNode.metrics.error_rate * 100).toFixed(1)}%</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400">Requests/min</span>
                  <span className="text-xs text-white">{selectedNode.metrics.requests_per_min}</span>
                </div>

                {selectedNode.tags.length > 0 && (
                  <>
                    <hr className="border-slate-700" />
                    <div className="flex flex-wrap gap-1">
                      {selectedNode.tags.map((tag, i) => (
                        <span key={i} className="text-xs bg-slate-700 text-slate-300 px-2 py-0.5 rounded">{tag}</span>
                      ))}
                    </div>
                  </>
                )}
              </div>
            </div>
          ) : (
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 text-center text-slate-500 text-sm">
              Click a node to see details
            </div>
          )}

          {/* Impact Analysis */}
          {impact && (
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-white mb-3">Impact Analysis</h3>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-slate-400">Downstream</span>
                  <span className="text-white font-medium">{impact.downstream_count}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Blast Radius</span>
                  <span className="text-red-400 font-medium">{impact.blast_radius}%</span>
                </div>
                {impact.downstream_services.length > 0 && (
                  <>
                    <p className="text-slate-400 mt-2 font-semibold">Affected Services</p>
                    <div className="space-y-1">
                      {impact.downstream_services.slice(0, 10).map(s => (
                        <div key={s} className="text-slate-300">{s}</div>
                      ))}
                      {impact.downstream_services.length > 10 && (
                        <div className="text-slate-500">+{impact.downstream_services.length - 10} more</div>
                      )}
                    </div>
                  </>
                )}
              </div>
            </div>
          )}

          {/* Summary counts */}
          {graph && (
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-white mb-3">Summary</h3>
              <div className="space-y-2 text-xs">
                {Object.entries(nodeTypeCounts).map(([type, count]) => (
                  <div key={type} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full" style={{ backgroundColor: NODE_COLORS[type] || '#4b5563' }} />
                      <span className="text-slate-400 capitalize">{type}</span>
                    </div>
                    <span className="text-white">{count}</span>
                  </div>
                ))}
                <hr className="border-slate-700" />
                {Object.entries(edgeTypeCounts).map(([type, count]) => (
                  <div key={type} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-0.5" style={{ backgroundColor: EDGE_COLORS[type as EdgeType] || '#6b7280' }} />
                      <span className="text-slate-400">{EDGE_LABELS[type as EdgeType] || type}</span>
                    </div>
                    <span className="text-white">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}