const { EmbedBuilder, ActionRowBuilder, ButtonBuilder, ButtonStyle, ModalBuilder, TextInputBuilder, TextInputStyle } = require('discord.js');
const fs = require('fs');
const path = require('path');
const cron = require('node-cron');

class EventScheduler {
    constructor(client) {
        this.client = client;
        this.events = [];
        this.reminders = new Map();
        this.loadEvents();
    }

    loadEvents() {
        const filePath = path.join(__dirname, '..', 'scheduled_events.json');
        try {
            if (fs.existsSync(filePath)) {
                this.events = JSON.parse(fs.readFileSync(filePath, 'utf8'));
                this.scheduleAll();
            }
        } catch (e) {
            console.error('Error loading events:', e);
        }
    }

    saveEvents() {
        const filePath = path.join(__dirname, '..', 'scheduled_events.json');
        try {
            fs.writeFileSync(filePath, JSON.stringify(this.events, null, 2));
        } catch (e) {
            console.error('Error saving events:', e);
        }
    }

    parseTime(timeStr) {
        if (timeStr.startsWith('in ')) {
            const match = timeStr.match(/in (\d+)([mhd])/);
            if (match) {
                const num = parseInt(match[1]);
                const unit = match[2];
                const now = Date.now();
                if (unit === 'm') return new Date(now + num * 60000);
                if (unit === 'h') return new Date(now + num * 3600000);
                if (unit === 'd') return new Date(now + num * 86400000);
            }
        }
        const d = new Date(timeStr);
        return isNaN(d.getTime()) ? null : d;
    }

    parseReminderTime(timeStr) {
        const match = timeStr.match(/(\d+)([mh])/);
        if (match) {
            const num = parseInt(match[1]);
            const unit = match[2];
            if (unit === 'm') return num * 60000;
            if (unit === 'h') return num * 3600000;
        }
        return 60000;
    }

    scheduleAll() {
        for (const event of this.events) {
            this.scheduleEvent(event);
        }
    }

    scheduleEvent(event) {
        const eventTime = new Date(event.time).getTime();
        const now = Date.now();
        const delay = eventTime - now;

        if (delay > 0) {
            setTimeout(() => this.triggerEvent(event), delay);
        }

        if (event.reminders) {
            for (const reminder of event.reminders) {
                const reminderTime = eventTime - reminder.offset;
                const remDelay = reminderTime - now;
                if (remDelay > 0) {
                    setTimeout(() => this.triggerReminder(event, reminder), remDelay);
                }
            }
        }

        if (event.recurring && event.recurring !== 'none') {
            this.scheduleRecurring(event);
        }
    }

    scheduleRecurring(event) {
        const intervals = { daily: '0 0 * * *', weekly: '0 0 * * 0', monthly: '0 0 1 * *' };
        const expr = intervals[event.recurring];
        if (expr && cron.validate(expr)) {
            cron.schedule(expr, () => {
                const newEvent = { ...event, time: new Date(Date.now() + 86400000).toISOString(), id: Date.now().toString() };
                this.events.push(newEvent);
                this.saveEvents();
                this.scheduleEvent(newEvent);
            });
        }
    }

    async triggerEvent(event) {
        try {
            const guild = this.client.guilds.cache.first();
            if (!guild) return;

            const channel = guild.channels.cache.find(c => c.name === 'events' || c.name === 'announcements');
            if (!channel) return;

            const embed = new EmbedBuilder()
                .setTitle(`📅 Event: ${event.name}`)
                .setDescription(event.description)
                .setColor('#6C5CE7')
                .setTimestamp();

            const content = event.roleId ? `<@&${event.roleId}>` : '';

            const row = new ActionRowBuilder().addComponents(
                new ButtonBuilder().setCustomId('event_remind').setLabel('Erinnern').setStyle(ButtonStyle.Secondary).setEmoji('🔔')
            );

            await channel.send({ content, embeds: [embed], components: [row] });
        } catch (e) {
            console.error('Error triggering event:', e);
        }
    }

