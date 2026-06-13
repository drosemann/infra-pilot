const { EmbedBuilder, PermissionFlagsBits, ChannelType } = require('discord.js');

class VoiceManager {
    constructor(client) {
        this.client = client;
        this.userChannels = new Map();
    }

    async handleCommand(interaction) {
        if (interaction.commandName !== 'voice') return;

        const sub = interaction.options.getSubcommand();

        if (sub === 'create') {
            await this.createChannel(interaction);
        } else if (sub === 'limit') {
            await this.setLimit(interaction);
        } else if (sub === 'lock') {
            await this.lockChannel(interaction);
        } else if (sub === 'unlock') {
            await this.unlockChannel(interaction);
        } else if (sub === 'claim') {
            await this.claimChannel(interaction);
        }
    }

    async createChannel(interaction) {
        const name = interaction.options.getString('name');
        const limit = interaction.options.getInteger('limit') || 0;

        if (!interaction.member.voice.channel) {
            return interaction.reply({ content: '❌ Du musst in einem Sprachkanal sein, um einen zu erstellen.', ephemeral: true });
        }

        try {
            const category = interaction.member.voice.channel.parent;

            const channel = await interaction.guild.channels.create({
                name,
                type: ChannelType.GuildVoice,
                parent: category?.id || null,
                userLimit: limit,
                permissionOverwrites: [
                    {
                        id: interaction.guild.id,
                        allow: [PermissionFlagsBits.Connect],
                        deny: []
                    },
                    {
                        id: interaction.user.id,
                        allow: [
                            PermissionFlagsBits.Connect,
                            PermissionFlagsBits.ManageChannels,
                            PermissionFlagsBits.MuteMembers,
                            PermissionFlagsBits.DeafenMembers,
                            PermissionFlagsBits.MoveMembers
                        ],
                        deny: []
                    }
                ]
            });

            this.userChannels.set(interaction.user.id, channel.id);

            await interaction.member.voice.setChannel(channel);

            const embed = new EmbedBuilder()
                .setTitle('✅ Sprachkanal erstellt')
                .setDescription(`Kanal **${name}** wurde erstellt.`)
                .addFields([
                    { name: 'Limit', value: limit > 0 ? limit.toString() : 'Kein Limit', inline: true }
                ])
                .setColor('#6C5CE7')
                .setTimestamp();

            await interaction.reply({ embeds: [embed], ephemeral: true });
        } catch (e) {
            await interaction.reply({ content: `❌ Fehler: ${e.message}`, ephemeral: true });
        }
    }

    async setLimit(interaction) {
        const limit = interaction.options.getInteger('limit');
        const channelId = this.userChannels.get(interaction.user.id);

        if (!channelId) {
            return interaction.reply({ content: '❌ Du hast keinen eigenen Sprachkanal.', ephemeral: true });
        }

        const channel = interaction.guild.channels.cache.get(channelId);
        if (!channel) {
            this.userChannels.delete(interaction.user.id);
            return interaction.reply({ content: '❌ Kanal nicht gefunden.', ephemeral: true });
        }

        try {
            await channel.setUserLimit(limit);
            await interaction.reply({ content: `✅ Limit auf ${limit} gesetzt.`, ephemeral: true });
        } catch (e) {
            await interaction.reply({ content: `❌ Fehler: ${e.message}`, ephemeral: true });
        }
    }

    async lockChannel(interaction) {
        const channelId = this.userChannels.get(interaction.user.id);
        if (!channelId) {
            return interaction.reply({ content: '❌ Du hast keinen eigenen Sprachkanal.', ephemeral: true });
        }

        const channel = interaction.guild.channels.cache.get(channelId);
        if (!channel) {
            this.userChannels.delete(interaction.user.id);
            return interaction.reply({ content: '❌ Kanal nicht gefunden.', ephemeral: true });
        }

        try {
            await channel.permissionOverwrites.edit(interaction.guild.id, {
                Connect: false
            });
            await interaction.reply({ content: '🔒 Kanal wurde gesperrt.', ephemeral: true });
        } catch (e) {
            await interaction.reply({ content: `❌ Fehler: ${e.message}`, ephemeral: true });
        }
    }

    async unlockChannel(interaction) {
        const channelId = this.userChannels.get(interaction.user.id);
        if (!channelId) {
            return interaction.reply({ content: '❌ Du hast keinen eigenen Sprachkanal.', ephemeral: true });
        }

        const channel = interaction.guild.channels.cache.get(channelId);
        if (!channel) {
            this.userChannels.delete(interaction.user.id);
            return interaction.reply({ content: '❌ Kanal nicht gefunden.', ephemeral: true });
        }

        try {
            await channel.permissionOverwrites.edit(interaction.guild.id, {
                Connect: null
            });
            await interaction.reply({ content: '🔓 Kanal wurde entsperrt.', ephemeral: true });
        } catch (e) {
            await interaction.reply({ content: `❌ Fehler: ${e.message}`, ephemeral: true });
        }
    }

    async claimChannel(interaction) {
        if (!interaction.member.voice.channel) {
            return interaction.reply({ content: '❌ Du bist in keinem Sprachkanal.', ephemeral: true });
        }

        const channel = interaction.member.voice.channel;
        let currentOwner = null;

        for (const [userId, channelId] of this.userChannels) {
            if (channelId === channel.id) {
                currentOwner = userId;
                break;
            }
        }

        if (!currentOwner || currentOwner === interaction.user.id) {
            return interaction.reply({ content: '❌ Du besitzt diesen Kanal bereits oder er hat keinen Besitzer.', ephemeral: true });
        }

        const ownerMember = await interaction.guild.members.fetch(currentOwner).catch(() => null);
        if (ownerMember && channel.members.has(ownerMember.id)) {
            return interaction.reply({ content: '❌ Der Besitzer ist noch im Kanal.', ephemeral: true });
        }

        this.userChannels.delete(currentOwner);
        this.userChannels.set(interaction.user.id, channel.id);

        await channel.permissionOverwrites.edit(interaction.user.id, {
            Connect: true,
            ManageChannels: true,
            MuteMembers: true,
            DeafenMembers: true
        });

        await interaction.reply({ content: '✅ Du hast die Kontrolle über diesen Kanal übernommen.', ephemeral: true });
    }

    async handleButton(interaction) {
        // reserved
    }
}

module.exports = VoiceManager;
