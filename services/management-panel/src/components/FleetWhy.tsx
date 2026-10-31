/**
 * FleetWhy — "Why does it feel like this?" detail view for a creature.
 * Renders the per-vital scores and contributing raw signals straight from
 * the fleet API explanation trace. Collapsed by default; no fetching here.
 */

import type { CreatureView } from './FleetPet';

function formatSignalValue(value: unknown): string {
  if (value === null || value === undefined) return 'unknown';
  if (typeof value === 'boolean') return value ? 'yes' : 'no';
  if (typeof value === 'number') return Number.isInteger(value) ? String(value) : value.toFixed(1);
  return String(value);
}

export function FleetWhy({ creature }: { creature: CreatureView }) {
  const rows = creature.explanation ?? [];
  if (rows.length === 0) return null;
  return (
    <details className="fleet-why mt-2 text-xs text-slate-400">
      <summary className="cursor-pointer select-none hover:text-slate-200">
        Why does {creature.display_name} feel {creature.mood}?
      </summary>
      <ul className="mt-1 space-y-1 pl-1">
        {rows.map((row) => (
          <li key={row.vital}>
            <span className="font-semibold text-slate-300">{row.vital}</span>
            {': '}
            {row.score === null ? 'unknown' : row.score}
            {Object.keys(row.signals).length > 0 && (
              <span className="text-slate-500">
                {' ('}
                {Object.entries(row.signals)
                  .map(([k, v]) => `${k}=${formatSignalValue(v)}`)
                  .join(', ')}
                {')'}
              </span>
            )}
          </li>
        ))}
      </ul>
    </details>
  );
}
