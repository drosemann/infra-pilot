const { EmbedBuilder } = require('discord.js');
const fs = require('fs');
const path = require('path');

class ActivityTracker {
    constructor(client) {
        this.client = client;
        this.data = new Map();
        this.voiceSessions = new Map();
        this.loadData();
    }

    loadData() {
        const filePath = path.join(__dirname, '..', 'activity_data.json');
        try {
            if (fs.existsSync(filePath)) {
                const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
                for (const [guildId, users] of Object.entries(data)) {
                    this.data.set(guildId, new Map(Object.entries(users)));
                }
            }
        } catch (e) {
            console.error('Error loading activity data:', e);
        }
    }

    saveData() {
        const filePath = path.join(__dirname, '..', 'activity_data.json');
        try {
            const data = {};
            for (const [guildId, users] of this.data) {
                data[guildId] = Object.fromEntries(users);
            }
            fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
        } catch (e) {
            console.error('Error saving activity data:', e);
        }
    }

    initialize(client) {
        // Periodically save
        setInterval(() => this.saveData(), 300000);
    }

    getUserData(guildId, userId) {
        if (!this.data.has(guildId)) {
            this.data.set(guildId, new Map());
        }
        const guild = this.data.get(guildId);
        if (!guild.has(userId)) {
            guild.set(userId, {
                messages: 0,
                voiceMinutes: 0,
                reactions: 0,
                lastSeen: new Date().toISOString()
            });
        }
        return guild.get(userId);
    }

    trackMessage(message) {
        if (message.author.bot) return;
        const data = this.getUserData(message.guildId, message.author.id);
        data.messages++;
        data.lastSeen = new Date().toISOString();
    }

    async handleVoiceStateUpdate(oldState, newState) {
        const userId = newState.id || oldState.id;
        const guildId = newState.guild.id || oldState.guild.id;

        if (!oldState.channelId && newState.channelId) {
            this.voiceSessions.set(`${guildId}-${userId}`, Date.now());
        } else if (oldState.channelId && !newState.channelId) {
            const startTime = this.voiceSessions.get(`${guildId}-${userId}`);
            if (startTime) {
                const minutes = (Date.now() - startTime) / 60000;
                const data = this.getUserData(guildId, userId);
                data.voiceMinutes += Math.round(minutes);
                this.voiceSessions.delete(`${guildId}-${userId}`);
            }
        }
    }

    async handleCommand(interaction) {
        if (interaction.commandName !== 'activity') return;

        const sub = interaction.options.getSubcommand();

        if (sub === 'leaderboard') {
            await this.showLeaderboard(interaction);
        } else if (sub === 'stats') {
            await this.showStats(interaction);
        }
    }

    async showLeaderboard(interaction) {
        const guildData = this.data.get(interaction.guildId);
        if (!guildData || guildData.size === 0) {
            return interaction.reply({ content: '📊 Noch keine Aktivitätsdaten vorhanden.', ephemeral: true });
        }

        const sorted = Array.from(guildData.entries())
            .sort((a, b) => (b[1].messages + b[1].voiceMinutes) - (a[1].messages + a[1].voiceMinutes))
            .slice(0, 10);

        const embed = new EmbedBuilder()
            .setTitle('📊 Aktivitäts-Rangliste')
            .setColor('#6C5CE7')
            .setDescription('Top 10 aktivste Mitglieder')
            .setTimestamp();

        for (let i = 0; i < sorted.length; i++) {
            const [userId, data] = sorted[i];
            const total = data.messages + data.voiceMinutes;
            const user = await this.client.users.fetch(userId).catch(() => null);
            const name = user ? user.username : 'Unbekannt';

            embed.addFields({
                name: `#${i + 1} ${name}`,
                value: `💬 ${data.messages} Nachrichten | 🎤 ${data.voiceMinutes} Minuten Sprachchat | Gesamt: ${total}`,
                inline: false
            });
        }

        await interaction.reply({ embeds: [embed] });
    }

    async showStats(interaction) {
        const data = this.getUserData(interaction.guildId, interaction.user.id);

        const embed = new EmbedBuilder()
            .setTitle('📊 Deine Aktivitätsstatistiken')
            .setColor('#6C5CE7')
            .addFields([
                { name: '💬 Nachrichten', value: data.messages.toString(), inline: true },
                { name: '🎤 Sprachchat', value: `${data.voiceMinutes} Minuten`, inline: true },
                { name: 'Letzte Aktivität', value: new Date(data.lastSeen).toLocaleString('de-DE'), inline: false }
            ])
            .setTimestamp();

        await interaction.reply({ embeds: [embed] });
    }
}

module.exports = ActivityTracker;
