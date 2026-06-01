const { EmbedBuilder, ActionRowBuilder, ButtonBuilder, ButtonStyle } = require('discord.js');

class WorkflowNotifications {
    constructor(client) {
        this.client = client;
        this.notificationChannel = null;
        this.approvers = new Map();
    }

    async initialize() {
        const channelId = process.env.WORKFLOW_NOTIFICATION_CHANNEL_ID;
        if (channelId) {
            this.notificationChannel = await this.client.channels.fetch(channelId).catch(() => null);
        }
    }

    async handleWorkflowExecution(workflowData) {
        const { workflow_id, workflow_name, execution_id, status, triggered_by, duration } = workflowData;
        const color = status === 'completed' ? 0x00ff00 : status === 'failed' ? 0xff0000 : 0xffff00;
        const embed = new EmbedBuilder()
            .setTitle(`🔄 Workflow: ${workflow_name}`)
            .setColor(color)
            .addFields(
                { name: 'Workflow ID', value: workflow_id, inline: true },
                { name: 'Execution ID', value: execution_id, inline: true },
                { name: 'Status', value: status, inline: true },
                { name: 'Triggered By', value: triggered_by || 'Manual', inline: true },
                { name: 'Duration', value: duration ? `${duration}s` : 'N/A', inline: true }
            )
            .setTimestamp();
        if (this.notificationChannel) {
            await this.notificationChannel.send({ embeds: [embed] });
        }
    }

    async handlePipelineRun(pipelineData) {
        const { pipeline_id, pipeline_name, run_id, stage, status, commit_sha } = pipelineData;
        const needsApproval = stage === 'approve';
        const embed = new EmbedBuilder()
            .setTitle(`🔧 Pipeline: ${pipeline_name}`)
            .setColor(needsApproval ? 0xffaa00 : status === 'running' ? 0x3498db : 0x00ff00)
            .addFields(
                { name: 'Pipeline ID', value: pipeline_id, inline: true },
                { name: 'Run ID', value: run_id, inline: true },
                { name: 'Stage', value: stage, inline: true },
                { name: 'Status', value: status, inline: true },
                { name: 'Commit', value: commit_sha ? commit_sha.substring(0, 8) : 'N/A', inline: true }
            )
            .setTimestamp();

        if (needsApproval && this.notificationChannel) {
            const approve = new ButtonBuilder().setCustomId(`approve_pipeline_${run_id}`).setLabel('✅ Approve').setStyle(ButtonStyle.Success);
            const reject = new ButtonBuilder().setCustomId(`reject_pipeline_${run_id}`).setLabel('❌ Reject').setStyle(ButtonStyle.Danger);
            const row = new ActionRowBuilder().addComponents(approve, reject);
            await this.notificationChannel.send({ embeds: [embed], components: [row] });
        } else if (this.notificationChannel) {
            await this.notificationChannel.send({ embeds: [embed] });
        }
    }

    async handleDriftAlert(driftData) {
        const { scan_id, drifted_resources, total_resources, severity, details } = driftData;
        const color = drifted_resources > 10 ? 0xff0000 : drifted_resources > 3 ? 0xff6600 : 0xffff00;
        const embed = new EmbedBuilder()
            .setTitle('📊 Configuration Drift Detected')
            .setColor(color)
            .addFields(
                { name: 'Scan ID', value: scan_id, inline: true },
                { name: 'Drifted / Total', value: `${drifted_resources} / ${total_resources}`, inline: true },
                { name: 'Compliance', value: total_resources > 0 ? `${((1 - drifted_resources / total_resources) * 100).toFixed(1)}%` : 'N/A', inline: true },
                { name: 'Severity', value: severity || 'medium', inline: true },
                { name: 'Details', value: details ? details.substring(0, 1024) : 'No details', inline: false }
            )
            .setFooter({ text: 'Infra Pilot Drift Monitor' })
            .setTimestamp();
        if (this.notificationChannel) {
            await this.notificationChannel.send({ embeds: [embed] });
        }
    }

    async handleQuotaAlert(quotaData) {
        const { entity_type, entity_id, resource, requested, limit, usage } = quotaData;
        const embed = new EmbedBuilder()
            .setTitle('⚠️ Resource Quota Alert')
            .setColor(0xff6600)
            .addFields(
                { name: 'Entity', value: `${entity_type}: ${entity_id}`, inline: true },
                { name: 'Resource', value: resource, inline: true },
                { name: 'Requested', value: `${requested}`, inline: true },
                { name: 'Limit', value: `${limit}`, inline: true },
                { name: 'Current Usage', value: `${usage}`, inline: true }
            )
            .setTimestamp();
        if (this.notificationChannel) {
            await this.notificationChannel.send({ embeds: [embed] });
        }
    }

    async handleChaosEvent(eventData) {
        const { experiment_name, fault_type, target, status, blast_radius } = eventData;
        const color = status === 'running' ? 0xff0000 : status === 'completed' ? 0x9b59b6 : 0xffff00;
        const embed = new EmbedBuilder()
            .setTitle('🧪 Chaos Engineering Event')
            .setColor(color)
            .addFields(
                { name: 'Experiment', value: experiment_name, inline: true },
                { name: 'Fault Type', value: fault_type, inline: true },
                { name: 'Target', value: `${target.type}: ${target.selector}`, inline: true },
                { name: 'Status', value: status, inline: true },
                { name: 'Blast Radius', value: blast_radius || 'Unlimited', inline: true }
            )
            .setTimestamp();
        if (this.notificationChannel) {
            await this.notificationChannel.send({ embeds: [embed] });
        }
    }

    async handleSelfHealing(eventData) {
        const { pattern, action, result, confidence, target } = eventData;
        const color = result === 'success' ? 0x00ff00 : result === 'failed' ? 0xff0000 : 0xffff00;
        const embed = new EmbedBuilder()
            .setTitle('🩺 Self-Healing Action')
            .setColor(color)
            .addFields(
                { name: 'Pattern', value: pattern, inline: true },
                { name: 'Action Taken', value: action, inline: true },
                { name: 'Result', value: result, inline: true },
                { name: 'Confidence', value: `${(confidence * 100).toFixed(0)}%`, inline: true },
                { name: 'Target', value: target, inline: false }
            )
            .setTimestamp();
        if (this.notificationChannel) {
            await this.notificationChannel.send({ embeds: [embed] });
        }
    }
}

module.exports = WorkflowNotifications;
