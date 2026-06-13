const { EmbedBuilder } = require('discord.js');
const fs = require('fs');
const path = require('path');

class CustomCommands {
    constructor(client) {
        this.client = client;
        this.commands = new Map();
        this.loadCommands();
    }

    loadCommands() {
        const filePath = path.join(__dirname, '..', 'custom_commands.json');
        try {
            if (fs.existsSync(filePath)) {
                const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
                for (const [guildId, cmds] of Object.entries(data)) {
                    if (!this.commands.has(guildId)) this.commands.set(guildId, new Map());
                    for (const [name, config] of Object.entries(cmds)) {
                        this.commands.get(guildId).set(name.toLowerCase(), config);
                    }
                }
            }
        } catch (e) {
            console.error('Error loading custom commands:', e);
        }
    }

    saveCommands() {
        const filePath = path.join(__dirname, '..', 'custom_commands.json');
        try {
            const data = {};
            for (const [guildId, cmds] of this.commands) {
                data[guildId] = Object.fromEntries(cmds);
            }
            fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
        } catch (e) {
            console.error('Error saving custom commands:', e);
        }
    }

    async handleCommand(interaction) {
        if (interaction.commandName !== 'command') return;

        const sub = interaction.options.getSubcommand();
        if (sub === 'create') {
            await this.createCommand(interaction);
        } else if (sub === 'delete') {
            await this.deleteCommand(interaction);
        } else if (sub === 'list') {
            await this.listCommands(interaction);
        }
    }

    async createCommand(interaction) {
        if (!interaction.member.permissions.has('ADMINISTRATOR')) {
            return interaction.reply({ content: '❌ Nur Administratoren können benutzerdefinierte Befehle erstellen.', ephemeral: true });
        }

        const name = interaction.options.getString('name').toLowerCase();
        const response = interaction.options.getString('response');
        const embedTitle = interaction.options.getString('embed_title');
        const embedColor = interaction.options.getString('embed_color') || '#6C5CE7';

        if (!/^[a-z0-9_]+$/.test(name)) {
            return interaction.reply({ content: '❌ Der Befehlsname darf nur Kleinbuchstaben, Zahlen und Unterstriche enthalten.', ephemeral: true });
        }

        if (!this.commands.has(interaction.guildId)) {
            this.commands.set(interaction.guildId, new Map());
        }

        const guildCommands = this.commands.get(interaction.guildId);
        guildCommands.set(name, {
            response,
            embedTitle: embedTitle || null,
            embedColor,
            createdBy: interaction.user.id,
            createdAt: new Date().toISOString(),
            uses: 0
        });

        this.saveCommands();

        await interaction.reply({ content: `✅ Befehl \`${name}\` wurde erstellt!`, ephemeral: true });
    }

    async deleteCommand(interaction) {
        if (!interaction.member.permissions.has('ADMINISTRATOR')) {
            return interaction.reply({ content: '❌ Nur Administratoren können Befehle löschen.', ephemeral: true });
        }

        const name = interaction.options.getString('name').toLowerCase();
        const guildCommands = this.commands.get(interaction.guildId);

        if (!guildCommands || !guildCommands.has(name)) {
            return interaction.reply({ content: `❌ Befehl \`${name}\` nicht gefunden.`, ephemeral: true });
        }

        guildCommands.delete(name);
        this.saveCommands();

        await interaction.reply({ content: `✅ Befehl \`${name}\` wurde gelöscht.`, ephemeral: true });
    }

    async listCommands(interaction) {
        const guildCommands = this.commands.get(interaction.guildId);

        if (!guildCommands || guildCommands.size === 0) {
            return interaction.reply({ content: '📝 Keine benutzerdefinierten Befehle auf diesem Server.', ephemeral: true });
        }

        const embed = new EmbedBuilder()
            .setTitle('📝 Benutzerdefinierte Befehle')
            .setColor('#6C5CE7')
            .setDescription(Array.from(guildCommands.entries())
                .map(([name, cmd]) => `**\`${name}\`** - ${cmd.response.substring(0, 50)}${cmd.response.length > 50 ? '...' : ''} (${cmd.uses} Nutzungen)`)
                .join('\n'))
            .setTimestamp();

        await interaction.reply({ embeds: [embed], ephemeral: true });
    }

    async handleMessage(message) {
        if (message.author.bot) return;

        const prefix = '!';
        if (!message.content.startsWith(prefix)) return;

        const args = message.content.slice(prefix.length).split(/\s+/);
        const commandName = args[0].toLowerCase();

        const guildCommands = this.commands.get(message.guildId);
        if (!guildCommands) return;

        const cmd = guildCommands.get(commandName);
        if (!cmd) return;

        cmd.uses = (cmd.uses || 0) + 1;
        this.saveCommands();

        const content = cmd.response.replace(/{user}/g, message.author.toString())
            .replace(/{server}/g, message.guild.name)
            .replace(/{channel}/g, message.channel.name);

        if (cmd.embedTitle) {
            const embed = new EmbedBuilder()
                .setTitle(cmd.embedTitle.replace(/{user}/g, message.author.tag))
                .setDescription(content)
                .setColor(parseInt(cmd.embedColor.replace('#', ''), 16) || 0x6C5CE7)
                .setTimestamp();

            await message.channel.send({ embeds: [embed] });
        } else {
            await message.channel.send(content);
        }
    }

    async handleModalSubmit(interaction) {
        // reserved
    }
}

module.exports = CustomCommands;
