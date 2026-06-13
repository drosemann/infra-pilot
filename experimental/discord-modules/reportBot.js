const { EmbedBuilder, ActionRowBuilder, ButtonBuilder, ButtonStyle } = require('discord.js');
const axios = require('axios');
const fs = require('fs');
const path = require('path');
const cron = require('node-cron');

const DATA_FILE = path.join(__dirname, '..', 'data', 'reportBot.json');
const API_BASE = process.env.API_BASE_URL || 'http://localhost:3001';

class ReportBot {
    constructor(client) {
        this.client = client;
        this.schedules = new Map();
        this.data = this.loadData();
    }

    loadData() {
        try {
            if (fs.existsSync(DATA_FILE)) {
                return JSON.parse(fs.readFileSync(DATA_FILE, 'utf8'));
            }
        } catch (e) {
            console.error('[ReportBot] Error loading data:', e.message);
        }
        return { schedules: [], deliveryLog: [] };
    }

    saveData() {
        try {
            const dir = path.dirname(DATA_FILE);
            if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
            fs.writeFileSync(DATA_FILE, JSON.stringify(this.data, null, 2));
        } catch (e) {
            console.error('[ReportBot] Error saving data:', e.message);
        }
    }

    initialize(client) {
        for (const sched of this.data.schedules) {
            if (sched.enabled && sched.cron) {
                this.startSchedule(sched);
            }
        }
        console.log(`[ReportBot] Loaded ${this.data.schedules.length} report schedules`);
    }

    startSchedule(sched) {
        if (this.schedules.has(sched.id)) {
            this.schedules.get(sched.id).stop();
        }
        if (!cron.validate(sched.cron)) {
            console.error(`[ReportBot] Invalid cron for schedule ${sched.id}: ${sched.cron}`);
            return;
        }
        const task = cron.schedule(sched.cron, async () => {
            await this.deliverReport(sched);
        });
        this.schedules.set(sched.id, task);
        console.log(`[ReportBot] Started schedule ${sched.id}: "${sched.name}" (${sched.cron})`);
    }

    stopSchedule(id) {
        if (this.schedules.has(id)) {
            this.schedules.get(id).stop();
            this.schedules.delete(id);
        }
    }

    async handleCommand(interaction) {
        if (interaction.commandName !== 'report') return;
        const sub = interaction.options.getSubcommand();

        switch (sub) {
            case 'send':
                await this.sendReportCommand(interaction);
                break;
            case 'schedule':
                await this.scheduleReportCommand(interaction);
                break;
            case 'list':
                await this.listSchedulesCommand(interaction);
                break;
            case 'delete':
                await this.deleteScheduleCommand(interaction);
                break;
            case 'digest':
                await this.sendDigestCommand(interaction);
                break;
            default:
                await interaction.reply({ content: 'Unknown subcommand. Use: send, schedule, list, delete, digest', ephemeral: true });
        }
    }

    async handleButton(interaction) {
        const id = interaction.customId;
        if (id === 'report_refresh') {
            await interaction.deferUpdate();
            const embed = await this.createReportEmbed('executive-summary', '1h');
            await interaction.editReply({ embeds: [embed] });
        } else if (id.startsWith('report_export_')) {
            const type = id.replace('report_export_', '');
            await interaction.reply({ content: `Exporting ${type} report as PDF... (simulated)`, ephemeral: true });
        } else if (id.startsWith('report_view_')) {
            const type = id.replace('report_view_', '');
            await interaction.deferUpdate();
            const embed = await this.createReportEmbed(type, '24h');
            await interaction.editReply({ embeds: [embed] });
        }
    }

    async sendReportCommand(interaction) {
        await interaction.deferReply({ ephemeral: true });
        const type = interaction.options.getString('type') || 'executive-summary';
        const period = interaction.options.getString('period') || '24h';
        const embed = await this.createReportEmbed(type, period);
        const row = new ActionRowBuilder().addComponents(
            new ButtonBuilder().setCustomId('report_refresh').setLabel('Refresh').setStyle(ButtonStyle.Primary).setEmoji('🔄'),
            new ButtonBuilder().setCustomId(`report_export_${type}`).setLabel('Export PDF').setStyle(ButtonStyle.Secondary).setEmoji('📄')
        );
        await interaction.channel.send({ embeds: [embed], components: [row] });
        await interaction.editReply({ content: '✅ Report sent to channel!' });
    }

