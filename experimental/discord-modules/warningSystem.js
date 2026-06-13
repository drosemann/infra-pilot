const { EmbedBuilder, PermissionFlagsBits } = require('discord.js');
const fs = require('fs');
const path = require('path');

class WarningSystem {
    constructor(client) {
        this.client = client;
        this.warnings = new Map();
        this.loadWarnings();
    }

    loadWarnings() {
        const filePath = path.join(__dirname, '..', 'warnings.json');
        try {
            if (fs.existsSync(filePath)) {
                const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
                for (const [guildId, users] of Object.entries(data)) {
                    this.warnings.set(guildId, new Map(Object.entries(users)));
                }
            }
        } catch (e) {
            console.error('Error loading warnings:', e);
        }
    }

    saveWarnings() {
        const filePath = path.join(__dirname, '..', 'warnings.json');
        try {
            const data = {};
            for (const [guildId, users] of this.warnings) {
                data[guildId] = Object.fromEntries(users);
            }
            fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
        } catch (e) {
            console.error('Error saving warnings:', e);
        }
    }

    getWarningsForUser(guildId, userId) {
        const guild = this.warnings.get(guildId);
        if (!guild) return [];
        return guild.get(userId) || [];
    }

    async handleCommand(interaction) {
        if (interaction.commandName === 'warn') {
            await this.warnUser(interaction);
        } else if (interaction.commandName === 'warnings') {
            await this.viewWarnings(interaction);
        } else if (interaction.commandName === 'warnremove') {
            await this.removeWarning(interaction);
        }
    }

    async warnUser(interaction) {
        if (!interaction.member.permissions.has(PermissionFlagsBits.ModerateMembers)) {
            return interaction.reply({ content: '❌ Du benötigst die Berechtigung "Mitglieder moderieren".', ephemeral: true });
        }

        const user = interaction.options.getUser('user');
        const reason = interaction.options.getString('reason');
        const member = await interaction.guild.members.fetch(user.id).catch(() => null);

        if (member && member.roles.highest.position >= interaction.member.roles.highest.position) {
            return interaction.reply({ content: '❌ Du kannst diesen Benutzer nicht verwarnen.', ephemeral: true });
        }

        const warning = {
            id: Date.now().toString(),
            userId: user.id,
            moderatorId: interaction.user.id,
            reason,
            timestamp: new Date().toISOString()
        };

        if (!this.warnings.has(interaction.guildId)) {
            this.warnings.set(interaction.guildId, new Map());
        }

        const guildWarnings = this.warnings.get(interaction.guildId);
        if (!guildWarnings.has(user.id)) {
            guildWarnings.set(user.id, []);
        }

        guildWarnings.get(user.id).push(warning);
        this.saveWarnings();

        const count = guildWarnings.get(user.id).length;

        let action = '';
        if (count >= 5) {
            action = '🚫 Automatischer Kick bei 5 Verwarnungen.';
            if (member) await member.kick(`5 Verwarnungen erreicht`).catch(() => {});
        } else if (count >= 3) {
            action = '🔇 Automatischer Timeout (1h) bei 3 Verwarnungen.';
            if (member) await member.timeout(3600000, '3 Verwarnungen erreicht').catch(() => {});
        }

        const embed = new EmbedBuilder()
            .setTitle('⚠️ Verwarnung')
            .setDescription(`${user} wurde verwarnt.`)
            .addFields([
                { name: 'Grund', value: reason, inline: false },
                { name: 'Anzahl', value: `${count}/5`, inline: true },
                { name: 'Moderator', value: interaction.user.toString(), inline: true }
            ])
            .setColor('#ffa500')
            .setTimestamp();

        if (action) {
            embed.addFields({ name: 'Automatische Aktion', value: action, inline: false });
        }

        await interaction.reply({ embeds: [embed] });

        try {
            await user.send({ embeds: [
                new EmbedBuilder()
                    .setTitle('⚠️ Du wurdest verwarnt')
                    .setDescription(`**Grund:** ${reason}`)
                    .setColor('#ffa500')
                    .setTimestamp()
            ]});
        } catch (e) {}
    }

    async viewWarnings(interaction) {
        const user = interaction.options.getUser('user') || interaction.user;
        const warnings = this.getWarningsForUser(interaction.guildId, user.id);

        if (warnings.length === 0) {
            return interaction.reply({ content: `✅ ${user.username} hat keine Verwarnungen.`, ephemeral: true });
        }

        const embed = new EmbedBuilder()
            .setTitle(`⚠️ Verwarnungen für ${user.username}`)
            .setDescription(`**Anzahl: ${warnings.length}/5**`)
            .setColor('#ffa500')
            .setTimestamp();

        for (const w of warnings) {
            const mod = await this.client.users.fetch(w.moderatorId).catch(() => null);
            embed.addFields({
                name: `#${w.id} - ${new Date(w.timestamp).toLocaleString('de-DE')}`,
                value: `**Grund:** ${w.reason}\n**Moderator:** ${mod ? mod.tag : 'Unbekannt'}`,
                inline: false
            });
        }

        await interaction.reply({ embeds: [embed], ephemeral: true });
    }

    async removeWarning(interaction) {
        if (!interaction.member.permissions.has(PermissionFlagsBits.ModerateMembers)) {
            return interaction.reply({ content: '❌ Du benötigst die Berechtigung "Mitglieder moderieren".', ephemeral: true });
        }

        const user = interaction.options.getUser('user');
        const warningId = interaction.options.getString('warning_id');
        const guildWarnings = this.warnings.get(interaction.guildId);

        if (!guildWarnings || !guildWarnings.has(user.id)) {
            return interaction.reply({ content: '❌ Keine Verwarnungen für diesen Benutzer gefunden.', ephemeral: true });
        }

        const warnings = guildWarnings.get(user.id);
        const index = warnings.findIndex(w => w.id === warningId);

        if (index === -1) {
            return interaction.reply({ content: '❌ Verwarnung nicht gefunden.', ephemeral: true });
        }

        warnings.splice(index, 1);
        if (warnings.length === 0) guildWarnings.delete(user.id);
        this.saveWarnings();

        await interaction.reply({ content: `✅ Verwarnung #${warningId} von ${user.username} entfernt.`, ephemeral: true });
    }

    async handleModalSubmit(interaction) {
        // reserved
    }
}

module.exports = WarningSystem;
