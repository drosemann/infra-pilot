import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { toast } from 'sonner';
import { apiClient } from '../lib/api';

interface TopoNode {
  id: string;
  name: string;
  type: 'server' | 'container' | 'database' | 'load_balancer' | 'storage';
  status: 'running' | 'stopped' | 'error' | 'warning';
  metrics: { cpu: number; memory: number; load: number };
  position: { x: number; y: number; z: number };
  metadata: Record<string, string>;
}

interface TopoEdge {
  id: string;
  source: string;
  target: string;
  type: 'network' | 'data_flow' | 'dependency';
  bandwidth: number;
  latency_ms: number;
  status: 'active' | 'degraded' | 'down';
}

const NODE_COLORS: Record<string, string> = {
  server: '#3b82f6',
  container: '#10b981',
  database: '#f59e0b',
  load_balancer: '#8b5cf6',
  storage: '#ef4444',
};

const STATUS_COLORS: Record<string, string> = {
  running: '#10b981',
  stopped: '#6b7280',
  error: '#ef4444',
  warning: '#f59e0b',
};

const NODE_TYPES: Array<{ type: TopoNode['type']; label: string; icon: string }> = [
  { type: 'server', label: 'Server', icon: '🖥️' },
  { type: 'container', label: 'Container', icon: '📦' },
  { type: 'database', label: 'Database', icon: '🗄️' },
  { type: 'load_balancer', label: 'LB', icon: '⚖️' },
  { type: 'storage', label: 'Storage', icon: '💾' },
];

// 3D projection helpers
function project3D(x: number, y: number, z: number, angleX: number, angleY: number, distance: number, w: number, h: number): { sx: number; sy: number; scale: number } {
  const cosX = Math.cos(angleX);
  const sinX = Math.sin(angleX);
  const cosY = Math.cos(angleY);
  const sinY = Math.sin(angleY);

  // Rotate around Y axis
  let rx = x * cosY + z * sinY;
  let ry = y;
  let rz = -x * sinY + z * cosY;

  // Rotate around X axis
  const tY = ry * cosX - rz * sinX;
  rz = ry * sinX + rz * cosX;
  ry = tY;

  const perspective = distance / (distance + rz);
  const sx = w / 2 + rx * perspective * 100;
  const sy = h / 2 - ry * perspective * 100;

  return { sx, sy, scale: perspective };
}

