const { EmbedBuilder, PermissionFlagsBits } = require('discord.js');

class ChannelCleanup {
    constructor(client) {
        this.client = client;
    }

    async handleCommand(interaction) {
        if (interaction.commandName !== 'purge') return;

        if (!interaction.member.permissions.has(PermissionFlagsBits.ManageMessages)) {
            return interaction.reply({ content: '❌ Du benötigst die Berechtigung "Nachrichten verwalten".', ephemeral: true });
        }

        const sub = interaction.options.getSubcommand();

        if (sub === 'all') {
            const count = interaction.options.getInteger('count');
            await this.purgeAll(interaction, count);
        } else if (sub === 'user') {
            const user = interaction.options.getUser('user');
            const count = interaction.options.getInteger('count');
            await this.purgeUser(interaction, user, count);
        } else if (sub === 'bot') {
            const count = interaction.options.getInteger('count');
            await this.purgeBot(interaction, count);
        }
    }

    async purgeAll(interaction, count) {
        await interaction.deferReply({ ephemeral: true });

        try {
            const messages = await interaction.channel.bulkDelete(Math.min(count, 100), true);
            await interaction.editReply({ content: `✅ ${messages.size} Nachrichten gelöscht.` });
        } catch (e) {
            await interaction.editReply({ content: `❌ Fehler: ${e.message}` });
        }
    }

    async purgeUser(interaction, user, count) {
        await interaction.deferReply({ ephemeral: true });

        try {
            const messages = await interaction.channel.messages.fetch({ limit: Math.min(count * 2, 200) });
            const userMessages = messages.filter(m => m.author.id === user.id).first(Math.min(count, 100));
            const deleted = await interaction.channel.bulkDelete(userMessages, true);

            await interaction.editReply({ content: `✅ ${deleted.size} Nachrichten von ${user.username} gelöscht.` });
        } catch (e) {
            await interaction.editReply({ content: `❌ Fehler: ${e.message}` });
        }
    }

    async purgeBot(interaction, count) {
        await interaction.deferReply({ ephemeral: true });

        try {
            const messages = await interaction.channel.messages.fetch({ limit: Math.min(count * 2, 200) });
            const botMessages = messages.filter(m => m.author.bot).first(Math.min(count, 100));
            const deleted = await interaction.channel.bulkDelete(botMessages, true);

            await interaction.editReply({ content: `✅ ${deleted.size} Bot-Nachrichten gelöscht.` });
        } catch (e) {
            await interaction.editReply({ content: `❌ Fehler: ${e.message}` });
        }
    }
}

module.exports = ChannelCleanup;
