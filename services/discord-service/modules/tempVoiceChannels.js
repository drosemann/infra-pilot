const { ChannelType, PermissionFlagsBits } = require('discord.js');

class TempVoiceChannels {
    constructor(client) {
        this.client = client;
        this.tempChannels = new Map();
        this.joinToCreateChannelIds = new Set();
        this.cleanupInterval = null;
    }

    initialize(client) {
        this.cleanupInterval = setInterval(() => this.cleanupEmptyChannels(), 30000);
    }

    async handleVoiceStateUpdate(oldState, newState) {
        if (oldState.channelId === newState.channelId) return;

        if (newState.channelId) {
            await this.handleJoin(newState);
        }

        if (oldState.channelId) {
            await this.handleLeave(oldState);
        }
    }

    async handleJoin(state) {
        const channel = state.channel;
        if (!channel || !this.isJoinToCreateChannel(channel)) return;

        try {
            const tempChannel = await state.guild.channels.create({
                name: `🔊 ${state.member.displayName}s Channel`,
                type: ChannelType.GuildVoice,
                parent: channel.parentId,
                userLimit: 0,
                permissionOverwrites: [
                    {
                        id: state.guild.id,
                        allow: [PermissionFlagsBits.Connect],
                        deny: []
                    },
                    {
                        id: state.member.id,
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

            this.tempChannels.set(tempChannel.id, {
                ownerId: state.member.id,
                createdAt: Date.now()
            });

            await state.member.voice.setChannel(tempChannel);
        } catch (e) {
            console.error('Error creating temp voice channel:', e.message);
        }
    }

    async handleLeave(state) {
        const channel = state.channel;
        if (!channel) return;

        if (this.tempChannels.has(channel.id)) {
            const tempInfo = this.tempChannels.get(channel.id);
            if (channel.members.size === 0) {
                try {
                    await channel.delete('Temp-Channel leer');
                    this.tempChannels.delete(channel.id);
                } catch (e) {
                    console.error('Error deleting temp channel:', e.message);
                }
            } else if (tempInfo.ownerId === state.member.id) {
                const newOwner = channel.members.first();
                if (newOwner) {
                    this.tempChannels.set(channel.id, {
                        ownerId: newOwner.id,
                        createdAt: tempInfo.createdAt
                    });
                }
            }
        }
    }

    async handleMemberLeave(member) {
        for (const [channelId, info] of this.tempChannels) {
            if (info.ownerId === member.id) {
                const channel = member.guild.channels.cache.get(channelId);
                if (channel) {
                    const newOwner = channel.members.first();
                    if (newOwner) {
                        this.tempChannels.set(channelId, { ownerId: newOwner.id, createdAt: info.createdAt });
                    }
                }
            }
        }
    }

    async cleanupEmptyChannels() {
        for (const [channelId, info] of this.tempChannels) {
            try {
                const channel = await this.client.channels.fetch(channelId).catch(() => null);
                if (!channel || channel.members.size === 0) {
                    if (channel) await channel.delete('Cleanup: leer').catch(() => {});
                    this.tempChannels.delete(channelId);
                }
            } catch (e) {}
        }
    }

    isJoinToCreateChannel(channel) {
        return channel.name.toLowerCase().includes('join to create') ||
               channel.name.toLowerCase().includes('create') && channel.type === ChannelType.GuildVoice;
    }
}

module.exports = TempVoiceChannels;
