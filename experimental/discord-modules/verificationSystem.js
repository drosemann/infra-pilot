const { EmbedBuilder, ActionRowBuilder, ButtonBuilder, ButtonStyle, PermissionFlagsBits } = require('discord.js');
const fs = require('fs');
const path = require('path');

class VerificationSystem {
    constructor(client) {
        this.client = client;
        this.configs = new Map();
        this.pendingVerifications = new Map();
        this.loadConfigs();
    }

    loadConfigs() {
        const filePath = path.join(__dirname, '..', 'verification_config.json');
        try {
            if (fs.existsSync(filePath)) {
                this.configs = new Map(Object.entries(JSON.parse(fs.readFileSync(filePath, 'utf8'))));
            }
        } catch (e) {
            console.error('Error loading verification configs:', e);
        }
    }

    saveConfigs() {
        const filePath = path.join(__dirname, '..', 'verification_config.json');
        try {
            fs.writeFileSync(filePath, JSON.stringify(Object.fromEntries(this.configs), null, 2));
        } catch (e) {
            console.error('Error saving verification configs:', e);
        }
    }

    initialize(client) {
        for (const [guildId, config] of this.configs) {
            this.setupVerificationMessage(guildId, config);
        }
    }

    async setupVerificationMessage(guildId, config) {
        try {
            const guild = this.client.guilds.cache.get(guildId);
            if (!guild) return;

            const channel = guild.channels.cache.get(config.channelId);
            if (!channel) return;

            const messages = await channel.messages.fetch({ limit: 10 });
            const existing = messages.find(m => m.author.id === this.client.user.id && m.embeds[0]?.title === '✅ Verifizierung');

            if (!existing) {
                const embed = new EmbedBuilder()
                    .setTitle('✅ Verifizierung')
                    .setDescription('Klicke auf den Button unten, um dich zu verifizieren und Zugriff auf den Server zu erhalten.')
                    .setColor('#6C5CE7')
                    .setTimestamp();

                const row = new ActionRowBuilder().addComponents(
                    new ButtonBuilder().setCustomId('verify_captcha').setLabel('Verifizieren').setStyle(ButtonStyle.Success).setEmoji('✅')
                );

                await channel.send({ embeds: [embed], components: [row] });
            }
        } catch (e) {
            console.error('Error setting up verification message:', e);
        }
    }

    async handleCommand(interaction) {
        if (interaction.commandName !== 'verify') return;

        const sub = interaction.options.getSubcommand();

        if (sub === 'config') {
            await this.configureVerification(interaction);
        }
    }

    async handleButton(interaction) {
        if (interaction.customId === 'verify_captcha') {
            await this.startVerification(interaction);
        }
    }

    async handleCaptchaButton(interaction) {
        await this.startVerification(interaction);
    }

    async startVerification(interaction) {
        const num1 = Math.floor(Math.random() * 10) + 1;
        const num2 = Math.floor(Math.random() * 10) + 1;
        const answer = num1 + num2;

        this.pendingVerifications.set(interaction.user.id, {
            answer,
            attempts: 0,
            channelId: interaction.channelId
        });

        const embed = new EmbedBuilder()
            .setTitle('🧮 Captcha-Verifizierung')
            .setDescription(`Bitte löse folgende Aufgabe:\n\n**Was ist ${num1} + ${num2}?**\n\nAntworte mit der Zahl in diesem Kanal.`)
            .setColor('#6C5CE7')
            .setTimestamp();

        await interaction.reply({ embeds: [embed], ephemeral: true });
    }

    async handleMemberJoin(member) {
        const config = this.configs.get(member.guild.id);
        if (!config) return;

        const role = member.guild.roles.cache.get(config.roleId);
        if (!role) return;

        const unverifiedRole = member.guild.roles.cache.find(r => r.name === 'Unverified');
        if (unverifiedRole) {
            await member.roles.add(unverifiedRole).catch(() => {});
        }
    }

    async handleMessage(message) {
        if (message.author.bot) return;

        const pending = this.pendingVerifications.get(message.author.id);
        if (!pending) return;

        const answer = parseInt(message.content);
        if (isNaN(answer)) return;

        pending.attempts++;

        if (answer === pending.answer) {
            this.pendingVerifications.delete(message.author.id);

            const config = this.configs.get(message.guild.id);
            if (config) {
                const role = message.guild.roles.cache.get(config.roleId);
                if (role) {
                    await message.member.roles.add(role).catch(() => {});
                }

                const unverifiedRole = message.guild.roles.cache.find(r => r.name === 'Unverified');
                if (unverifiedRole) {
                    await message.member.roles.remove(unverifiedRole).catch(() => {});
                }
            }

            await message.react('✅');

            const embed = new EmbedBuilder()
                .setTitle('✅ Verifizierung erfolgreich')
                .setDescription('Du wurdest erfolgreich verifiziert!')
                .setColor('#00ff00')
                .setTimestamp();

            await message.author.send({ embeds: [embed] }).catch(() => {});
        } else if (pending.attempts >= 3) {
            this.pendingVerifications.delete(message.author.id);

            await message.reply('❌ Zu viele Fehlversuche. Bitte klicke erneut auf "Verifizieren".');
        } else {
            await message.reply(`❌ Falsche Antwort. Versuch es noch einmal. (Versuch ${pending.attempts}/3)`);
        }
    }

    async configureVerification(interaction) {
        if (!interaction.member.permissions.has(PermissionFlagsBits.Administrator)) {
            return interaction.reply({ content: '❌ Nur Administratoren können die Verifizierung konfigurieren.', ephemeral: true });
        }

        const channel = interaction.options.getChannel('channel');
        const role = interaction.options.getRole('role');

        this.configs.set(interaction.guildId, {
            channelId: channel.id,
            roleId: role.id,
            enabled: true
        });

        this.saveConfigs();
        this.setupVerificationMessage(interaction.guildId, this.configs.get(interaction.guildId));

        await interaction.reply({ content: `✅ Verifizierung konfiguriert! Kanal: ${channel}, Rolle: ${role}`, ephemeral: true });
    }
}

module.exports = VerificationSystem;
