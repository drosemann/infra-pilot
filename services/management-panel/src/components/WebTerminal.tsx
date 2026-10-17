import { useEffect, useRef, useState } from 'react';
import { Terminal as TerminalIcon, Maximize2, Minimize2 } from 'lucide-react';
import { useWebSocket } from '../hooks/useWebSocket.ts';
import type { WsServerMessage } from '../hooks/useWebSocket.ts';

interface WebTerminalProps {
  appId: string;
  containerId?: string;
}

export function WebTerminal({ appId, containerId }: WebTerminalProps) {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [lines, setLines] = useState<string[]>(['Connecting to container...']);
  const [input, setInput] = useState('');
  const endRef = useRef<HTMLDivElement>(null);
  const append = (line: string) => setLines((prev) => [...prev.slice(-500), line]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [lines]);

  const { status, send } = useWebSocket({
    appId,
    mode: 'logs',
    enabled: Boolean(containerId),
    autoSubscribeLogs: true,
    onMessage: (msg: WsServerMessage) => {
      switch (msg.type) {
        case 'log':
          append(String(msg.data ?? ''));
          break;
        case 'log_end':
          append('--- Log stream ended ---');
          break;
        case 'subscribed':
          append('--- Log stream started ---');
          break;
        case 'exec_result': {
          const output = String(msg.output ?? '');
          for (const line of output.split('\n')) {
            if (line.length > 0) append(line);
          }
          if (msg.error) append(`--- ${String(msg.error)} ---`);
          break;
        }
        case 'error':
          append(`--- ${String(msg.message ?? msg.code ?? 'error')} ---`);
          break;
        default:
          break;
      }
    },
    onClose: ({ reason, willRetry }) => {
      append(willRetry ? `--- Disconnected (${reason}); reconnecting... ---` : `--- ${reason} ---`);
    },
  });

  const sendCommand = (e: React.FormEvent) => {
    e.preventDefault();
    const command = input.trim();
    if (!command) return;
    setLines((prev) => [...prev.slice(-500), `$ ${command}`]);
    if (!send({ type: 'exec', appId, command })) {
      append('--- Not connected ---');
    }
    setInput('');
  };

  return (
    <div className={`rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden ${isFullscreen ? 'fixed inset-4 z-50' : ''}`}>
      <div className="flex items-center justify-between px-4 py-2 bg-gray-900 text-gray-300 text-xs">
        <span className="flex items-center gap-2">
          <TerminalIcon className="w-3.5 h-3.5" /> Container Terminal
          <span className={`w-2 h-2 rounded-full ${status === 'open' ? 'bg-green-500' : status === 'error' ? 'bg-red-500' : 'bg-yellow-500'}`} />
        </span>
        <button onClick={() => setIsFullscreen(!isFullscreen)} className="hover:text-white">
          {isFullscreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
        </button>
      </div>
      <div className="bg-black p-4 font-mono text-sm text-green-400 h-64 overflow-y-auto" style={{ background: '#0a0a0a' }}>
        {lines.map((line, i) => <div key={i}>{line}</div>)}
        <div ref={endRef} />
      </div>
      <form onSubmit={sendCommand} className="flex bg-gray-900 border-t border-gray-800">
        <span className="px-3 py-2 text-green-400 font-mono text-sm">$</span>
        <input value={input} onChange={e => setInput(e.target.value)} className="flex-1 bg-transparent px-2 py-2 text-sm text-green-400 font-mono outline-none" placeholder="Type a command..." />
      </form>
    </div>
  );
}
