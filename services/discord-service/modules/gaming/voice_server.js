const { SlashCommandBuilder, EmbedBuilder } = require('discord.js');

module.exports = {
  name: 'voice_server',
  description: 'Voice Server commands',
  async execute(interaction) {
    const embed = new EmbedBuilder()
      .setColor(0xFF6600)
      .setTitle('Voice Server')
      .setDescription('Gaming Voice Server management and monitoring.')
      .addFields(
        { name: 'Status', value: 'Online', inline: true },
        { name: 'Players', value: 'Active', inline: true },
        { name: 'Latency', value: '12ms', inline: true },
      )
      .setTimestamp();
    await interaction.reply({ embeds: [embed] });
  }
};
