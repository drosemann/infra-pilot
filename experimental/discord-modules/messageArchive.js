const { EmbedBuilder, PermissionFlagsBits, AttachmentBuilder } = require('discord.js');
const fs = require('fs');
const path = require('path');

class MessageArchive {
    constructor(client) {
        this.client = client;
    }

    async handleCommand(interaction) {
        if (interaction.commandName !== 'archive') return;

        const sub = interaction.options.getSubcommand();
        if (sub === 'channel') {
            await this.archiveChannel(interaction);
        }
    }

    async archiveChannel(interaction) {
        if (!interaction.member.permissions.has(PermissionFlagsBits.Administrator)) {
            return interaction.reply({ content: '❌ Nur Administratoren können Kanäle archivieren.', ephemeral: true });
        }

        const channel = interaction.options.getChannel('channel');
        const format = interaction.options.getString('format') || 'json';

        await interaction.deferReply({ ephemeral: true });

        try {
            const messages = await channel.messages.fetch({ limit: 100 });
            const archiveData = messages.reverse().map(m => ({
                id: m.id,
                author: m.author.tag,
                authorId: m.author.id,
                content: m.content,
                timestamp: m.createdAt.toISOString(),
                attachments: m.attachments.map(a => a.url),
                hasEmbeds: m.embeds.length > 0
            }));

            let fileName, fileBuffer, attachment;

            if (format === 'csv') {
                const header = 'ID,Autor,Inhalt,Datum,Anhänge\n';
                const rows = archiveData.map(m => {
                    const content = `"${m.content.replace(/"/g, '""')}"`;
                    return `${m.id},"${m.author}",${content},"${m.timestamp}","${m.attachments.join('; ')}"`;
                }).join('\n');
                fileBuffer = Buffer.from(header + rows, 'utf8');
                fileName = `archive-${channel.name}-${Date.now()}.csv`;
                attachment = new AttachmentBuilder(fileBuffer, { name: fileName });
            } else if (format === 'txt') {
                const text = archiveData.map(m =>
                    `[${new Date(m.timestamp).toLocaleString('de-DE')}] ${m.author}: ${m.content}${m.attachments.length ? `\n    Anhänge: ${m.attachments.join(', ')}` : ''}`
                ).join('\n\n');
                fileBuffer = Buffer.from(text, 'utf8');
                fileName = `archive-${channel.name}-${Date.now()}.txt`;
                attachment = new AttachmentBuilder(fileBuffer, { name: fileName });
            } else {
                fileBuffer = Buffer.from(JSON.stringify(archiveData, null, 2), 'utf8');
                fileName = `archive-${channel.name}-${Date.now()}.json`;
                attachment = new AttachmentBuilder(fileBuffer, { name: fileName });
            }

            const embed = new EmbedBuilder()
                .setTitle('📦 Kanal-Archiv')
                .setDescription(`Archiv von **#${channel.name}**`)
                .addFields([
                    { name: 'Nachrichten', value: archiveData.length.toString(), inline: true },
                    { name: 'Format', value: format.toUpperCase(), inline: true },
                    { name: 'Größe', value: `${(fileBuffer.length / 1024).toFixed(1)} KB`, inline: true }
                ])
                .setColor('#6C5CE7')
                .setTimestamp();

            await interaction.editReply({ embeds: [embed], files: [attachment] });
        } catch (e) {
            await interaction.editReply({ content: `❌ Fehler beim Archivieren: ${e.message}` });
        }
    }
}

module.exports = MessageArchive;
