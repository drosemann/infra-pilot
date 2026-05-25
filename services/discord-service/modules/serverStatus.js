const { EmbedBuilder, ActionRowBuilder, ButtonBuilder, ButtonStyle } = require('discord.js');
const si = require('systeminformation');
const axios = require('axios');

class ServerStatus {
    constructor(client) {
        this.client = client;
        this.widgets = new Map();
        this.updateIntervals = new Map();
    }

    initialize(client) {
        for (const [channelId, config] of this.widgets) {
            this.startWidgetUpdate(channelId, config);
        }
    }

    async handleCommand(interaction) {
        if (interaction.commandName !== 'status') return;

        const sub = interaction.options.getSubcommand();
        if (sub === 'widget') {
            await this.createWidget(interaction);
        } else if (sub === 'info') {
            await this.showStatus(interaction);
        }
    }

    async createWidget(interaction) {
        if (!interaction.member.permissions.has('ADMINISTRATOR')) {
            return interaction.reply({ content: '❌ Du benötigst Administrator-Rechte.', ephemeral: true });
        }

        await interaction.deferReply();

        const embed = await this.createStatusEmbed();
        const row = new ActionRowBuilder().addComponents(
            new ButtonBuilder().setCustomId('refresh_status').setLabel('Refresh').setStyle(ButtonStyle.Primary).setEmoji('🔄')
        );

        const msg = await interaction.channel.send({ embeds: [embed], components: [row] });
        this.widgets.set(interaction.channelId, { messageId: msg.id, channelId: interaction.channelId });
        this.startWidgetUpdate(interaction.channelId);

        await interaction.editReply({ content: '✅ Status-Widget erstellt!', ephemeral: true });
    }

    startWidgetUpdate(channelId) {
        if (this.updateIntervals.has(channelId)) {
            clearInterval(this.updateIntervals.get(channelId));
        }
        const interval = setInterval(() => this.updateWidget(channelId), 30000);
        this.updateIntervals.set(channelId, interval);
    }

    async updateWidget(channelId) {
        const config = this.widgets.get(channelId);
        if (!config) return;

        try {
            const channel = await this.client.channels.fetch(channelId).catch(() => null);
            if (!channel) return;

            const msg = await channel.messages.fetch(config.messageId).catch(() => null);
            if (!msg) {
                this.widgets.delete(channelId);
                clearInterval(this.updateIntervals.get(channelId));
                return;
            }

            const embed = await this.createStatusEmbed();
            await msg.edit({ embeds: [embed] });
        } catch (e) {
            console.error('Status widget update error:', e.message);
        }
    }

    async createStatusEmbed() {
        try {
            const [cpu, mem, os, load, time] = await Promise.all([
                si.cpu(),
                si.mem(),
                si.osInfo(),
                si.currentLoad(),
                si.time()
            ]);

            const uptime = this.formatUptime(time.uptime);

            return new EmbedBuilder()
                .setTitle('🖥️ Server Status')
                .setColor('#6C5CE7')
                .addFields([
                    { name: 'CPU', value: `${cpu.manufacturer} ${cpu.brand}\nAuslastung: ${load.currentLoad.toFixed(1)}%`, inline: true },
                    { name: 'RAM', value: `Belegt: ${this.formatBytes(mem.used)}\nGesamt: ${this.formatBytes(mem.total)}`, inline: true },
                    { name: 'System', value: `${os.platform} ${os.release}`, inline: true },
                    { name: 'Uptime', value: uptime, inline: true },
                    { name: 'Online since', value: time.timezone, inline: true }
                ])
                .setFooter({ text: 'Aktualisiert alle 30s' })
                .setTimestamp();
        } catch (e) {
            return new EmbedBuilder()
                .setTitle('❌ Status-Fehler')
                .setDescription('Konnte Systeminformationen nicht abrufen.')
                .setColor('#ff0000');
        }
    }

    async showStatus(interaction) {
        await interaction.deferReply();
        const embed = await this.createStatusEmbed();
        await interaction.editReply({ embeds: [embed] });
    }

    async handleButton(interaction) {
        if (interaction.customId !== 'refresh_status') return;
        await interaction.deferUpdate();
        await this.updateWidget(interaction.channelId);
    }

    formatBytes(bytes) {
        if (bytes === 0) return '0 B';
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)), 10);
        return (bytes / Math.pow(1024, i)).toFixed(1) + ' ' + sizes[i];
    }

    formatUptime(seconds) {
        const d = Math.floor(seconds / 86400);
        const h = Math.floor((seconds % 86400) / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        const parts = [];
        if (d > 0) parts.push(`${d}d`);
        if (h > 0) parts.push(`${h}h`);
        parts.push(`${m}m`);
        return parts.join(' ');
    }
}

module.exports = ServerStatus;
