const { EmbedBuilder, ActionRowBuilder, ButtonBuilder, ButtonStyle } = require('discord.js');
const fs = require('fs');
const path = require('path');

class PollCreator {
    constructor(client) {
        this.client = client;
        this.polls = new Map();
        this.loadPolls();
    }

    loadPolls() {
        const filePath = path.join(__dirname, '..', 'polls.json');
        try {
            if (fs.existsSync(filePath)) {
                const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
                for (const [id, poll] of Object.entries(data)) {
                    this.polls.set(id, poll);
                }
            }
        } catch (e) {
            console.error('Error loading polls:', e);
        }
    }

    savePolls() {
        const filePath = path.join(__dirname, '..', 'polls.json');
        try {
            fs.writeFileSync(filePath, JSON.stringify(Object.fromEntries(this.polls), null, 2));
        } catch (e) {
            console.error('Error saving polls:', e);
        }
    }

    async handleCommand(interaction) {
        if (interaction.commandName !== 'poll') return;

        const sub = interaction.options.getSubcommand();
        if (sub === 'create') {
            await this.createPoll(interaction);
        } else if (sub === 'vote') {
            await this.votePoll(interaction);
        } else if (sub === 'results') {
            await this.showResults(interaction);
        }
    }

    async createPoll(interaction) {
        const question = interaction.options.getString('question');
        const options = [
            interaction.options.getString('option1'),
            interaction.options.getString('option2'),
            interaction.options.getString('option3'),
            interaction.options.getString('option4'),
            interaction.options.getString('option5')
        ].filter(Boolean);

        const duration = interaction.options.getInteger('duration') || 0;
        const anonymous = interaction.options.getBoolean('anonymous') || false;

        if (options.length < 2) {
            return interaction.reply({ content: '❌ Bitte mindestens 2 Optionen angeben.', ephemeral: true });
        }

        const pollId = `poll_${Date.now()}`;
        const emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣'];

        const embed = new EmbedBuilder()
            .setTitle(anonymous ? '📊 Anonyme Umfrage' : '📊 Umfrage')
            .setDescription(`**${question}**\n\n${options.map((opt, i) => `${emojis[i]} ${opt}`).join('\n')}`)
            .setColor('#6C5CE7')
            .setFooter({ text: anonymous ? 'Anonyme Abstimmung' : `Erstellt von ${interaction.user.tag}` })
            .setTimestamp();

        if (duration > 0) {
            embed.addFields({ name: '⏱ Dauer', value: `${duration} Minuten`, inline: true });
        }

        const row = new ActionRowBuilder();
        for (let i = 0; i < options.length; i++) {
            row.addComponents(
                new ButtonBuilder().setCustomId(`poll_vote_${pollId}_${i}`).setLabel(emojis[i]).setStyle(ButtonStyle.Primary)
            );
        }

        const msg = await interaction.reply({ embeds: [embed], components: [row], fetchReply: true });

        const poll = {
            id: pollId,
            messageId: msg.id,
            channelId: interaction.channelId,
            question,
            options,
            anonymous,
            votes: options.map(() => []),
            voters: [],
            createdAt: Date.now(),
            duration: duration * 60000,
            authorId: interaction.user.id
        };

        this.polls.set(pollId, poll);
        this.savePolls();

        if (duration > 0) {
            setTimeout(() => this.closePoll(pollId), duration * 60000);
        }
    }

    async handleButton(interaction) {
        if (!interaction.customId.startsWith('poll_vote_')) return;

        const parts = interaction.customId.split('_');
        const pollId = parts.slice(2, -1).join('_');
        const optionIndex = parseInt(parts[parts.length - 1]);

        const poll = this.polls.get(pollId);
        if (!poll) {
            return interaction.reply({ content: '❌ Umfrage nicht gefunden oder abgelaufen.', ephemeral: true });
        }

        if (poll.voters.includes(interaction.user.id)) {
            return interaction.reply({ content: '❌ Du hast bereits abgestimmt.', ephemeral: true });
        }

        poll.votes[optionIndex].push(interaction.user.id);
        poll.voters.push(interaction.user.id);
        this.savePolls();

        await interaction.reply({ content: `✅ Du hast für "${poll.options[optionIndex]}" gestimmt.`, ephemeral: true });
    }

