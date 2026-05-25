const { EmbedBuilder, PermissionFlagsBits, AttachmentBuilder } = require('discord.js');

class StatsGraphs {
    constructor(client) {
        this.client = client;
    }

    async handleCommand(interaction) {
        if (interaction.commandName !== 'statsgraph') return;

        if (!interaction.member.permissions.has(PermissionFlagsBits.Administrator)) {
            return interaction.reply({ content: '❌ Nur Administratoren können Statistiken anzeigen.', ephemeral: true });
        }

        const sub = interaction.options.getSubcommand();
        if (sub === 'members') {
            await this.showMemberGrowth(interaction);
        } else if (sub === 'messages') {
            await this.showMessageVolume(interaction);
        }
    }

    async showMemberGrowth(interaction) {
        await interaction.deferReply();

        try {
            const guild = interaction.guild;
            const members = await guild.members.fetch();
            const now = Date.now();

            const days = 30;
            const dayLabels = [];
            const countData = [];

            for (let i = days; i >= 0; i--) {
                const date = new Date(now - i * 86400000);
                dayLabels.push(date.toLocaleDateString('de-DE', { weekday: 'short', day: 'numeric' }));

                const count = members.filter(m => m.joinedAt && m.joinedAt <= date).size;
                countData.push(count);
            }

            const embed = new EmbedBuilder()
                .setTitle('📈 Mitgliederwachstum (30 Tage)')
                .setColor('#6C5CE7')
                .setDescription(
                    `**Aktuelle Mitglieder:** ${members.size}\n` +
                    `**Heute beigetreten:** ${members.filter(m => m.joinedAt && (now - m.joinedAt.getTime()) < 86400000).size}\n` +
                    `**Diese Woche:** ${members.filter(m => m.joinedAt && (now - m.joinedAt.getTime()) < 7 * 86400000).size}\n\n` +
                    '```\n' + this.createBarChart(countData, 15) + '\n```'
                )
                .setFooter({ text: 'Letzte 30 Tage' })
                .setTimestamp();

            await interaction.editReply({ embeds: [embed] });
        } catch (e) {
            await interaction.editReply({ content: `❌ Fehler: ${e.message}` });
        }
    }

    async showMessageVolume(interaction) {
        await interaction.deferReply();

        try {
            const channel = interaction.options.getChannel('channel') || interaction.channel;
            const messages = await channel.messages.fetch({ limit: 500 });

            const days = {};
            messages.forEach(m => {
                const day = m.createdAt.toLocaleDateString('de-DE');
                days[day] = (days[day] || 0) + 1;
            });

            const sorted = Object.entries(days).sort((a, b) => a[0].localeCompare(b[0])).slice(-14);

            if (sorted.length === 0) {
                return interaction.editReply({ content: '❌ Keine Nachrichtendaten verfügbar.' });
            }

            const values = sorted.map(([, count]) => count);

            const embed = new EmbedBuilder()
                .setTitle(`📊 Nachrichtenvolumen - #${channel.name}`)
                .setColor('#6C5CE7')
                .setDescription(
                    `**Nachrichten (letzte 500):** ${messages.size}\n` +
                    `**Tage mit Daten:** ${sorted.length}\n\n` +
                    '```\n' + this.createBarChart(values, 10) + '\n```'
                )
                .setFooter({ text: 'Letzte 14 Tage' })
                .setTimestamp();

            await interaction.editReply({ embeds: [embed] });
        } catch (e) {
            await interaction.editReply({ content: `❌ Fehler: ${e.message}` });
        }
    }

    createBarChart(values, barWidth) {
        if (values.length === 0) return 'Keine Daten';

        const max = Math.max(...values);
        if (max === 0) return values.map(() => '▁'.repeat(barWidth)).join('\n');

        const bars = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█'];
        return values.map(v => {
            const ratio = v / max;
            const fullBars = Math.floor(ratio * barWidth);
            const partial = (ratio * barWidth) - fullBars;
            const partialIndex = Math.floor(partial * bars.length);
            return bars[bars.length - 1].repeat(fullBars) + (partialIndex > 0 ? bars[partialIndex] : '') + ' ' + v;
        }).join('\n');
    }
}

module.exports = StatsGraphs;