export default function Topology3D() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const projectedRef = useRef<any[]>([]);
  const [nodes, setNodes] = useState<TopoNode[]>([]);
  const [edges, setEdges] = useState<TopoEdge[]>([]);
  const [loading, setLoading] = useState(true);
  const [angleX, setAngleX] = useState(0.4);
  const [angleY, setAngleY] = useState(0.3);
  const [zoom, setZoom] = useState(1);
  const [selectedNode, setSelectedNode] = useState<TopoNode | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0, ax: 0, ay: 0 });
  const [hoveredNode, setHoveredNode] = useState<TopoNode | null>(null);
  const [filterType, setFilterType] = useState<string>('all');
  const [autoRotate, setAutoRotate] = useState(true);
  const [dimensions, setDimensions] = useState({ w: 900, h: 600 });
  const animRef = useRef<number>(0);

  // Paint event handler for HTML-in-Canvas labels
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
      ctx.save();
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      for (const node of projected) {
        const span = canvas.querySelector<HTMLSpanElement>(`[data-t3d="${node.id}"]`);
        if (!span) continue;
        try {
          const transform = (ctx as any).drawElementImage(span, node.sx, node.sy + node.drawR + 4);
          if (transform) span.style.transform = transform.toString();
        } catch {}
      }
      ctx.restore();
    };
    canvas.addEventListener('paint', onPaint);
    return () => canvas.removeEventListener('paint', onPaint);
  }, []);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [n, e] = await Promise.all([
        apiClient.get('/api/v3/topology/nodes'),
        apiClient.get('/api/v3/topology/edges'),
      ]);
      // The topology API may not exist yet - use mock data
      const mockNodes: TopoNode[] = [
        { id: 'lb-1', name: 'Main LB', type: 'load_balancer', status: 'running', metrics: { cpu: 23, memory: 45, load: 0.3 }, position: { x: 0, y: 2, z: 0 }, metadata: { region: 'us-east' } },
        { id: 'srv-web-1', name: 'Web Server 1', type: 'server', status: 'running', metrics: { cpu: 56, memory: 62, load: 1.2 }, position: { x: -2, y: 0, z: 1.5 }, metadata: { region: 'us-east', os: 'Ubuntu 22.04' } },
        { id: 'srv-web-2', name: 'Web Server 2', type: 'server', status: 'running', metrics: { cpu: 34, memory: 51, load: 0.8 }, position: { x: 2, y: 0, z: 1.5 }, metadata: { region: 'us-west', os: 'Ubuntu 22.04' } },
        { id: 'srv-api-1', name: 'API Server 1', type: 'server', status: 'running', metrics: { cpu: 78, memory: 71, load: 2.1 }, position: { x: -1.5, y: 0, z: -1.5 }, metadata: { region: 'us-east', os: 'Debian 12' } },
        { id: 'srv-api-2', name: 'API Server 2', type: 'server', status: 'warning', metrics: { cpu: 92, memory: 88, load: 3.4 }, position: { x: 1.5, y: 0, z: -1.5 }, metadata: { region: 'us-west', os: 'Debian 12' } },
        { id: 'db-main', name: 'PostgreSQL Primary', type: 'database', status: 'running', metrics: { cpu: 45, memory: 73, load: 1.5 }, position: { x: 0, y: -1, z: -3 }, metadata: { engine: 'PostgreSQL 16', size: '500GB' } },
        { id: 'db-replica', name: 'PostgreSQL Replica', type: 'database', status: 'running', metrics: { cpu: 22, memory: 65, load: 0.6 }, position: { x: 0, y: -1, z: 3 }, metadata: { engine: 'PostgreSQL 16', size: '500GB' } },
        { id: 'cache-1', name: 'Redis Cache', type: 'storage', status: 'running', metrics: { cpu: 12, memory: 34, load: 0.2 }, position: { x: -2.5, y: -0.5, z: 0 }, metadata: { engine: 'Redis 7', type: 'cache' } },
        { id: 'queue-1', name: 'RabbitMQ', type: 'container', status: 'running', metrics: { cpu: 8, memory: 28, load: 0.1 }, position: { x: 2.5, y: -0.5, z: 0 }, metadata: { engine: 'RabbitMQ 3.12', type: 'message queue' } },
        { id: 'storage-1', name: 'S3 Storage', type: 'storage', status: 'running', metrics: { cpu: 5, memory: 20, load: 0.1 }, position: { x: -2, y: -1.5, z: -2 }, metadata: { type: 'object storage', size: '2TB' } },
        { id: 'worker-1', name: 'Worker 1', type: 'container', status: 'running', metrics: { cpu: 67, memory: 55, load: 1.8 }, position: { x: 2, y: -1.5, z: -2 }, metadata: { runtime: 'Node.js 20' } },
        { id: 'worker-2', name: 'Worker 2', type: 'container', status: 'running', metrics: { cpu: 45, memory: 48, load: 1.1 }, position: { x: 2, y: -1.5, z: 2 }, metadata: { runtime: 'Python 3.12' } },
      ];
      const mockEdges: TopoEdge[] = [
        { id: 'e1', source: 'lb-1', target: 'srv-web-1', type: 'network', bandwidth: 1000, latency_ms: 1, status: 'active' },
        { id: 'e2', source: 'lb-1', target: 'srv-web-2', type: 'network', bandwidth: 1000, latency_ms: 5, status: 'active' },
        { id: 'e3', source: 'srv-web-1', target: 'srv-api-1', type: 'network', bandwidth: 100, latency_ms: 2, status: 'active' },
        { id: 'e4', source: 'srv-web-2', target: 'srv-api-2', type: 'network', bandwidth: 100, latency_ms: 8, status: 'degraded' },
        { id: 'e5', source: 'srv-api-1', target: 'db-main', type: 'data_flow', bandwidth: 500, latency_ms: 1, status: 'active' },
        { id: 'e6', source: 'srv-api-2', target: 'db-main', type: 'data_flow', bandwidth: 500, latency_ms: 15, status: 'active' },
        { id: 'e7', source: 'db-main', target: 'db-replica', type: 'data_flow', bandwidth: 1000, latency_ms: 2, status: 'active' },
        { id: 'e8', source: 'srv-web-1', target: 'cache-1', type: 'dependency', bandwidth: 10, latency_ms: 0.5, status: 'active' },
        { id: 'e9', source: 'srv-web-2', target: 'cache-1', type: 'dependency', bandwidth: 10, latency_ms: 5, status: 'active' },
        { id: 'e10', source: 'srv-api-1', target: 'queue-1', type: 'data_flow', bandwidth: 50, latency_ms: 1, status: 'active' },
        { id: 'e11', source: 'srv-api-2', target: 'queue-1', type: 'data_flow', bandwidth: 50, latency_ms: 3, status: 'active' },
        { id: 'e12', source: 'srv-api-1', target: 'storage-1', type: 'data_flow', bandwidth: 200, latency_ms: 10, status: 'active' },
        { id: 'e13', source: 'queue-1', target: 'worker-1', type: 'data_flow', bandwidth: 100, latency_ms: 1, status: 'active' },
        { id: 'e14', source: 'queue-1', target: 'worker-2', type: 'data_flow', bandwidth: 100, latency_ms: 2, status: 'active' },
        { id: 'e15', source: 'worker-1', target: 'db-main', type: 'data_flow', bandwidth: 50, latency_ms: 2, status: 'active' },
        { id: 'e16', source: 'worker-2', target: 'db-main', type: 'data_flow', bandwidth: 50, latency_ms: 3, status: 'active' },
      ];
      setNodes(n.data || mockNodes);
      setEdges(e.data || mockEdges);
    } catch {
      // Use mock if API fails
      setNodes([]);
      setEdges([]);
    }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  // Auto-rotate
  useEffect(() => {
    if (!autoRotate || isDragging) return;
    const interval = setInterval(() => {
      setAngleY(prev => prev + 0.005);
    }, 30);
    return () => clearInterval(interval);
  }, [autoRotate, isDragging]);

  // Canvas rendering
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;
    const w = rect.width;
    const h = Math.max(500, rect.height);
    const dpr = window.devicePixelRatio || 1;
    canvas.width = w * dpr;
    canvas.height = h * dpr;
    canvas.style.width = `${w}px`;
    canvas.style.height = `${h}px`;
    ctx.scale(dpr, dpr);
    setDimensions({ w, h });

    ctx.fillStyle = '#0a0e1a';
    ctx.fillRect(0, 0, w, h);

    // Grid
    ctx.strokeStyle = '#1a2540';
    ctx.lineWidth = 0.5;
    const gridSize = 50;
    for (let i = 0; i < w; i += gridSize) {
      ctx.beginPath();
      ctx.moveTo(i, 0);
      ctx.lineTo(i, h);
      ctx.stroke();
    }
    for (let i = 0; i < h; i += gridSize) {
      ctx.beginPath();
      ctx.moveTo(0, i);
      ctx.lineTo(w, i);
      ctx.stroke();
    }

    const distance = 5 * zoom;
    const scale = 1.5 * zoom;

    // Sort nodes by z-depth for painter's algorithm
    const projected = nodes
      .filter(n => filterType === 'all' || n.type === filterType)
      .map(n => {
        const { sx, sy, scale: s } = project3D(n.position.x * scale, n.position.y * scale, n.position.z * scale, angleX, angleY, distance, w, h);
        const isSel = selectedNode?.id === n.id;
        const isHov = hoveredNode?.id === n.id;
        const drawR = (isSel ? 16 : isHov ? 14 : 12) * s;
        return { ...n, sx, sy, depth: s, drawR };
      })
      .sort((a, b) => a.depth - b.depth);

    // Store projected for paint event + update HTML labels
    projectedRef.current = projected;
    const supportsHtmlLabel = typeof (ctx as any).drawElementImage === 'function';
    if (supportsHtmlLabel) {
      const existing = canvas.querySelectorAll('[data-t3d]');
      const projectedIds = new Set(projected.map(n => n.id));
      for (const el of existing) { if (!projectedIds.has(el.getAttribute('data-t3d')!)) el.remove(); }
      projected.forEach(node => {
        let span = canvas.querySelector<HTMLSpanElement>(`[data-t3d="${node.id}"]`);
        if (!span) { span = document.createElement('span'); span.setAttribute('data-t3d', node.id); canvas.appendChild(span); }
        span.textContent = node.name;
        span.style.cssText = `font: bold ${Math.round(9 * node.depth)}px sans-serif; color: #e2e8f0; white-space: nowrap; pointer-events: none; position: absolute; left: 0; top: 0;`;
      });
      if (typeof (canvas as any).requestPaint === 'function') (canvas as any).requestPaint();
    }

    // Draw edges
    for (const edge of edges) {
      const src = projected.find(n => n.id === edge.source);
      const tgt = projected.find(n => n.id === edge.target);
      if (!src || !tgt) continue;

      const avgDepth = (src.depth + tgt.depth) / 2;
      ctx.globalAlpha = 0.3 + avgDepth * 0.5;

      const edgeColor = edge.status === 'active' ? '#3b82f6' : edge.status === 'degraded' ? '#f59e0b' : '#ef4444';
      const lineW = Math.max(1, edge.bandwidth / 500);

      ctx.beginPath();
      ctx.moveTo(src.sx, src.sy);
      ctx.lineTo(tgt.sx, tgt.sy);
      ctx.strokeStyle = edgeColor;
      ctx.lineWidth = lineW;
      ctx.stroke();

      // Arrow
      const midX = (src.sx + tgt.sx) / 2;
      const midY = (src.sy + tgt.sy) / 2;
      const angle = Math.atan2(tgt.sy - src.sy, tgt.sx - src.sx);
      ctx.fillStyle = edgeColor;
      ctx.beginPath();
      ctx.moveTo(midX + Math.cos(angle) * 8, midY + Math.sin(angle) * 8);
      ctx.lineTo(midX + Math.cos(angle + 2.4) * 6, midY + Math.sin(angle + 2.4) * 6);
      ctx.lineTo(midX + Math.cos(angle - 2.4) * 6, midY + Math.sin(angle - 2.4) * 6);
      ctx.closePath();
      ctx.fill();

      ctx.globalAlpha = 1;
    }

    // Draw nodes
    for (const node of projected) {
      const isSelected = selectedNode?.id === node.id;
      const isHovered = hoveredNode?.id === node.id;
      const r = (isSelected ? 16 : isHovered ? 14 : 12) * node.depth;
      const color = NODE_COLORS[node.type] || '#6b7280';
      const glow = isSelected || isHovered;

      // Glow
      if (glow) {
        ctx.beginPath();
        ctx.arc(node.sx, node.sy, r + 8, 0, Math.PI * 2);
        ctx.fillStyle = color + '30';
        ctx.fill();
      }

      // Shadow/3D effect
      ctx.beginPath();
      ctx.ellipse(node.sx + 2, node.sy + 2, r, r * 0.8, 0, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(0,0,0,0.3)';
      ctx.fill();

      // Main circle
      ctx.beginPath();
      ctx.arc(node.sx, node.sy, r, 0, Math.PI * 2);
      const grad = ctx.createRadialGradient(node.sx - r * 0.3, node.sy - r * 0.3, 0, node.sx, node.sy, r);
      grad.addColorStop(0, lightenColor(color, 40));
      grad.addColorStop(1, color);
      ctx.fillStyle = grad;
      ctx.fill();

      // Border
      ctx.strokeStyle = isSelected ? '#ffffff' : STATUS_COLORS[node.status] || '#6b7280';
      ctx.lineWidth = isSelected ? 2.5 : 1.5;
      ctx.stroke();

      // Status dot
      ctx.beginPath();
      ctx.arc(node.sx + r * 0.5, node.sy - r * 0.5, 3, 0, Math.PI * 2);
      ctx.fillStyle = STATUS_COLORS[node.status] || '#6b7280';
      ctx.fill();
      ctx.strokeStyle = '#0a0e1a';
      ctx.lineWidth = 1;
      ctx.stroke();

      // Icon
      const icon = NODE_TYPES.find(t => t.type === node.type)?.icon || '❓';
      ctx.font = `${Math.round(10 * node.depth)}px sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(icon, node.sx, node.sy);

      // Label — HTML-in-Canvas via paint event, fillText fallback
      if (!supportsHtmlLabel) {
        ctx.fillStyle = '#e2e8f0';
        ctx.font = `bold ${Math.round(9 * node.depth)}px sans-serif`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';
        const label = node.name.length > 14 ? node.name.slice(0, 12) + '..' : node.name;
        ctx.fillText(label, node.sx, node.sy + r + 4);
      }

      // CPU bar
      if (node.depth > 0.5) {
        const barW = r * 1.5;
        const barH = 3;
        const barX = node.sx - barW / 2;
        const barY = node.sy + r + 16;
        ctx.fillStyle = '#1e293b';
        ctx.fillRect(barX, barY, barW, barH);
        ctx.fillStyle = node.metrics.cpu > 80 ? '#ef4444' : node.metrics.cpu > 50 ? '#f59e0b' : '#10b981';
        ctx.fillRect(barX, barY, barW * (node.metrics.cpu / 100), barH);
      }
    }

    // Title info
    ctx.fillStyle = '#ffffff40';
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'right';
    ctx.fillText(`${projected.length} nodes | ${edges.length} edges | drag to rotate | scroll to zoom`, w - 12, 20);

  }, [nodes, edges, angleX, angleY, zoom, selectedNode, hoveredNode, filterType, autoRotate]);

  // Mouse handling
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (e.button === 0) {
      setIsDragging(true);
      setDragStart({ x: e.clientX, y: e.clientY, ax: angleX, ay: angleY });
    }
  }, [angleX, angleY]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!canvasRef.current) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;

    if (isDragging) {
      const dx = e.clientX - dragStart.x;
      const dy = e.clientY - dragStart.y;
      setAngleX(dragStart.ax + dy * 0.01);
      setAngleY(dragStart.ay + dx * 0.01);
    } else {
      // Hover detection
      const w = rect.width;
      const h = rect.height;
      const distance = 5 * zoom;
      const scale = 1.5 * zoom;
      let found: TopoNode | null = null;
      for (const node of nodes) {
        const { sx, sy } = project3D(node.position.x * scale, node.position.y * scale, node.position.z * scale, angleX, angleY, distance, w, h);
        const d = Math.sqrt((mx - sx) ** 2 + (my - sy) ** 2);
        if (d < 20) { found = node; break; }
      }
      setHoveredNode(found);
    }
  }, [isDragging, dragStart, nodes, angleX, angleY, zoom]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    setZoom(prev => Math.max(0.2, Math.min(5, prev - e.deltaY * 0.001)));
  }, []);

  const handleClick = useCallback((e: React.MouseEvent) => {
    if (!canvasRef.current) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    const w = rect.width;
    const h = rect.height;
    const distance = 5 * zoom;
    const scale = 1.5 * zoom;
    let found: TopoNode | null = null;
    for (const node of nodes) {
      const { sx, sy } = project3D(node.position.x * scale, node.position.y * scale, node.position.z * scale, angleX, angleY, distance, w, h);
      const d = Math.sqrt((mx - sx) ** 2 + (my - sy) ** 2);
      if (d < 20) { found = node; break; }
    }
    setSelectedNode(found || null);
  }, [nodes, angleX, angleY, zoom]);

  const handleReset = () => {
    setAngleX(0.4);
    setAngleY(0.3);
    setZoom(1);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">3D Infrastructure Topology</h1>
          <p className="text-slate-400">Three-dimensional visualization of your infrastructure</p>
        </div>
      </div>

      {/* Stats + Controls */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-3">
          {NODE_TYPES.map(nt => (
            <div key={nt.type} className="flex items-center gap-1 text-xs">
              <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: NODE_COLORS[nt.type] }} />
              <span className="text-slate-400">{nt.icon}</span>
              <span className="text-white">{nodes.filter(n => n.type === nt.type).length}</span>
            </div>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <select value={filterType} onChange={e => setFilterType(e.target.value)}
            className="px-3 py-1.5 bg-slate-800 border border-slate-700 rounded text-xs text-white outline-none focus:border-blue-500">
            <option value="all">All Types</option>
            {NODE_TYPES.map(nt => <option key={nt.type} value={nt.type}>{nt.label}</option>)}
          </select>
          <button onClick={() => setAutoRotate(!autoRotate)}
            className={`px-3 py-1.5 text-xs rounded transition-colors ${autoRotate ? 'bg-blue-600 text-white' : 'bg-slate-700 text-slate-400'}`}>
            {autoRotate ? '⟳ Auto' : '⟳ Manual'}
          </button>
          <button onClick={handleReset}
            className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-white text-xs rounded transition-colors">Reset</button>
          <button onClick={() => toast.success('Topology refreshed')}
            className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded transition-colors">Refresh</button>
        </div>
      </div>

      {/* Main layout */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <div className="lg:col-span-3">
          <div ref={containerRef} className="relative bg-[#0a0e1a] border border-slate-700 rounded-lg overflow-hidden" style={{ minHeight: '500px' }}>
            {loading ? (
              <div className="absolute inset-0 flex items-center justify-center text-slate-400">Loading topology...</div>
            ) : (
              <canvas
                ref={canvasRef}
                className="w-full cursor-grab active:cursor-grabbing"
                style={{ minHeight: '500px' }}
                onMouseDown={handleMouseDown}
                onMouseMove={handleMouseMove}
                onMouseUp={handleMouseUp}
                onMouseLeave={handleMouseUp}
                onClick={handleClick}
                onWheel={handleWheel}
              />
            )}

            {/* Controls help */}
            <div className="absolute bottom-3 left-3 text-xs text-slate-500">
              Drag to orbit · Scroll to zoom · Click to select
            </div>
          </div>
        </div>

        {/* Detail panel + Legend */}
        <div className="space-y-4">
          {selectedNode ? (
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-white mb-3">{selectedNode.name}</h3>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-slate-400">Type</span>
                  <span className="text-white capitalize">{selectedNode.type.replace('_', ' ')}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Status</span>
                  <span style={{ color: STATUS_COLORS[selectedNode.status] }} className="font-medium capitalize">{selectedNode.status}</span>
                </div>
                <hr className="border-slate-700" />
                <p className="text-slate-400 font-semibold">Metrics</p>
                <div className="space-y-1">
                  <div className="flex justify-between">
                    <span>CPU</span>
                    <span className={selectedNode.metrics.cpu > 80 ? 'text-red-400' : selectedNode.metrics.cpu > 50 ? 'text-yellow-400' : 'text-green-400'}>{selectedNode.metrics.cpu}%</span>
                  </div>
                  <div className="w-full h-1.5 bg-slate-700 rounded-full">
                    <div className={`h-full rounded-full ${selectedNode.metrics.cpu > 80 ? 'bg-red-500' : selectedNode.metrics.cpu > 50 ? 'bg-yellow-500' : 'bg-green-500'}`}
                      style={{ width: `${selectedNode.metrics.cpu}%` }} />
                  </div>
                  <div className="flex justify-between mt-1">
                    <span>Memory</span>
                    <span className={selectedNode.metrics.memory > 80 ? 'text-red-400' : selectedNode.metrics.memory > 50 ? 'text-yellow-400' : 'text-green-400'}>{selectedNode.metrics.memory}%</span>
                  </div>
                  <div className="w-full h-1.5 bg-slate-700 rounded-full">
                    <div className={`h-full rounded-full ${selectedNode.metrics.memory > 80 ? 'bg-red-500' : selectedNode.metrics.memory > 50 ? 'bg-yellow-500' : 'bg-blue-500'}`}
                      style={{ width: `${selectedNode.metrics.memory}%` }} />
                  </div>
                  <div className="flex justify-between mt-1">
                    <span>Load</span>
                    <span className="text-white">{selectedNode.metrics.load.toFixed(1)}</span>
                  </div>
                </div>
                <hr className="border-slate-700" />
                {Object.entries(selectedNode.metadata).map(([k, v]) => (
                  <div key={k} className="flex justify-between">
                    <span className="text-slate-400 capitalize">{k.replace('_', ' ')}</span>
                    <span className="text-slate-300">{v}</span>
                  </div>
                ))}
                <hr className="border-slate-700" />
                <div className="text-slate-500">Position: ({selectedNode.position.x.toFixed(1)}, {selectedNode.position.y.toFixed(1)}, {selectedNode.position.z.toFixed(1)})</div>
                {/* Connected edges */}
                <p className="text-slate-400 font-semibold mt-2">Connections</p>
                {edges.filter(e => e.source === selectedNode.id || e.target === selectedNode.id).map(e => {
                  const peer = e.source === selectedNode.id ? nodes.find(n => n.id === e.target) : nodes.find(n => n.id === e.source);
                  return (
                    <div key={e.id} className="flex items-center justify-between text-xs">
                      <span className="text-slate-300">{peer?.name || e.target}</span>
                      <span className={`text-xs ${e.status === 'active' ? 'text-green-400' : e.status === 'degraded' ? 'text-yellow-400' : 'text-red-400'}`}>
                        {e.latency_ms}ms
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 text-center text-slate-500 text-sm">
              Click a node to see details
            </div>
          )}

          {/* Legend */}
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-white mb-3">Legend</h3>
            <div className="space-y-2 text-xs">
              <p className="text-slate-400 font-medium mb-1">Node Types</p>
              {NODE_TYPES.map(nt => (
                <div key={nt.type} className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: NODE_COLORS[nt.type] }} />
                  <span className="text-slate-300">{nt.icon} {nt.label}</span>
                </div>
              ))}
              <p className="text-slate-400 font-medium mt-3 mb-1">Status</p>
              {Object.entries(STATUS_COLORS).map(([s, c]) => (
                <div key={s} className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: c }} />
                  <span className="text-slate-300 capitalize">{s}</span>
                </div>
              ))}
              <p className="text-slate-400 font-medium mt-3 mb-1">Edges</p>
              {(['active', 'degraded', 'down'] as const).map(s => (
                <div key={s} className="flex items-center gap-2">
                  <div className="w-4 h-0.5" style={{ backgroundColor: s === 'active' ? '#3b82f6' : s === 'degraded' ? '#f59e0b' : '#ef4444' }} />
                  <span className="text-slate-300 capitalize">{s}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function lightenColor(hex: string, percent: number): string {
  const num = parseInt(hex.replace('#', ''), 16);
  const r = Math.min(255, (num >> 16) + percent);
  const g = Math.min(255, ((num >> 8) & 0x00FF) + percent);
  const b = Math.min(255, (num & 0x0000FF) + percent);
  return `rgb(${r},${g},${b})`;
}