    async votePoll(interaction) {
        const messageId = interaction.options.getString('message_id');
        const option = interaction.options.getInteger('option') - 1;

        let poll = null;
        for (const [, p] of this.polls) {
            if (p.messageId === messageId) { poll = p; break; }
        }

        if (!poll) {
            return interaction.reply({ content: '❌ Umfrage nicht gefunden.', ephemeral: true });
        }

        if (poll.voters.includes(interaction.user.id)) {
            return interaction.reply({ content: '❌ Du hast bereits abgestimmt.', ephemeral: true });
        }

        if (option < 0 || option >= poll.options.length) {
            return interaction.reply({ content: '❌ Ungültige Option.', ephemeral: true });
        }

        poll.votes[option].push(interaction.user.id);
        poll.voters.push(interaction.user.id);
        this.savePolls();

        await interaction.reply({ content: `✅ Du hast für "${poll.options[option]}" gestimmt.`, ephemeral: true });
    }

    async showResults(interaction) {
        const messageId = interaction.options.getString('message_id');

        let poll = null;
        for (const [, p] of this.polls) {
            if (p.messageId === messageId) { poll = p; break; }
        }

        if (!poll) {
            return interaction.reply({ content: '❌ Umfrage nicht gefunden.', ephemeral: true });
        }

        const total = poll.voters.length;
        const emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣'];

        const embed = new EmbedBuilder()
            .setTitle('📊 Umfrage-Ergebnisse')
            .setDescription(`**${poll.question}**\n\nGesamtstimmen: ${total}`)
            .setColor('#6C5CE7')
            .setTimestamp();

        for (let i = 0; i < poll.options.length; i++) {
            const count = poll.votes[i].length;
            const percent = total > 0 ? Math.round((count / total) * 100) : 0;
            const bar = '█'.repeat(Math.floor(percent / 10)) + '░'.repeat(10 - Math.floor(percent / 10));
            embed.addFields({
                name: `${emojis[i]} ${poll.options[i]}`,
                value: `${bar} ${count} Stimmen (${percent}%)`,
                inline: false
            });
        }

        await interaction.reply({ embeds: [embed], ephemeral: true });
    }

    closePoll(pollId) {
        const poll = this.polls.get(pollId);
        if (!poll) return;

        this.showResultsToChannel(poll);
        this.polls.delete(pollId);
        this.savePolls();
    }

    async showResultsToChannel(poll) {
        try {
            const channel = await this.client.channels.fetch(poll.channelId).catch(() => null);
            if (!channel) return;

            const msg = await channel.messages.fetch(poll.messageId).catch(() => null);
            if (!msg) return;

            const total = poll.voters.length;
            const emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣'];

            const embed = new EmbedBuilder()
                .setTitle('📊 Umfrage beendet - Ergebnisse')
                .setDescription(`**${poll.question}**\n\nGesamtstimmen: ${total}`)
                .setColor('#ffd700')
                .setTimestamp();

            for (let i = 0; i < poll.options.length; i++) {
                const count = poll.votes[i].length;
                const percent = total > 0 ? Math.round((count / total) * 100) : 0;
                embed.addFields({
                    name: `${emojis[i]} ${poll.options[i]}`,
                    value: `${count} Stimmen (${percent}%)`,
                    inline: true
                });
            }

            await msg.edit({ embeds: [embed], components: [] });
        } catch (e) {
            console.error('Error closing poll:', e);
        }
    }

    async handleReaction(reaction, user, added) {
        // reserved
    }

    async handleModalSubmit(interaction) {
        // reserved
    }
}

module.exports = PollCreator;
