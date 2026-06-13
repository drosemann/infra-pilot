const { SlashCommandBuilder, EmbedBuilder } = require('discord.js');

module.exports = {
  name: 'live_spectate',
  description: 'Live Spectate commands',
  async execute(interaction) {
    const embed = new EmbedBuilder()
      .setColor(0xFF6600)
      .setTitle('Live Spectate')
      .setDescription('Gaming Live Spectate management and monitoring.')
      .addFields(
        { name: 'Status', value: 'Online', inline: true },
        { name: 'Players', value: 'Active', inline: true },
        { name: 'Latency', value: '12ms', inline: true },
      )
      .setTimestamp();
    await interaction.reply({ embeds: [embed] });
  }
};
