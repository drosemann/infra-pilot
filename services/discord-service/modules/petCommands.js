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

// Care hints: deterministic nudges derived from the creature's real state.
// Shown on demand only (no proactive DMs) so the bot can never spam.
const CARE_HINTS = {
  thriving: 'Keep doing what you are doing. Backups passing, deploys fresh.',
  content: 'Healthy and calm. No action needed.',
  sleepy: 'Idle for a long stretch. If this should serve traffic, check routing.',
  hungry: 'No successful deploy for a while — feed it an update and rebuild the image.',
  sick: 'Check restarts and healthcheck output, then look at recent logs.',
  stressed: 'CPU or memory pressure is high — check limits and traffic spikes.',
  sad: 'A vital dipped. Open "why does it feel like this?" in the panel.',
  ghost: 'Down for hours unacknowledged. Resurrect it, then find out why nobody noticed.',
};

function careHint(mood) {
  return CARE_HINTS[mood] || 'Unknown mood. Check the panel.';
}

function fleetBase() {
  return (process.env.ORCHESTRATOR_URL || 'http://orchestrator-agent:8500').replace(/\/$/, '');
}

async function fetchJson(path) {
  const headers = {};
  if (process.env.FEDERATION_API_TOKEN) {
    headers.Authorization = `Bearer ${process.env.FEDERATION_API_TOKEN}`;
  }
  const res = await fetch(`${fleetBase()}${path}`, { headers, signal: AbortSignal.timeout(8000) });
  if (!res.ok) throw new Error(`fleet API ${res.status}`);
  return res.json();
}

// Discord embed descriptions cap at 4096 chars; split long fleets across pages.
function paginateLines(lines, limit = 4000) {
  const pages = [];
  let current = '';
  for (const line of lines) {
    if ((current + line + '\n').length > limit && current) {
      pages.push(current);
      current = '';
    }
    current += `${line}\n`;
  }
  if (current) pages.push(current);
  return pages.length ? pages : ['No creatures yet.'];
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
      const entries = creatures.map((c) => `${MOOD_EMOJI[c.mood] || '❓'} **${c.display_name}** \`(${c.workload_id})\` — ${c.mood} (${c.stage})`);
      const pages = paginateLines(entries);
      await interaction.editReply({ embeds: [new EmbedBuilder().setTitle('Living Fleet').setDescription(pages[0]).setColor('#7c3aed')] });
      for (const page of pages.slice(1)) {
        await interaction.followUp({ embeds: [new EmbedBuilder().setTitle('Living Fleet (cont.)').setDescription(page).setColor('#7c3aed')], ephemeral: true });
      }
      return null;
    }
    if (interaction.commandName === 'pet-status') {
      const workload = interaction.options.getString('workload', true);
      const c = await fetchJson(`/api/v1/fleet/creatures/${encodeURIComponent(workload)}`);
      const vitals = Object.entries(c.vitals || {}).map(([k, v]) => `${k}: ${v === null ? 'unknown' : v}`).join('\n');
      const embed = new EmbedBuilder()
        .setTitle(`${MOOD_EMOJI[c.mood] || '❓'} ${c.display_name}`)
        .setDescription(`Mood: **${c.mood}**\nStage: ${c.stage}\n\n${vitals}\n\n💡 ${careHint(c.mood)}`)
        .setColor('#7c3aed');
      return interaction.editReply({ embeds: [embed] });
    }
  } catch (error) {
    console.error('[PetCommands] failed:', error.message);
    return interaction.editReply({ content: 'The fleet is unreachable right now (orchestrator down or feature disabled).' });
  }
}

// careHint is exported so AlertManager/Monitoring can reuse the same
// deterministic copy if proactive nudges are added later (with dedup).
module.exports = { toSpec, isParsed, handle, careHint, MOOD_EMOJI };
