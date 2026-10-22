/**
 * @file Living Fleet pet commands (barecode). Read-only creature views.
 * Fetches from the orchestrator fleet API; never touches the panel DB.
 */

const { EmbedBuilder } = require('discord.js');

const COMMAND_SPECS = [
  { name: 'pet', description: 'Living Fleet creature commands', options: [{ name: 'list', description: 'List all creatures with mood and stage', type: 1 }] },
  { name: 'pet-status', description: 'Show one creature with vitals', options: [{ name: 'workload', description: 'Workload ID of the creature', type: 3, required: true }] },
];

const MOOD_EMOJI = {
  thriving: '🌟', content: '😊', sleepy: '😴', hungry: '🍽️',
  sick: '🤒', stressed: '😰', sad: '😢', ghost: '👻',
};

function fleetBase() {
  return (process.env.ORCHESTRATOR_URL || 'http://orchestrator-agent:8500').replace(/\/$/, '');
}

async function fetchJson(path) {
  const res = await fetch(`${fleetBase()}${path}`, { signal: AbortSignal.timeout(8000) });
  if (!res.ok) throw new Error(`fleet API ${res.status}`);
  return res.json();
}

function toSpec() {
  return COMMAND_SPECS;
}

function isParsed(name) {
  return COMMAND_SPECS.some((c) => c.name === name);
}

async function handle(interaction) {
  await interaction.deferReply({ ephemeral: true });
  try {
    if (interaction.commandName === 'pet') {
      const creatures = await fetchJson('/api/v1/fleet/creatures');
      if (!creatures.length) return interaction.editReply({ content: 'No creatures yet. They are born when a workload is first seen healthy.' });
      const lines = creatures.map((c) => `${MOOD_EMOJI[c.mood] || '❓'} **${c.display_name}** — ${c.mood} (${c.stage})`).join('\n');
      const embed = new EmbedBuilder().setTitle('Living Fleet').setDescription(lines).setColor('#7c3aed');
      return interaction.editReply({ embeds: [embed] });
    }
    if (interaction.commandName === 'pet-status') {
      const workload = interaction.options.getString('workload', true);
      const c = await fetchJson(`/api/v1/fleet/creatures/${encodeURIComponent(workload)}`);
      const vitals = Object.entries(c.vitals || {}).map(([k, v]) => `${k}: ${v === null ? 'unknown' : v}`).join('\n');
      const embed = new EmbedBuilder()
        .setTitle(`${MOOD_EMOJI[c.mood] || '❓'} ${c.display_name}`)
        .setDescription(`Mood: **${c.mood}**\nStage: ${c.stage}\n\n${vitals}`)
        .setColor('#7c3aed');
      return interaction.editReply({ embeds: [embed] });
    }
  } catch (error) {
    console.error('[PetCommands] failed:', error.message);
    return interaction.editReply({ content: 'The fleet is unreachable right now (orchestrator down or feature disabled).' });
  }
}

module.exports = { toSpec, isParsed, handle };