    async scheduleReportCommand(interaction) {
        const name = interaction.options.getString('name') || 'Daily Report';
        const type = interaction.options.getString('type') || 'executive-summary';
        const cronExp = interaction.options.getString('cron') || '0 8 * * *';
        const channel = interaction.options.getChannel('channel') || interaction.channel;

        const sched = {
            id: `sched_${Date.now()}`,
            name,
            type,
            cron: cronExp,
            channelId: channel.id,
            guildId: interaction.guildId,
            enabled: true,
            createdAt: new Date().toISOString(),
        };

        this.data.schedules.push(sched);
        this.saveData();
        this.startSchedule(sched);

        const embed = new EmbedBuilder()
            .setTitle('📅 Report Schedule Created')
            .setDescription(`**${name}** will be delivered to <#${channel.id}>`)
            .addFields(
                { name: 'Type', value: type, inline: true },
                { name: 'Schedule', value: cronExp, inline: true },
                { name: 'Next Run', value: this.getNextCronDate(cronExp), inline: true }
            )
            .setColor('#10b981')
            .setFooter({ text: `ID: ${sched.id}` });

        await interaction.reply({ embeds: [embed] });
    }

    async listSchedulesCommand(interaction) {
        const guildSchedules = this.data.schedules.filter(s => s.guildId === interaction.guildId);
        if (guildSchedules.length === 0) {
            return interaction.reply({ content: 'No report schedules configured for this server.', ephemeral: true });
        }

        const embed = new EmbedBuilder()
            .setTitle('📋 Report Schedules')
            .setColor('#3b82f6');

        for (const s of guildSchedules) {
            embed.addFields({
                name: `${s.enabled ? '✅' : '⏸️'} ${s.name}`,
                value: `Type: ${s.type}\nCron: \`${s.cron}\`\nChannel: <#${s.channelId}>\nID: \`${s.id}\``,
                inline: true,
            });
        }

        await interaction.reply({ embeds: [embed], ephemeral: true });
    }

    async deleteScheduleCommand(interaction) {
        const id = interaction.options.getString('id');
        const idx = this.data.schedules.findIndex(s => s.id === id && s.guildId === interaction.guildId);
        if (idx === -1) {
            return interaction.reply({ content: 'Schedule not found.', ephemeral: true });
        }
        this.stopSchedule(id);
        this.data.schedules.splice(idx, 1);
        this.saveData();
        await interaction.reply({ content: `✅ Schedule \`${id}\` deleted.`, ephemeral: true });
    }

    async sendDigestCommand(interaction) {
        await interaction.deferReply({ ephemeral: false });

        const mode = interaction.options.getString('mode') || 'daily';
        const embed = new EmbedBuilder()
            .setTitle(`📊 ${mode.charAt(0).toUpperCase() + mode.slice(1)} Infrastructure Digest`)
            .setDescription(`Infrastructure summary for ${new Date().toLocaleDateString()}`)
            .setColor('#6366f1')
            .setTimestamp();

        embed.addFields(
            { name: '🖥️ Overall Health', value: '✅ All systems operational\n⏱️ Avg response: 245ms\n📈 Uptime: 99.97%', inline: false },
            { name: '📦 Resource Usage', value: 'CPU: 47% | Memory: 62% | Disk: 71%\n🔄 Active containers: 12', inline: true },
            { name: '⚠️ Recent Alerts', value: '🔴 CPU spike on api-2 (92%)\n🟡 Memory warning on db-main (83%)', inline: true },
            { name: '📈 Traffic', value: `Requests (24h): 142,530\nAvg latency: 43ms\nError rate: 0.12%`, inline: false },
            { name: '💰 Cost', value: 'Today: $142.50\nThis month: $3,820.00\nvs budget: 72%', inline: true },
            { name: '📉 Anomalies', value: '3 anomalies detected\n1 critical, 2 warnings', inline: true }
        );

        const row = new ActionRowBuilder().addComponents(
            new ButtonBuilder().setCustomId('report_refresh').setLabel('Refresh').setStyle(ButtonStyle.Primary).setEmoji('🔄'),
            new ButtonBuilder().setCustomId('report_export_digest').setLabel('Export PDF').setStyle(ButtonStyle.Secondary).setEmoji('📄'),
            new ButtonBuilder().setCustomId('report_view_performance').setLabel('View Details').setStyle(ButtonStyle.Link).setURL('http://localhost:5173/dashboard')
        );

        await interaction.editReply({ embeds: [embed], components: [row] });
    }

    async deliverReport(sched) {
        try {
            const channel = await this.client.channels.fetch(sched.channelId);
            if (!channel) return;

            const embed = await this.createReportEmbed(sched.type, '24h');
            const row = new ActionRowBuilder().addComponents(
                new ButtonBuilder().setCustomId('report_refresh').setLabel('Refresh').setStyle(ButtonStyle.Primary).setEmoji('🔄'),
                new ButtonBuilder().setCustomId(`report_export_${sched.type}`).setLabel('Export PDF').setStyle(ButtonStyle.Secondary).setEmoji('📄')
            );

            await channel.send({ embeds: [embed], components: [row] });

            this.data.deliveryLog.push({
                scheduleId: sched.id,
                deliveredAt: new Date().toISOString(),
                status: 'sent',
            });
            this.saveData();
        } catch (e) {
            console.error(`[ReportBot] Failed to deliver schedule ${sched.id}:`, e.message);
            this.data.deliveryLog.push({
                scheduleId: sched.id,
                deliveredAt: new Date().toISOString(),
                status: 'failed',
                error: e.message,
            });
            this.saveData();
        }
    }

