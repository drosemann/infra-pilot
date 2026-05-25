const { EmbedBuilder, PermissionFlagsBits } = require('discord.js');
const fs = require('fs');
const path = require('path');

class MessageFilter {
    constructor(client) {
        this.client = client;
        this.configs = new Map();
        this.badWords = new Map();
        this.whitelistedDomains = new Map();
        this.spamTracker = new Map();
        this.loadConfig();
    }

    loadConfig() {
        const filePath = path.join(__dirname, '..', 'filter_config.json');
        try {
            if (fs.existsSync(filePath)) {
                const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
                for (const [guildId, config] of Object.entries(data)) {
                    this.configs.set(guildId, config);
                    this.badWords.set(guildId, new Set(config.badWords || []));
                    this.whitelistedDomains.set(guildId, new Set(config.whitelistedDomains || []));
                }
            }
        } catch (e) {
            console.error('Error loading filter config:', e);
        }
    }

    saveConfig() {
        const filePath = path.join(__dirname, '..', 'filter_config.json');
        try {
            const data = {};
            for (const [guildId, config] of this.configs) {
                data[guildId] = {
                    ...config,
                    badWords: Array.from(this.badWords.get(guildId) || []),
                    whitelistedDomains: Array.from(this.whitelistedDomains.get(guildId) || [])
                };
            }
            fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
        } catch (e) {
            console.error('Error saving filter config:', e);
        }
    }

    getConfig(guildId) {
        if (!this.configs.has(guildId)) {
            this.configs.set(guildId, {
                action: 'delete',
                logChannelId: null,
                enabled: true
            });
            this.badWords.set(guildId, new Set());
            this.whitelistedDomains.set(guildId, new Set());
        }
        return this.configs.get(guildId);
    }

    async handleCommand(interaction) {
        if (interaction.commandName !== 'filter') return;

        const sub = interaction.options.getSubcommand();

        if (sub === 'config') {
            await this.configureFilter(interaction);
        } else if (sub === 'badword') {
            await this.addBadWord(interaction);
        } else if (sub === 'badword_remove') {
            await this.removeBadWord(interaction);
        } else if (sub === 'whitelist') {
            await this.whitelistDomain(interaction);
        }
    }

    async configureFilter(interaction) {
        if (!interaction.member.permissions.has(PermissionFlagsBits.Administrator)) {
            return interaction.reply({ content: '❌ Nur Administratoren können den Filter konfigurieren.', ephemeral: true });
        }

        const action = interaction.options.getString('action');
        const logChannel = interaction.options.getChannel('log_channel');

        const config = this.getConfig(interaction.guildId);
        config.action = action;
        if (logChannel) config.logChannelId = logChannel.id;
        this.saveConfig();

        await interaction.reply({ content: `✅ Filter konfiguriert. Aktion: ${action}${logChannel ? `, Log-Kanal: ${logChannel}` : ''}`, ephemeral: true });
    }

    async addBadWord(interaction) {
        if (!interaction.member.permissions.has(PermissionFlagsBits.Administrator)) {
            return interaction.reply({ content: '❌ Nur Administratoren können Wörter hinzufügen.', ephemeral: true });
        }

        const word = interaction.options.getString('word').toLowerCase();
        const words = this.badWords.get(interaction.guildId);
        if (!words) {
            this.badWords.set(interaction.guildId, new Set([word]));
        } else {
            words.add(word);
        }
        this.saveConfig();

        await interaction.reply({ content: `✅ Wort "${word}" wurde zur Filterliste hinzugefügt.`, ephemeral: true });
    }

    async removeBadWord(interaction) {
        if (!interaction.member.permissions.has(PermissionFlagsBits.Administrator)) {
            return interaction.reply({ content: '❌ Nur Administratoren können Wörter entfernen.', ephemeral: true });
        }

        const word = interaction.options.getString('word').toLowerCase();
        const words = this.badWords.get(interaction.guildId);
        if (words && words.has(word)) {
            words.delete(word);
            this.saveConfig();
            await interaction.reply({ content: `✅ Wort "${word}" wurde aus der Filterliste entfernt.`, ephemeral: true });
        } else {
            await interaction.reply({ content: `❌ Wort "${word}" nicht in der Filterliste.`, ephemeral: true });
        }
    }

