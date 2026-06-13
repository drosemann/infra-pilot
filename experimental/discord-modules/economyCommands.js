const { SlashCommandBuilder } = require('@discordjs/builders');
const { EmbedBuilder, PermissionFlagsBits } = require('discord.js');
const mysql = require('mysql2/promise');
require('dotenv').config();

class EconomyCommands {
    constructor(client) {
        this.client = client;
        this.db = null;
        this.initializeDatabase();
        this.commands = this.createCommands();
    }

    async initializeDatabase() {
        this.db = await mysql.createConnection({
            host: process.env.DB_HOST,
            user: process.env.DB_USER,
            password: process.env.DB_PASSWORD,
            database: process.env.DB_NAME
        });
    }

    createCommands() {
        return [
            new SlashCommandBuilder()
                .setName('balance')
                .setDescription('Check your balance')
                .addUserOption(option =>
                    option.setName('user')
                        .setDescription('User to check balance for (staff only)')
                        .setRequired(false)
                ),

            new SlashCommandBuilder()
                .setName('pay')
                .setDescription('Pay another user')
                .addUserOption(option =>
                    option.setName('user')
                        .setDescription('User to pay')
                        .setRequired(true)
                )
                .addNumberOption(option =>
                    option.setName('amount')
                        .setDescription('Amount to pay')
                        .setRequired(true)
                ),

            new SlashCommandBuilder()
                .setName('baltop')
                .setDescription('View top balances'),

            new SlashCommandBuilder()
                .setName('ecoadmin')
                .setDescription('Manage user balances (Admin only)')
                .setDefaultMemberPermissions(PermissionFlagsBits.Administrator)
                .addSubcommand(subcommand =>
                    subcommand
                        .setName('give')
                        .setDescription('Give money to a user')
                        .addUserOption(option =>
                            option.setName('user')
                                .setDescription('User to give money to')
                                .setRequired(true)
                        )
                        .addNumberOption(option =>
                            option.setName('amount')
                                .setDescription('Amount to give')
                                .setRequired(true)
                        )
                )
                .addSubcommand(subcommand =>
                    subcommand
                        .setName('take')
                        .setDescription('Take money from a user')
                        .addUserOption(option =>
                            option.setName('user')
                                .setDescription('User to take money from')
                                .setRequired(true)
                        )
                        .addNumberOption(option =>
                            option.setName('amount')
                                .setDescription('Amount to take')
                                .setRequired(true)
                        )
                )
        ].map(command => command.toJSON());
    }

    async handleCommand(interaction) {
        if (!interaction.isCommand()) return;

        switch (interaction.commandName) {
            case 'balance':
                await this.handleBalanceCommand(interaction);
                break;
            case 'pay':
                await this.handlePayCommand(interaction);
                break;
            case 'baltop':
                await this.handleBalanceTopCommand(interaction);
                break;
            case 'ecoadmin':
                await this.handleEcoAdminCommand(interaction);
                break;
        }
    }

    async handleBalanceCommand(interaction) {
        await interaction.deferReply();

        const target = interaction.options.getUser('user') || interaction.user;
        
        if (target !== interaction.user && !interaction.member.permissions.has('ADMINISTRATOR')) {
            await interaction.editReply('You do not have permission to check other users\' balances.');
            return;
        }

        try {
            const [rows] = await this.db.execute(
                'SELECT balance FROM player_economy WHERE uuid = ?',
                [target.id]
            );

            const balance = rows[0]?.balance || 0;
            const embed = new EmbedBuilder()
                .setTitle(`${target.username}'s Balance`)
                .setDescription(`Balance: $${balance.toFixed(2)}`)
                .setColor('#00ff00')
                .setTimestamp();

            await interaction.editReply({ embeds: [embed] });
        } catch (error) {
            console.error('Error checking balance:', error);
            await interaction.editReply('An error occurred while checking the balance.');
        }
    }

