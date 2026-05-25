const cron = require('node-cron');
const fs = require('fs');
const path = require('path');

class MessageScheduler {
    constructor(client) {
        this.client = client;
        this.scheduledMessages = [];
        this.jobs = new Map();
        this.loadMessages();
    }

    loadMessages() {
        const filePath = path.join(__dirname, '..', 'scheduled_messages.json');
        try {
            if (fs.existsSync(filePath)) {
                this.scheduledMessages = JSON.parse(fs.readFileSync(filePath, 'utf8'));
            }
        } catch (e) {
            console.error('Error loading scheduled messages:', e);
        }
    }

    saveMessages() {
        const filePath = path.join(__dirname, '..', 'scheduled_messages.json');
        try {
            fs.writeFileSync(filePath, JSON.stringify(this.scheduledMessages, null, 2));
        } catch (e) {
            console.error('Error saving scheduled messages:', e);
        }
    }

    initialize(client) {
        for (const msg of this.scheduledMessages) {
            this.scheduleMessage(msg);
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

    scheduleMessage(msg) {
        if (msg.recurring && cron.validate(msg.recurring)) {
            const job = cron.schedule(msg.recurring, () => this.sendMessage(msg));
            this.jobs.set(msg.id, job);
        } else {
            const targetTime = new Date(msg.time).getTime();
            const delay = targetTime - Date.now();
            if (delay > 0) {
                const timeout = setTimeout(() => this.sendMessage(msg), delay);
                this.jobs.set(msg.id, timeout);
            }
        }
    }

    async sendMessage(msg) {
        try {
            const channel = await this.client.channels.fetch(msg.channelId).catch(() => null);
            if (!channel) return;

            const content = msg.content
                .replace(/{time}/g, new Date().toLocaleString('de-DE'))
                .replace(/{date}/g, new Date().toLocaleDateString('de-DE'));

            await channel.send(content);
        } catch (e) {
            console.error('Error sending scheduled message:', e.message);
        }
    }

    async handleCommand(interaction) {
        if (interaction.commandName !== 'schedule') return;

        const sub = interaction.options.getSubcommand();
        if (sub === 'message') {
            await this.scheduleNewMessage(interaction);
        }
    }

    async scheduleNewMessage(interaction) {
        if (!interaction.member.permissions.has('ADMINISTRATOR')) {
            return interaction.reply({ content: '❌ Nur Administratoren können Nachrichten planen.', ephemeral: true });
        }

        const channel = interaction.options.getChannel('channel');
        const content = interaction.options.getString('content');
        const timeStr = interaction.options.getString('time');
        const recurring = interaction.options.getString('recurring');

        const targetTime = this.parseTime(timeStr);
        if (!targetTime) {
            return interaction.reply({ content: '❌ Ungültiges Datum/Zeit. Nutze ISO-Format oder "in 30m".', ephemeral: true });
        }

        const msg = {
            id: `sched_${Date.now()}`,
            channelId: channel.id,
            content,
            time: targetTime.toISOString(),
            recurring: recurring || null,
            createdAt: new Date().toISOString(),
            authorId: interaction.user.id
        };

        this.scheduledMessages.push(msg);
        this.saveMessages();
        this.scheduleMessage(msg);

        await interaction.reply({
            content: `✅ Nachricht geplant für ${targetTime.toLocaleString('de-DE')} in ${channel}${recurring ? ` (wiederholend: ${recurring})` : ''}`,
            ephemeral: true
        });
    }
}

module.exports = MessageScheduler;