    async triggerReminder(event, reminder) {
        try {
            const guild = this.client.guilds.cache.first();
            if (!guild) return;

            const channel = guild.channels.cache.find(c => c.name === 'events' || c.name === 'announcements');
            if (!channel) return;

            const embed = new EmbedBuilder()
                .setTitle(`🔔 Erinnerung: ${event.name}`)
                .setDescription(`Das Event beginnt in Kürze!`)
                .setColor('#ffa500')
                .setTimestamp();

            await channel.send({ embeds: [embed] });
        } catch (e) {
            console.error('Error triggering reminder:', e);
        }
    }

    async handleCommand(interaction) {
        if (interaction.commandName !== 'event') return;

        const sub = interaction.options.getSubcommand();
        if (sub === 'create') {
            await this.createEvent(interaction);
        } else if (sub === 'list') {
            await this.listEvents(interaction);
        } else if (sub === 'remind') {
            await this.setReminder(interaction);
        }
    }

    async createEvent(interaction) {
        const name = interaction.options.getString('name');
        const description = interaction.options.getString('description');
        const timeStr = interaction.options.getString('time');
        const recurring = interaction.options.getString('recurring') || 'none';
        const role = interaction.options.getRole('role');

        const eventTime = this.parseTime(timeStr);
        if (!eventTime) {
            return interaction.reply({ content: '❌ Ungültiges Datum/Zeit. Nutze ISO-Format oder "in 2h".', ephemeral: true });
        }

        const event = {
            id: Date.now().toString(),
            name,
            description,
            time: eventTime.toISOString(),
            recurring,
            roleId: role?.id || null,
            createdAt: new Date().toISOString(),
            reminders: []
        };

        this.events.push(event);
        this.saveEvents();
        this.scheduleEvent(event);

        const embed = new EmbedBuilder()
            .setTitle('✅ Event erstellt')
            .setDescription(`**${name}**\n${description}`)
            .addFields([
                { name: 'Zeit', value: eventTime.toLocaleString('de-DE'), inline: true },
                { name: 'Wiederholung', value: recurring, inline: true },
                { name: 'ID', value: event.id, inline: true }
            ])
            .setColor('#6C5CE7')
            .setTimestamp();

        await interaction.reply({ embeds: [embed], ephemeral: true });
    }

    async listEvents(interaction) {
        const upcoming = this.events
            .filter(e => new Date(e.time).getTime() > Date.now())
            .sort((a, b) => new Date(a.time) - new Date(b.time))
            .slice(0, 10);

        if (upcoming.length === 0) {
            return interaction.reply({ content: '📅 Keine bevorstehenden Events.', ephemeral: true });
        }

        const embed = new EmbedBuilder()
            .setTitle('📅 Bevorstehende Events')
            .setColor('#6C5CE7')
            .setTimestamp();

        for (const event of upcoming) {
            const time = new Date(event.time).toLocaleString('de-DE');
            embed.addFields({
                name: `${event.name} (ID: ${event.id})`,
                value: `🕐 ${time}\n🔄 ${event.recurring}\n${event.description.substring(0, 100)}`,
                inline: false
            });
        }

        await interaction.reply({ embeds: [embed], ephemeral: true });
    }

    async setReminder(interaction) {
        const eventId = interaction.options.getString('id');
        const reminderTime = interaction.options.getString('time');

        const event = this.events.find(e => e.id === eventId);
        if (!event) {
            return interaction.reply({ content: '❌ Event nicht gefunden.', ephemeral: true });
        }

        const offset = this.parseReminderTime(reminderTime);
        const reminder = { offset, createdAt: new Date().toISOString() };
        event.reminders.push(reminder);
        this.saveEvents();

        await interaction.reply({ content: `✅ Erinnerung für Event "${event.name}" in ${reminderTime} eingerichtet.`, ephemeral: true });
    }

    async handleModalSubmit(interaction) {
        // reserved
    }
}

module.exports = EventScheduler;
