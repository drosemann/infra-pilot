const { EmbedBuilder } = require('discord.js');
const fs = require('fs');
const path = require('path');

class MessageLogger {
    constructor(client) {
        this.client = client;
        this.logChannels = new Map();
        this.messageCache = new Map();
        this.loadConfig();
    }

    loadConfig() {
        const filePath = path.join(__dirname, '..', 'message_log_config.json');
        try {
            if (fs.existsSync(filePath)) {
                const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
                for (const [guildId, channelId] of Object.entries(data)) {
                    this.logChannels.set(guildId, channelId);
                }
            }
        } catch (e) {
            console.error('Error loading message log config:', e);
        }
    }

    saveConfig() {
        const filePath = path.join(__dirname, '..', 'message_log_config.json');
        try {
            fs.writeFileSync(filePath, JSON.stringify(Object.fromEntries(this.logChannels), null, 2));
        } catch (e) {
            console.error('Error saving message log config:', e);
        }
    }

    initialize(client) {
        // Auto-create log channel if configured
    }

    trackMessage(message) {
        if (message.author.bot) return;
        this.messageCache.set(message.id, {
            content: message.content,
            authorId: message.author.id,
            authorTag: message.author.tag,
            channelId: message.channel.id,
            channelName: message.channel.name,
            createdAt: message.createdAt,
            attachments: message.attachments.map(a => a.url),
            embeds: message.embeds.length
        });

        if (this.messageCache.size > 500) {
            const firstKey = this.messageCache.keys().next().value;
            this.messageCache.delete(firstKey);
        }
    }

    async handleMessageDelete(message) {
        if (message.author?.bot) return;

        const guild = message.guild;
        if (!guild) return;

        const logChannelId = this.logChannels.get(guild.id);
        if (!logChannelId) return;

        const logChannel = guild.channels.cache.get(logChannelId);
        if (!logChannel) return;

        const cached = this.messageCache.get(message.id) || {
            content: message.content || 'Unbekannt',
            authorId: message.author?.id || 'Unbekannt',
            authorTag: message.author?.tag || 'Unbekannt',
            channelName: message.channel?.name || 'Unbekannt',
            attachments: []
        };

        const embed = new EmbedBuilder()
            .setTitle('🗑️ Nachricht gelöscht')
            .setDescription(`**Autor:** <@${cached.authorId}> (${cached.authorTag})\n**Kanal:** #${cached.channelName}\n**Inhalt:**\n${cached.content.substring(0, 1000)}`)
            .setColor('#ff4444')
            .setTimestamp();

        if (cached.attachments && cached.attachments.length > 0) {
            embed.addFields({ name: 'Anhänge', value: cached.attachments.join('\n'), inline: false });
        }

        await logChannel.send({ embeds: [embed] }).catch(() => {});

        this.messageCache.delete(message.id);
    }
}

module.exports = MessageLogger;
