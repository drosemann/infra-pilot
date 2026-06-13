const { EmbedBuilder, PermissionFlagsBits } = require('discord.js');

class RoleHierarchy {
    constructor(client, roleManager) {
        this.client = client;
        this.roleManager = roleManager;
    }

    async handleCommand(interaction) {
        if (interaction.commandName !== 'role') return;

        const sub = interaction.options.getSubcommand();

        if (sub === 'create') {
            await this.createRole(interaction);
        } else if (sub === 'delete') {
            await this.deleteRole(interaction);
        } else if (sub === 'edit') {
            await this.editRole(interaction);
        } else if (sub === 'info') {
            await this.showHierarchy(interaction);
        } else if (sub === 'menu') {
            await this.createRoleMenu(interaction);
        }
    }

    async createRole(interaction) {
        if (!interaction.member.permissions.has(PermissionFlagsBits.ManageRoles)) {
            return interaction.reply({ content: '❌ Du benötigst die Berechtigung "Rollen verwalten".', ephemeral: true });
        }

        const name = interaction.options.getString('name');
        const color = interaction.options.getString('color') || '#6C5CE7';
        const hoist = interaction.options.getBoolean('hoist') || false;

        try {
            const role = await interaction.guild.roles.create({
                name,
                color: parseInt(color.replace('#', ''), 16) || 0x6C5CE7,
                hoist,
                reason: `Erstellt von ${interaction.user.tag}`
            });

            const embed = new EmbedBuilder()
                .setTitle('✅ Rolle erstellt')
                .setDescription(`Rolle **${role.name}** wurde erstellt.`)
                .addFields([
                    { name: 'ID', value: role.id, inline: true },
                    { name: 'Farbe', value: color, inline: true },
                    { name: 'Position', value: role.position.toString(), inline: true }
                ])
                .setColor(color)
                .setTimestamp();

            await interaction.reply({ embeds: [embed] });
        } catch (e) {
            await interaction.reply({ content: `❌ Fehler: ${e.message}`, ephemeral: true });
        }
    }

    async deleteRole(interaction) {
        if (!interaction.member.permissions.has(PermissionFlagsBits.ManageRoles)) {
            return interaction.reply({ content: '❌ Du benötigst die Berechtigung "Rollen verwalten".', ephemeral: true });
        }

        const role = interaction.options.getRole('role');

        if (role.managed) {
            return interaction.reply({ content: '❌ Diese Rolle wird von einer Integration verwaltet und kann nicht gelöscht werden.', ephemeral: true });
        }

        if (role.position >= interaction.member.roles.highest.position) {
            return interaction.reply({ content: '❌ Du kannst keine Rolle löschen, die höher oder gleich deiner höchsten Rolle ist.', ephemeral: true });
        }

        try {
            await role.delete(`Gelöscht von ${interaction.user.tag}`);
            await interaction.reply({ content: `✅ Rolle **${role.name}** wurde gelöscht.` });
        } catch (e) {
            await interaction.reply({ content: `❌ Fehler: ${e.message}`, ephemeral: true });
        }
    }

    async editRole(interaction) {
        if (!interaction.member.permissions.has(PermissionFlagsBits.ManageRoles)) {
            return interaction.reply({ content: '❌ Du benötigst die Berechtigung "Rollen verwalten".', ephemeral: true });
        }

        const role = interaction.options.getRole('role');
        const name = interaction.options.getString('name');
        const color = interaction.options.getString('color');

        if (role.position >= interaction.member.roles.highest.position) {
            return interaction.reply({ content: '❌ Du kannst diese Rolle nicht bearbeiten.', ephemeral: true });
        }

        try {
            const editOptions = {};
            if (name) editOptions.name = name;
            if (color) editOptions.color = parseInt(color.replace('#', ''), 16) || 0x6C5CE7;

            await role.edit(editOptions);

            const embed = new EmbedBuilder()
                .setTitle('✅ Rolle bearbeitet')
                .setDescription(`Rolle **${role.name}** wurde aktualisiert.`)
                .setColor(color || '#6C5CE7')
                .setTimestamp();

            await interaction.reply({ embeds: [embed] });
        } catch (e) {
            await interaction.reply({ content: `❌ Fehler: ${e.message}`, ephemeral: true });
        }
    }

    async showHierarchy(interaction) {
        const roles = interaction.guild.roles.cache
            .filter(r => r.id !== interaction.guild.id)
            .sort((a, b) => b.position - a.position);

        const embed = new EmbedBuilder()
            .setTitle('📋 Rollenhierarchie')
            .setDescription(roles.map(r => `<@&${r.id}> - Position ${r.position}`).join('\n'))
            .setColor('#6C5CE7')
            .setFooter({ text: `${roles.size} Rollen insgesamt` })
            .setTimestamp();

        await interaction.reply({ embeds: [embed], ephemeral: true });
    }

    async createRoleMenu(interaction) {
        if (!interaction.member.permissions.has(PermissionFlagsBits.ManageRoles)) {
            return interaction.reply({ content: '❌ Du benötigst die Berechtigung "Rollen verwalten".', ephemeral: true });
        }

        const channel = interaction.options.getChannel('channel');
        const roles = interaction.guild.roles.cache
            .filter(r => r.id !== interaction.guild.id && !r.managed && r.position < interaction.member.roles.highest.position)
            .first(10);

        if (roles.length === 0) {
            return interaction.reply({ content: '❌ Keine verfügbaren Rollen gefunden.', ephemeral: true });
        }

        const emojis = ['🌟', '⭐', '💎', '🔮', '🎯', '🎨', '🎭', '🎪', '🎫', '🎬'];
        const options = roles.slice(0, 10).map((role, i) => ({
            emoji: emojis[i] || '✅',
            role: role,
            description: `Klicke um ${role.name} zu erhalten/entfernen`
        }));

        try {
            await this.roleManager.createRoleMenu(channel, options);
            await interaction.reply({ content: `✅ Rollen-Menü in ${channel} erstellt!`, ephemeral: true });
        } catch (e) {
            await interaction.reply({ content: `❌ Fehler: ${e.message}`, ephemeral: true });
        }
    }
}

module.exports = RoleHierarchy;