    async handlePayCommand(interaction) {
        await interaction.deferReply();

        const target = interaction.options.getUser('user');
        const amount = interaction.options.getNumber('amount');

        if (target.id === interaction.user.id) {
            await interaction.editReply('You cannot pay yourself.');
            return;
        }

        if (amount <= 0) {
            await interaction.editReply('Amount must be positive.');
            return;
        }

        try {
            await this.db.beginTransaction();

            // Check sender's balance
            const [senderRows] = await this.db.execute(
                'SELECT balance FROM player_economy WHERE uuid = ?',
                [interaction.user.id]
            );

            const senderBalance = senderRows[0]?.balance || 0;

            if (senderBalance < amount) {
                await this.db.rollback();
                await interaction.editReply('Insufficient funds.');
                return;
            }

            // Update sender's balance
            await this.db.execute(
                'UPDATE player_economy SET balance = balance - ? WHERE uuid = ?',
                [amount, interaction.user.id]
            );

            // Update receiver's balance
            await this.db.execute(
                `INSERT INTO player_economy (uuid, balance) 
                VALUES (?, ?) 
                ON DUPLICATE KEY UPDATE balance = balance + ?`,
                [target.id, amount, amount]
            );

            await this.db.commit();

            const embed = new EmbedBuilder()
                .setTitle('Payment Successful')
                .setDescription(`You sent $${amount.toFixed(2)} to ${target.username}`)
                .setColor('#00ff00')
                .setTimestamp();

            await interaction.editReply({ embeds: [embed] });

            // Notify receiver
            try {
                await target.send(`${interaction.user.username} sent you $${amount.toFixed(2)}`);
            } catch (error) {
                // User might have DMs disabled
            }
        } catch (error) {
            await this.db.rollback();
            console.error('Error processing payment:', error);
            await interaction.editReply('An error occurred while processing the payment.');
        }
    }

    async handleBalanceTopCommand(interaction) {
        await interaction.deferReply();

        try {
            const [rows] = await this.db.execute(
                'SELECT uuid, balance FROM player_economy ORDER BY balance DESC LIMIT 10'
            );

            const embed = new EmbedBuilder()
                .setTitle('Top 10 Richest Players')
                .setColor('#ffd700')
                .setTimestamp();

            for (let i = 0; i < rows.length; i++) {
                const user = await this.client.users.fetch(rows[i].uuid).catch(() => null);
                const username = user ? user.username : 'Unknown User';
                embed.addFields({
                    name: `#${i + 1} ${username}`,
                    value: `$${rows[i].balance.toFixed(2)}`,
                    inline: false
                });
            }

            await interaction.editReply({ embeds: [embed] });
        } catch (error) {
            console.error('Error fetching top balances:', error);
            await interaction.editReply('An error occurred while fetching top balances.');
        }
    }

    async handleEcoAdminCommand(interaction) {
        if (!interaction.member.permissions.has('ADMINISTRATOR')) {
            await interaction.reply({ content: 'You do not have permission to use this command.', ephemeral: true });
            return;
        }

        await interaction.deferReply();

        const subcommand = interaction.options.getSubcommand();
        const target = interaction.options.getUser('user');
        const amount = interaction.options.getNumber('amount');

        try {
            if (subcommand === 'give') {
                await this.db.execute(
                    `INSERT INTO player_economy (uuid, balance) 
                    VALUES (?, ?) 
                    ON DUPLICATE KEY UPDATE balance = balance + ?`,
                    [target.id, amount, amount]
                );

                await interaction.editReply(`Added $${amount.toFixed(2)} to ${target.username}'s balance.`);
            } else if (subcommand === 'take') {
                const [rows] = await this.db.execute(
                    'SELECT balance FROM player_economy WHERE uuid = ?',
                    [target.id]
                );

                const currentBalance = rows[0]?.balance || 0;

                if (currentBalance < amount) {
                    await interaction.editReply(`${target.username} does not have enough funds.`);
                    return;
                }

                await this.db.execute(
                    'UPDATE player_economy SET balance = balance - ? WHERE uuid = ?',
                    [amount, target.id]
                );

                await interaction.editReply(`Removed $${amount.toFixed(2)} from ${target.username}'s balance.`);
            }
        } catch (error) {
            console.error('Error processing admin command:', error);
            await interaction.editReply('An error occurred while processing the command.');
        }
    }
}

module.exports = EconomyCommands;