    async createReportEmbed(type, period) {
        let title, description, color, fields;

        switch (type) {
            case 'executive-summary':
                title = '📊 Executive Summary';
                description = `Infrastructure overview for the last ${period}`;
                color = '#6366f1';
                fields = [
                    { name: '🏥 System Health', value: '✅ All systems operational\nUptime: 99.97%\nAvg response: 245ms', inline: false },
                    { name: '📊 Resource Usage', value: 'CPU Avg: 47% | Mem Avg: 62% | Disk: 71%\nActive containers: 12', inline: true },
                    { name: '⚠️ Active Alerts', value: '2 warnings\n1 critical (api-2 CPU)', inline: true },
                    { name: '📈 Traffic', value: `Requests: 142.5K\nErrors: 0.12%\nAvg Latency: 43ms`, inline: true },
                    { name: '💰 Cost (24h)', value: '$142.50\nThis month: $3,820.00', inline: true },
                ];
                break;
            case 'cost':
                title = '💰 Cost Report';
                description = `Cost breakdown for the last ${period}`;
                color = '#f59e0b';
                fields = [
                    { name: 'Total Spend', value: '$3,820.00 this month\n$142.50 today', inline: false },
                    { name: 'By Service', value: 'Web: $1,240\nAPI: $980\nDB: $760\nCache: $340\nQueue: $280\nStorage: $220', inline: true },
                    { name: 'By Provider', value: 'AWS: 52%\nGCP: 28%\nAzure: 15%\nOn-Prem: 5%', inline: true },
                    { name: 'Top Spender', value: 'web-2: $420\napi-1: $380\ndb-main: $340', inline: true },
                ];
                break;
            case 'performance':
                title = '📈 Performance Report';
                description = `Performance metrics for the last ${period}`;
                color = '#10b981';
                fields = [
                    { name: 'API Latency', value: 'p50: 43ms | p95: 128ms | p99: 345ms', inline: false },
                    { name: 'Database', value: 'Query time: 12ms avg\nConnections: 24/100\nCache hit: 87%', inline: true },
                    { name: 'Network', value: 'Throughput: 450 Mbps\nPacket loss: 0.01%\nTCP retransmits: 0.3%', inline: true },
                ];
                break;
            case 'incidents':
                title = '⚠️ Incident Report';
                description = `Incidents and alerts for the last ${period}`;
                color = '#ef4444';
                fields = [
                    { name: 'Critical (1)', value: 'api-2 CPU at 92% for 15m\nResolved: auto-scaled', inline: false },
                    { name: 'Warning (2)', value: 'db-main memory at 83%\nweb-1 latency spike to 2.1s', inline: true },
                    { name: 'Info (4)', value: 'Deployments: 3 config changes\n2 backup completions', inline: true },
                ];
                break;
            case 'anomaly-digest':
                title = '🔍 Anomaly Digest';
                description = `Detected anomalies for the last ${period}`;
                color = '#8b5cf6';
                fields = [
                    { name: '3 Anomalies Detected', value: '1️⃣ CPU spike on api-2 (92%)\n2️⃣ Traffic drop on web-1 (-34%)\n3️⃣ Error rate increase on db-main (2.1%)', inline: false },
                    { name: 'Status', value: '1 auto-remediated\n2 under observation', inline: true },
                ];
                break;
            case 'capacity-forecast':
                title = '📊 Capacity Forecast';
                description = `Resource forecast for the next 30 days`;
                color = '#3b82f6';
                fields = [
                    { name: 'CPU Trend', value: 'Current: 47%\nProjected (30d): 62%\nWarning threshold: 80% at day 45', inline: false },
                    { name: 'Memory Trend', value: 'Current: 62%\nProjected (30d): 74%\nWarning threshold: 80% at day 22', inline: true },
                    { name: 'Storage Trend', value: 'Current: 71%\nProjected (30d): 82%\nAction needed: day 18', inline: true },
                    { name: 'Recommendation', value: '📌 Add 2 web nodes by day 20\n📌 Increase DB storage by 100GB', inline: false },
                ];
                break;
            default:
                title = '📊 Report';
                description = `Report type: ${type}`;
                color = '#6366f1';
                fields = [{ name: 'Data', value: 'No data available for this report type', inline: false }];
        }

        const embed = new EmbedBuilder()
            .setTitle(title)
            .setDescription(description)
            .setColor(color)
            .setTimestamp();

        for (const f of fields) {
            embed.addFields(f);
        }

        return embed;
    }

    getNextCronDate(cronExp) {
        try {
            const parts = cronExp.split(' ');
            if (parts.length >= 5) {
                return `cron: ${cronExp} (runs per schedule)`;
            }
        } catch (e) {
            return cronExp;
        }
        return cronExp;
    }
}

module.exports = ReportBot;