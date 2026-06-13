const fs = require('fs');
const path = require('path');

class PrefixSettings {
    constructor(client) {
        this.client = client;
        this.prefixes = new Map();
        this.defaultPrefix = '!';
        this.loadPrefixes();
    }

    loadPrefixes() {
        const filePath = path.join(__dirname, '..', 'prefixes.json');
        try {
            if (fs.existsSync(filePath)) {
                this.prefixes = new Map(Object.entries(JSON.parse(fs.readFileSync(filePath, 'utf8'))));
            }
        } catch (e) {
            console.error('Error loading prefixes:', e);
        }
    }

    savePrefixes() {
        const filePath = path.join(__dirname, '..', 'prefixes.json');
        try {
            fs.writeFileSync(filePath, JSON.stringify(Object.fromEntries(this.prefixes), null, 2));
        } catch (e) {
            console.error('Error saving prefixes:', e);
        }
    }

    getPrefix(guildId) {
        return this.prefixes.get(guildId) || this.defaultPrefix;
    }

    async handleCommand(interaction) {
        if (interaction.commandName !== 'prefix') return;

        const sub = interaction.options.getSubcommand();

        if (sub === 'set') {
            await this.setPrefix(interaction);
        } else if (sub === 'reset') {
            await this.resetPrefix(interaction);
        }
    }

    async setPrefix(interaction) {
        if (!interaction.member.permissions.has('ADMINISTRATOR')) {
            return interaction.reply({ content: '❌ Nur Administratoren können das Prefix ändern.', ephemeral: true });
        }

        const newPrefix = interaction.options.getString('prefix');

        if (newPrefix.length > 5) {
            return interaction.reply({ content: '❌ Das Prefix darf maximal 5 Zeichen lang sein.', ephemeral: true });
        }

        this.prefixes.set(interaction.guildId, newPrefix);
        this.savePrefixes();

        await interaction.reply({ content: `✅ Prefix wurde zu \`${newPrefix}\` geändert.`, ephemeral: true });
    }

    async resetPrefix(interaction) {
        if (!interaction.member.permissions.has('ADMINISTRATOR')) {
            return interaction.reply({ content: '❌ Nur Administratoren können das Prefix zurücksetzen.', ephemeral: true });
        }

        this.prefixes.delete(interaction.guildId);
        this.savePrefixes();

        await interaction.reply({ content: `✅ Prefix wurde auf \`${this.defaultPrefix}\` zurückgesetzt.`, ephemeral: true });
    }
}

module.exports = PrefixSettings;