    async whitelistDomain(interaction) {
        if (!interaction.member.permissions.has(PermissionFlagsBits.Administrator)) {
            return interaction.reply({ content: '❌ Nur Administratoren können Domains whitelisten.', ephemeral: true });
        }

        const domain = interaction.options.getString('domain').toLowerCase();
        const domains = this.whitelistedDomains.get(interaction.guildId);
        if (!domains) {
            this.whitelistedDomains.set(interaction.guildId, new Set([domain]));
        } else {
            domains.add(domain);
        }
        this.saveConfig();

        await interaction.reply({ content: `✅ Domain "${domain}" wurde zur Whitelist hinzugefügt.`, ephemeral: true });
    }

    async checkMessage(message) {
        if (message.author.bot) return;
        if (!message.guild) return;

        const config = this.getConfig(message.guild.id);
        if (!config.enabled) return;

        const content = message.content.toLowerCase();

        if (this.checkSpam(message, config)) return;

        const badWords = this.badWords.get(message.guild.id);
        if (badWords) {
            for (const word of badWords) {
                if (content.includes(word)) {
                    await this.takeAction(message, config, `Enthält gefiltertes Wort: ${word}`);
                    return;
                }
            }
        }

        const urlRegex = /https?:\/\/[^\s]+/g;
        const urls = message.content.match(urlRegex);
        if (urls) {
            const whitelisted = this.whitelistedDomains.get(message.guild.id) || new Set();
            for (const url of urls) {
                try {
                    const domain = new URL(url).hostname.replace('www.', '');
                    if (!whitelisted.has(domain) && !whitelisted.has('*')) {
                        await this.takeAction(message, config, `Nicht-whitelistete Domain: ${domain}`);
                        return;
                    }
                } catch (e) {}
            }
        }
    }

    checkSpam(message, config) {
        const now = Date.now();
        const userId = message.author.id;

        if (!this.spamTracker.has(userId)) {
            this.spamTracker.set(userId, []);
        }

        const timestamps = this.spamTracker.get(userId);
        timestamps.push(now);

        const recent = timestamps.filter(t => now - t < 5000);
        this.spamTracker.set(userId, recent);

        if (recent.length >= 5) {
            this.takeAction(message, config, 'Spam erkannt');
            return true;
        }
        return false;
    }

    async takeAction(message, config, reason) {
        try {
            await message.delete();
        } catch (e) {}

        if (config.action === 'warn') {
            await message.author.send(`⚠️ **Nachricht gelöscht:** ${reason}`).catch(() => {});
        } else if (config.action === 'timeout') {
            const member = await message.guild.members.fetch(message.author.id).catch(() => null);
            if (member) {
                await member.timeout(600000, reason).catch(() => {});
            }
        }

        if (config.logChannelId) {
            const logChannel = message.guild.channels.cache.get(config.logChannelId);
            if (logChannel) {
                const embed = new EmbedBuilder()
                    .setTitle('🚫 Gefilterte Nachricht')
                    .setDescription(`**Benutzer:** ${message.author}\n**Kanal:** ${message.channel}\n**Grund:** ${reason}\n**Inhalt:** ${message.content.substring(0, 500)}`)
                    .setColor('#ff0000')
                    .setTimestamp();

                await logChannel.send({ embeds: [embed] }).catch(() => {});
            }
        }
    }

    async handleMessageUpdate(oldMessage, newMessage) {
        if (oldMessage.content !== newMessage.content) {
            await this.checkMessage(newMessage);
        }
    }

    async handleButton(interaction) {
        // reserved
    }
}

module.exports = MessageFilter;
