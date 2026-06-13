const { EmbedBuilder, PermissionFlagsBits } = require('discord.js');
const fs = require('fs');
const path = require('path');

class VerificationLevels {
    constructor(client) {
        this.client = client;
        this.configs = new Map();
        this.loadConfigs();
    }

    loadConfigs() {
        const filePath = path.join(__dirname, '..', 'verification_levels.json');
        try {
            if (fs.existsSync(filePath)) {
                this.configs = new Map(Object.entries(JSON.parse(fs.readFileSync(filePath, 'utf8'))));
            }
        } catch (e) {
            console.error('Error loading verification levels:', e);
        }
    }

    saveConfigs() {
        const filePath = path.join(__dirname, '..', 'verification_levels.json');
        try {
            fs.writeFileSync(filePath, JSON.stringify(Object.fromEntries(this.configs), null, 2));
        } catch (e) {
            console.error('Error saving verification levels:', e);
        }
    }

    async handleCommand(interaction) {
        if (interaction.commandName !== 'verifylevel') return;

        if (!interaction.member.permissions.has(PermissionFlagsBits.Administrator)) {
            return interaction.reply({ content: '❌ Nur Administratoren können Verifizierungsstufen konfigurieren.', ephemeral: true });
        }

        const sub = interaction.options.getSubcommand();
        if (sub === 'config') {
            await this.configure(interaction);
        }
    }

    async configure(interaction) {
        const requiredAgeDays = interaction.options.getInteger('required_age_days') || 0;
        const requiredGuildDays = interaction.options.getInteger('required_guild_days') || 0;
        const requiredRole = interaction.options.getRole('required_role');

        const config = {
            requiredAgeDays: requiredAgeDays,
            requiredGuildDays: requiredGuildDays,
            requiredRoleId: requiredRole?.id || null,
            enabled: true
        };

        this.configs.set(interaction.guildId, config);
        this.saveConfigs();

        const embed = new EmbedBuilder()
            .setTitle('✅ Verifizierungsstufen konfiguriert')
            .setColor('#6C5CE7')
            .addFields([
                { name: 'Account-Alter', value: requiredAgeDays > 0 ? `${requiredAgeDays} Tage` : 'Keine Anforderung', inline: true },
                { name: 'Tage im Server', value: requiredGuildDays > 0 ? `${requiredGuildDays} Tage` : 'Keine Anforderung', inline: true },
                { name: 'Erforderliche Rolle', value: requiredRole ? requiredRole.toString() : 'Keine', inline: true }
            ])
            .setTimestamp();

        await interaction.reply({ embeds: [embed], ephemeral: true });
    }

    async checkMember(member) {
        const config = this.configs.get(member.guild.id);
        if (!config || !config.enabled) return;

        const now = Date.now();
        const accountAge = (now - member.user.createdAt.getTime()) / 86400000;
        const guildAge = member.joinedAt ? (now - member.joinedAt.getTime()) / 86400000 : 0;

        const embed = new EmbedBuilder()
            .setTitle('🔒 Verifizierungs-Check')
            .setColor('#ffa500')
            .setTimestamp();

        let passed = true;
        const failed = [];

        if (config.requiredAgeDays > 0 && accountAge < config.requiredAgeDays) {
            passed = false;
            failed.push(`Account muss mindestens ${config.requiredAgeDays} Tage alt sein (aktuell: ${Math.floor(accountAge)} Tage)`);
        }

        if (config.requiredGuildDays > 0 && guildAge < config.requiredGuildDays) {
            passed = false;
            failed.push(`Du musst mindestens ${config.requiredGuildDays} Tage im Server sein (aktuell: ${Math.floor(guildAge)} Tage)`);
        }

        if (config.requiredRoleId) {
            const hasRole = member.roles.cache.has(config.requiredRoleId);
            if (!hasRole) {
                passed = false;
                const role = member.guild.roles.cache.get(config.requiredRoleId);
                failed.push(`Du benötigst die Rolle: ${role ? role.name : 'Unbekannt'}`);
            }
        }

        if (!passed) {
            embed.setDescription(`❌ Du erfüllst nicht alle Voraussetzungen:\n\n${failed.map(f => `• ${f}`).join('\n')}`);

            try {
                await member.send({ embeds: [embed] });
            } catch (e) {}

            const unverifiedRole = member.guild.roles.cache.find(r => r.name === 'Unverified' || r.name === 'unverified');
            if (unverifiedRole) {
                await member.roles.add(unverifiedRole).catch(() => {});
            }

            const limitedChannels = member.guild.channels.cache.filter(c =>
                c.name.toLowerCase().includes('welcome') || c.name.toLowerCase().includes('verification')
            );
            for (const [, channel] of limitedChannels) {
                await channel.permissionOverwrites.edit(member.id, {
                    ViewChannel: true,
                    SendMessages: true
                }).catch(() => {});
            }
        }
    }
}

module.exports = VerificationLevels;
