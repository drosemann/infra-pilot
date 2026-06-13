const { EmbedBuilder, ButtonBuilder, ActionRowBuilder, ButtonStyle, StringSelectMenuBuilder, ModalBuilder, TextInputBuilder, TextInputStyle, PermissionFlagsBits } = require('discord.js');
const fs = require('fs');
const path = require('path');

class AdvancedTicketSystem {
    constructor(client, ticketSystem) {
        this.client = client;
        this.ticketSystem = ticketSystem;
        this.pendingRatings = new Map();
        this.templates = new Map();
        this.loadTemplates();
    }

    loadTemplates() {
        const filePath = path.join(__dirname, '..', 'ticket_templates.json');
        try {
            if (fs.existsSync(filePath)) {
                this.templates = new Map(Object.entries(JSON.parse(fs.readFileSync(filePath, 'utf8'))));
            }
        } catch (e) {
            console.error('Error loading ticket templates:', e);
        }
    }

    saveTemplates() {
        const filePath = path.join(__dirname, '..', 'ticket_templates.json');
        try {
            fs.writeFileSync(filePath, JSON.stringify(Object.fromEntries(this.templates), null, 2));
        } catch (e) {
            console.error('Error saving ticket templates:', e);
        }
    }

    async handleCommand(interaction) {
        if (interaction.commandName !== 'ticket') return;
        const sub = interaction.options.getSubcommand();

        if (sub === 'panel') {
            await this.createCategoryPanel(interaction);
        } else if (sub === 'priority') {
            await this.setPriority(interaction);
        } else if (sub === 'close') {
            await this.closeWithRating(interaction);
        }
    }

    async createCategoryPanel(interaction) {
        const select = new StringSelectMenuBuilder()
            .setCustomId('ticket_category')
            .setPlaceholder('Wähle eine Kategorie')
            .addOptions([
                { label: 'Support', value: 'support', description: 'Allgemeiner Support', emoji: '❓' },
                { label: 'Bug Report', value: 'bug', description: 'Einen Fehler melden', emoji: '🐛' },
                { label: 'Feature Request', value: 'feature', description: 'Feature vorschlagen', emoji: '💡' },
                { label: 'Beschwerde', value: 'complaint', description: 'Beschwerde einreichen', emoji: '⚠️' },
                { label: 'Sonstiges', value: 'other', description: 'Anderes Anliegen', emoji: '📋' }
            ]);

        const row = new ActionRowBuilder().addComponents(select);
        const embed = new EmbedBuilder()
            .setTitle('🎫 Ticket erstellen')
            .setDescription('Wähle eine Kategorie für dein Ticket aus.')
            .setColor('#6C5CE7');

        await interaction.reply({ embeds: [embed], components: [row], ephemeral: true });
    }

    async handleSelectMenu(interaction) {
        if (interaction.customId !== 'ticket_category') return;

        const category = interaction.values[0];
        const modal = new ModalBuilder()
            .setCustomId(`ticket_modal_${category}`)
            .setTitle('Ticket erstellen');

        const titleInput = new TextInputBuilder()
            .setCustomId('ticket_title')
            .setLabel('Titel')
            .setStyle(TextInputStyle.Short)
            .setRequired(true)
            .setMaxLength(100);

        const descInput = new TextInputBuilder()
            .setCustomId('ticket_description')
            .setLabel('Beschreibung')
            .setStyle(TextInputStyle.Paragraph)
            .setRequired(true)
            .setMaxLength(1000);

        modal.addComponents(
            new ActionRowBuilder().addComponents(titleInput),
            new ActionRowBuilder().addComponents(descInput)
        );

        await interaction.showModal(modal);
    }

    async handleModalSubmit(interaction) {
        if (interaction.customId === 'ticket_rating') {
            await this.handleRatingSubmit(interaction);
            return;
        }
        if (!interaction.customId.startsWith('ticket_modal_')) return;

        const category = interaction.customId.replace('ticket_modal_', '');
        const title = interaction.fields.getTextInputValue('ticket_title');
        const description = interaction.fields.getTextInputValue('ticket_description');

        const ticketId = ++this.ticketSystem.ticketCounter;
        const ticketChannel = await this.ticketSystem.createTicketChannel(interaction, ticketId);

        if (!ticketChannel) {
            return interaction.reply({ content: '❌ Fehler beim Erstellen des Ticket-Kanals.', ephemeral: true });
        }

        this.ticketSystem.tickets.set(ticketChannel.id, {
            id: ticketId,
            userId: interaction.user.id,
            status: 'open',
            priority: 'medium',
            category: category,
            title: title,
            createdAt: new Date(),
            messages: []
        });

        const embed = new EmbedBuilder()
            .setTitle(`🎫 Ticket #${ticketId} - ${title}`)
            .setDescription(description)
            .addFields([
                { name: 'Kategorie', value: category, inline: true },
                { name: 'Priorität', value: '🟡 Medium', inline: true },
                { name: 'Erstellt von', value: interaction.user.toString(), inline: true }
            ])
            .setColor('#6C5CE7')
            .setTimestamp();

        const row = new ActionRowBuilder().addComponents(
            new ButtonBuilder().setCustomId('close_ticket').setLabel('Schließen').setStyle(ButtonStyle.Danger).setEmoji('🔒'),
            new ButtonBuilder().setCustomId('ticket_priority').setLabel('Priorität').setStyle(ButtonStyle.Secondary).setEmoji('📊')
        );

        await ticketChannel.send({ embeds: [embed], components: [row] });

        await interaction.reply({ content: `✅ Ticket erstellt! ${ticketChannel}`, ephemeral: true });
    }

