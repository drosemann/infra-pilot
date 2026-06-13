const { EmbedBuilder, ActionRowBuilder, ButtonBuilder, ButtonStyle } = require('discord.js');
const prettyBytes = require('pretty-bytes');
const si = require('systeminformation');
const mysql = require('mysql2/promise');
require('dotenv').config();

// Updater for the dashboard
// This module manages the dashboard for system, VPS, and Minecraft server statistics

class DashboardManager {
    constructor(client) {
        this.client = client;
        this.dashboards = new Map();
        this.updateInterval = 30000; // Update every 30 seconds
        this.db = null;
        this.initializeDatabase();
    }

    async initializeDatabase() {
        this.db = await mysql.createConnection({
            host: process.env.DB_HOST,
            user: process.env.DB_USER,
            password: process.env.DB_PASSWORD,
            database: process.env.DB_NAME
        });
    }

    async createDashboard(channel, options = {}) {
        const dashboard = {
            channelId: channel.id,
            messages: {
                system: null,
                vps: null,
                minecraft: null
            },
            components: new ActionRowBuilder()
                .addComponents(
                    new ButtonBuilder()
                        .setCustomId('refresh_dashboard')
                        .setLabel('Refresh')
                        .setStyle(ButtonStyle.Primary)
                        .setEmoji('🔄')
                )
        };

        // Create initial dashboard messages
        const systemMsg = await channel.send({ embeds: [await this.createSystemEmbed()] });
        const vpsMsg = await channel.send({ embeds: [await this.createVPSEmbed()] });
        const minecraftMsg = await channel.send({ 
            embeds: [await this.createMinecraftEmbed()],
            components: [dashboard.components]
        });

        dashboard.messages.system = systemMsg;
        dashboard.messages.vps = vpsMsg;
        dashboard.messages.minecraft = minecraftMsg;

        this.dashboards.set(channel.id, dashboard);
        this.startUpdateLoop(channel.id);

        return dashboard;
    }

    async createSystemEmbed() {
        const cpu = await si.cpu();
        const mem = await si.mem();
        const os = await si.osInfo();
        const load = await si.currentLoad();

        return new EmbedBuilder()
            .setTitle('🖥️ System Status')
            .setColor('#00ff00')
            .addFields([
                { 
                    name: 'CPU',
                    value: `${cpu.manufacturer} ${cpu.brand}\nLoad: ${load.currentLoad.toFixed(2)}%`,
                    inline: true
                },
                {
                    name: 'Memory',
                    value: `Used: ${prettyBytes(mem.used)}\nTotal: ${prettyBytes(mem.total)}`,
                    inline: true
                },
                {
                    name: 'System',
                    value: `${os.platform} ${os.release}`,
                    inline: true
                }
            ])
            .setTimestamp();
    }

    async createVPSEmbed() {
        // Get VPS statistics from the manager
        const vpsManager = this.client.vpsManager;
        const instances = vpsManager ? await vpsManager.getAllInstances() : [];

        const embed = new EmbedBuilder()
            .setTitle('🖥️ VPS Instances')
            .setColor('#0099ff')
            .setTimestamp();

        if (instances.length === 0) {
            embed.setDescription('No active VPS instances');
        } else {
            for (const instance of instances) {
                const stats = await vpsManager.get_vps_stats(instance.container_id);
                if (stats) {
                    embed.addFields({
                        name: `Instance ${instance.container_id.slice(0, 12)}`,
                        value: `Status: ${stats.status}\n` +
                               `CPU: ${stats.cpu_usage}%\n` +
                               `RAM: ${stats.memory_usage}%\n` +
                               `Network: ↓${prettyBytes(stats.network.rx_bytes)}/s ↑${prettyBytes(stats.network.tx_bytes)}/s`,
                        inline: true
                    });
                }
            }
        }

        return embed;
    }

    async createMinecraftEmbed() {
        try {
            // Query Minecraft server status
            const [rows] = await this.db.execute(
                'SELECT server_name, status, player_count, max_players, last_updated FROM minecraft_servers'
            );

            const embed = new EmbedBuilder()
                .setTitle('⚡ Minecraft Servers')
                .setColor('#00ff00')
                .setTimestamp();

            if (rows.length === 0) {
                embed.setDescription('No Minecraft servers found');
            } else {
                for (const server of rows) {
                    const status = server.status === 'online' ? '🟢' : '🔴';
                    embed.addFields({
                        name: server.server_name,
                        value: `${status} ${server.status}\n` +
                               `Players: ${server.player_count}/${server.max_players}\n` +
                               `Last Updated: ${new Date(server.last_updated).toLocaleString()}`,
                        inline: true
                    });
                }
            }

            return embed;
        } catch (error) {
            console.error('Error creating Minecraft embed:', error);
            return new EmbedBuilder()
                .setTitle('⚡ Minecraft Servers')
                .setDescription('Error fetching server status')
                .setColor('#ff0000')
                .setTimestamp();
        }
    }

    async updateDashboard(channelId) {
        const dashboard = this.dashboards.get(channelId);
        if (!dashboard) return;

        try {
            await dashboard.messages.system.edit({ embeds: [await this.createSystemEmbed()] });
            await dashboard.messages.vps.edit({ embeds: [await this.createVPSEmbed()] });
            await dashboard.messages.minecraft.edit({ 
                embeds: [await this.createMinecraftEmbed()],
                components: [dashboard.components]
            });
        } catch (error) {
            console.error(`Error updating dashboard in channel ${channelId}:`, error);
        }
    }

    startUpdateLoop(channelId) {
        setInterval(() => this.updateDashboard(channelId), this.updateInterval);
    }

    async handleRefreshButton(interaction) {
        await interaction.deferUpdate();
        const dashboard = this.dashboards.get(interaction.channelId);
        
        if (dashboard) {
            await this.updateDashboard(interaction.channelId);
        }
    }

    async handleDashboardCommand(interaction) {
        const channel = interaction.channel;
        
        // Check permissions
        if (!interaction.member.permissions.has('ADMINISTRATOR')) {
            await interaction.reply({
                content: 'You need administrator permissions to create a dashboard.',
                ephemeral: true
            });
            return;
        }

        await interaction.deferReply();

        try {
            const dashboard = await this.createDashboard(channel);
            await interaction.editReply('Dashboard created successfully!');
        } catch (error) {
            console.error('Error creating dashboard:', error);
            await interaction.editReply('Failed to create dashboard. Please check the bot permissions and try again.');
        }
    }
}

module.exports = DashboardManager;