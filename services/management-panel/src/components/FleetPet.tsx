/**
 * FleetPet (Living Fleet barecode) — renders one creature's mood + stage.
 *
 * Mounted in AppCard.tsx next to the app name; data comes from the
 * orchestrator fleet API proxied through the panel server
 * (GET /api/fleet/creatures). Do NOT fetch the orchestrator directly
 * from the browser.
 */

export type CreatureMood =
  | 'thriving'
  | 'content'
  | 'sleepy'
  | 'hungry'
  | 'sick'
  | 'stressed'
  | 'sad'
  | 'ghost';

export interface CreatureExplanation {
  vital: string;
  score: number | null;
  signals: Record<string, unknown>;
}

export interface CreatureView {
  workload_id: string;
  display_name: string;
  mood: CreatureMood;
  stage: string;
  vitals: Record<string, number | null>;
  explanation?: CreatureExplanation[];
  retired: boolean;
}

const MOOD_EMOJI: Record<CreatureMood, string> = {
  thriving: '🌟',
  content: '😊',
  sleepy: '😴',
  hungry: '🍽️',
  sick: '🤒',
  stressed: '😰',
  sad: '😢',
  ghost: '👻',
};

export function FleetPet({ creature }: { creature: CreatureView }) {
  const emoji = MOOD_EMOJI[creature.mood] ?? '❓';
  return (
    <span
      role="img"
      className="fleet-pet"
      title={`${creature.display_name} is ${creature.mood} (${creature.stage})`}
      aria-label={`${creature.display_name}, mood ${creature.mood}, stage ${creature.stage}`}
    >
      <span aria-hidden="true">{emoji}</span>
    </span>
  );
}
