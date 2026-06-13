const { ChannelType, PermissionFlagsBits } = require('discord.js');

class CategoryManager {
    constructor(client) {
        this.client = client;
    }

    async handleCommand(interaction) {
        if (interaction.commandName !== 'category') return;

        if (!interaction.member.permissions.has(PermissionFlagsBits.ManageChannels)) {
            return interaction.reply({ content: '❌ Du benötigst die Berechtigung "Kanäle verwalten".', ephemeral: true });
        }

        const sub = interaction.options.getSubcommand();

        if (sub === 'create') {
            await this.createCategory(interaction);
        } else if (sub === 'add') {
            await this.addToCategory(interaction);
        } else if (sub === 'permissions') {
            await this.syncPermissions(interaction);
        }
    }

    async createCategory(interaction) {
        const name = interaction.options.getString('name');

        try {
            const category = await interaction.guild.channels.create({
                name,
                type: ChannelType.GuildCategory,
                reason: `Erstellt von ${interaction.user.tag}`
            });

            await interaction.reply({ content: `✅ Kategorie **${name}** erstellt!`, ephemeral: true });
        } catch (e) {
            await interaction.reply({ content: `❌ Fehler: ${e.message}`, ephemeral: true });
        }
    }

    async addToCategory(interaction) {
        const channel = interaction.options.getChannel('channel');
        const category = interaction.options.getChannel('category');

        if (channel.type === ChannelType.GuildCategory) {
            return interaction.reply({ content: '❌ Du kannst keine Kategorie in eine andere Kategorie verschieben.', ephemeral: true });
        }

        if (category.type !== ChannelType.GuildCategory) {
            return interaction.reply({ content: '❌ Das Ziel ist keine Kategorie.', ephemeral: true });
        }

        try {
            await channel.setParent(category.id, { lockPermissions: false });
            await interaction.reply({ content: `✅ ${channel} wurde zu **${category.name}** hinzugefügt.`, ephemeral: true });
        } catch (e) {
            await interaction.reply({ content: `❌ Fehler: ${e.message}`, ephemeral: true });
        }
    }

    async syncPermissions(interaction) {
        const category = interaction.options.getChannel('category');

        if (category.type !== ChannelType.GuildCategory) {
            return interaction.reply({ content: '❌ Das ist keine Kategorie.', ephemeral: true });
        }

        try {
            const channels = category.children.cache;
            let synced = 0;

            for (const [, channel] of channels) {
                await channel.lockPermissions();
                synced++;
            }

            await interaction.reply({ content: `✅ Berechtigungen von ${synced} Kanälen in **${category.name}** synchronisiert.`, ephemeral: true });
        } catch (e) {
            await interaction.reply({ content: `❌ Fehler: ${e.message}`, ephemeral: true });
        }
    }
}

module.exports = CategoryManager;
