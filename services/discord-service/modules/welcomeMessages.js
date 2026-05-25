const { EmbedBuilder, PermissionFlagsBits } = require('discord.js');
const fs = require('fs');
const path = require('path');

class WelcomeMessages {
    constructor(client) {
        this.client = client;
        this.configs = new Map();
        this.loadConfigs();
    }

    loadConfigs() {
        const filePath = path.join(__dirname, '..', 'welcome_config.json');
        try {
            if (fs.existsSync(filePath)) {
                this.configs = new Map(Object.entries(JSON.parse(fs.readFileSync(filePath, 'utf8'))));
            }
        } catch (e) {
            console.error('Error loading welcome configs:', e);
        }
    }

    saveConfigs() {
        const filePath = path.join(__dirname, '..', 'welcome_config.json');
        try {
            fs.writeFileSync(filePath, JSON.stringify(Object.fromEntries(this.configs), null, 2));
        } catch (e) {
            console.error('Error saving welcome configs:', e);
        }
    }

    initialize(client) {
        // ready
    }

    async handleCommand(interaction) {
        if (interaction.commandName !== 'welcome') return;

        const sub = interaction.options.getSubcommand();

        if (sub === 'set') {
            await this.setWelcome(interaction);
        } else if (sub === 'preview') {
            await this.previewWelcome(interaction);
        }
    }

    async setWelcome(interaction) {
        if (!interaction.member.permissions.has(PermissionFlagsBits.Administrator)) {
            return interaction.reply({ content: '❌ Nur Administratoren können die Begrüßung konfigurieren.', ephemeral: true });
        }

        const channel = interaction.options.getChannel('channel');
        const message = interaction.options.getString('message');
        const dm = interaction.options.getBoolean('dm') || false;

        if (channel.type !== 0) {
            return interaction.reply({ content: '❌ Bitte wähle einen Textkanal.', ephemeral: true });
        }

        this.configs.set(interaction.guildId, {
            channelId: channel.id,
            message,
            dm,
            enabled: true
        });

        this.saveConfigs();

        await interaction.reply({ content: `✅ Willkommensnachricht konfiguriert! Kanal: ${channel}${dm ? ' (auch per DM)' : ''}`, ephemeral: true });
    }

    async handleMemberJoin(member) {
        const config = this.configs.get(member.guild.id);
        if (!config || !config.enabled) return;

        const processedMessage = config.message
            .replace(/{user}/g, member.toString())
            .replace(/{server}/g, member.guild.name)
            .replace(/{memberCount}/g, member.guild.memberCount.toString());

        const embed = new EmbedBuilder()
            .setTitle(`👋 Willkommen auf ${member.guild.name}!`)
            .setDescription(processedMessage)
            .setColor('#6C5CE7')
            .setThumbnail(member.user.displayAvatarURL({ dynamic: true }))
            .addFields([
                { name: 'Mitglied #', value: member.guild.memberCount.toString(), inline: true },
                { name: 'Account erstellt', value: member.user.createdAt.toLocaleDateString('de-DE'), inline: true }
            ])
            .setTimestamp();

        const channel = member.guild.channels.cache.get(config.channelId);
        if (channel) {
            await channel.send({ embeds: [embed] }).catch(() => {});
        }

        if (config.dm) {
            try {
                await member.send({ embeds: [
                    new EmbedBuilder()
                        .setTitle(`👋 Willkommen auf ${member.guild.name}!`)
                        .setDescription(processedMessage)
                        .setColor('#6C5CE7')
                        .setTimestamp()
                ]});
            } catch (e) {}
        }
    }

    async previewWelcome(interaction) {
        const config = this.configs.get(interaction.guildId);
        if (!config) {
            return interaction.reply({ content: '❌ Keine Willkommensnachricht konfiguriert.', ephemeral: true });
        }

        const processedMessage = config.message
            .replace(/{user}/g, interaction.user.toString())
            .replace(/{server}/g, interaction.guild.name)
            .replace(/{memberCount}/g, interaction.guild.memberCount.toString());

        const embed = new EmbedBuilder()
            .setTitle(`👋 Willkommen auf ${interaction.guild.name}!`)
            .setDescription(processedMessage)
            .setColor('#6C5CE7')
            .setThumbnail(interaction.user.displayAvatarURL({ dynamic: true }))
            .addFields([
                { name: 'Mitglied #', value: interaction.guild.memberCount.toString(), inline: true },
                { name: 'Account erstellt', value: interaction.user.createdAt.toLocaleDateString('de-DE'), inline: true }
            ])
            .setTimestamp();

        await interaction.reply({ embeds: [embed], ephemeral: true });
    }

    async handleModalSubmit(interaction) {
        // reserved
    }
}

module.exports = WelcomeMessages;