    async setPriority(interaction) {
        const channel = interaction.channel;
        if (!channel.name.startsWith('ticket-')) {
            return interaction.reply({ content: '❌ Dies ist kein Ticket-Kanal.', ephemeral: true });
        }

        const ticket = this.ticketSystem.tickets.get(channel.id);
        if (!ticket) return interaction.reply({ content: '❌ Ticket nicht gefunden.', ephemeral: true });

        const level = interaction.options.getString('level');
        ticket.priority = level;

        const colors = { low: '🟢', medium: '🟡', high: '🟠', critical: '🔴' };
        await interaction.reply({ content: `✅ Priorität auf ${colors[level] || '🟡'} ${level} gesetzt.`, ephemeral: true });
    }

    async handleButton(interaction) {
        if (interaction.customId === 'ticket_priority') {
            const channel = interaction.channel;
            if (!channel.name.startsWith('ticket-')) {
                return interaction.reply({ content: '❌ Dies ist kein Ticket-Kanal.', ephemeral: true });
            }

            const select = new StringSelectMenuBuilder()
                .setCustomId('ticket_set_priority')
                .setPlaceholder('Priorität wählen')
                .addOptions([
                    { label: 'Low', value: 'low', emoji: '🟢' },
                    { label: 'Medium', value: 'medium', emoji: '🟡' },
                    { label: 'High', value: 'high', emoji: '🟠' },
                    { label: 'Critical', value: 'critical', emoji: '🔴' }
                ]);

            const row = new ActionRowBuilder().addComponents(select);
            await interaction.reply({ components: [row], ephemeral: true });
        }
    }

    async handleUserSelect(interaction) {
        // reserved for future staff assignment
    }

    async closeWithRating(interaction) {
        const channel = interaction.channel;
        const ticket = this.ticketSystem.tickets.get(channel.id);
        if (!ticket || ticket.userId !== interaction.user.id) {
            return interaction.reply({ content: '❌ Du kannst nur deine eigenen Tickets schließen.', ephemeral: true });
        }

        const modal = new ModalBuilder()
            .setCustomId('ticket_rating')
            .setTitle('Ticket bewerten');

        const ratingInput = new TextInputBuilder()
            .setCustomId('rating_score')
            .setLabel('Bewertung (1-5)')
            .setStyle(TextInputStyle.Short)
            .setRequired(true)
            .setMaxLength(1);

        const feedbackInput = new TextInputBuilder()
            .setCustomId('rating_feedback')
            .setLabel('Feedback (optional)')
            .setStyle(TextInputStyle.Paragraph)
            .setRequired(false)
            .setMaxLength(500);

        modal.addComponents(
            new ActionRowBuilder().addComponents(ratingInput),
            new ActionRowBuilder().addComponents(feedbackInput)
        );

        this.pendingRatings.set(interaction.user.id, channel.id);
        await interaction.showModal(modal);
    }

    async handleRatingSubmit(interaction) {
        const channelId = this.pendingRatings.get(interaction.user.id);
        if (!channelId) return;

        const rating = parseInt(interaction.fields.getTextInputValue('rating_score'));
        const feedback = interaction.fields.getTextInputValue('rating_feedback');

        if (rating < 1 || rating > 5) {
            return interaction.reply({ content: '❌ Bitte gib eine Zahl zwischen 1 und 5 ein.', ephemeral: true });
        }

        const ticket = this.ticketSystem.tickets.get(channelId);
        if (ticket) {
            ticket.rating = rating;
            ticket.feedback = feedback;
            ticket.status = 'closed';

            const embed = new EmbedBuilder()
                .setTitle('📝 Ticket geschlossen')
                .setDescription(`Ticket #${ticket.id} wurde geschlossen.`)
                .addFields([
                    { name: 'Bewertung', value: '⭐'.repeat(rating), inline: true },
                    { name: 'Feedback', value: feedback || 'Kein Feedback', inline: false }
                ])
                .setColor('#00ff00')
                .setTimestamp();

            await interaction.reply({ embeds: [embed], ephemeral: true });

            const user = await this.client.users.fetch(ticket.userId).catch(() => null);
            if (user) {
                await user.send({ embeds: [embed] }).catch(() => {});
            }

            await interaction.channel.delete();
            this.ticketSystem.tickets.delete(channelId);
        }

        this.pendingRatings.delete(interaction.user.id);
    }
}

module.exports = AdvancedTicketSystem;
