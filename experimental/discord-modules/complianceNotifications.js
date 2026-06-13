const { EmbedBuilder } = require('discord.js');

class ComplianceNotifications {
    constructor(client) {
        this.client = client;
        this.notificationChannel = null;
    }

    async initialize() {
        const channelId = process.env.COMPLIANCE_ALERT_CHANNEL_ID;
        if (channelId) {
            this.notificationChannel = await this.client.channels.fetch(channelId).catch(() => null);
        }
    }

    async handleScanCompleted(scanData) {
        const { benchmark, compliance_score, passed, failed, warning, total_checks } = scanData;
        const color = compliance_score >= 90 ? 0x00ff00 : compliance_score >= 70 ? 0xffaa00 : 0xff0000;
        const embed = new EmbedBuilder()
            .setTitle(`✅ Compliance Scan Complete: ${benchmark}`)
            .setColor(color)
            .addFields(
                { name: 'Compliance Score', value: `${compliance_score.toFixed(1)}%`, inline: true },
                { name: 'Passed', value: `${passed}/${total_checks}`, inline: true },
                { name: 'Failed', value: `${failed}`, inline: true },
                { name: 'Warnings', value: `${warning}`, inline: true },
                { name: 'Status', value: compliance_score >= 90 ? '✅ Compliant' : compliance_score >= 70 ? '⚠️ Needs Attention' : '❌ Non-Compliant', inline: false }
            )
            .setFooter({ text: 'Infra Pilot Compliance Monitor' })
            .setTimestamp();
        if (this.notificationChannel) {
            await this.notificationChannel.send({ embeds: [embed] });
        }
    }

    async handleClassificationFinding(findingData) {
        const { scan_id, classification, pattern_type, confidence, source, content_preview } = findingData;
        const embed = new EmbedBuilder()
            .setTitle(`🔍 Data Classification Alert: ${classification.toUpperCase()}`)
            .setColor(classification === 'pci' ? 0xff0000 : classification === 'phi' ? 0xff6600 : 0xffff00)
            .addFields(
                { name: 'Classification', value: classification, inline: true },
                { name: 'Pattern', value: pattern_type, inline: true },
                { name: 'Confidence', value: `${(confidence * 100).toFixed(0)}%`, inline: true },
                { name: 'Source', value: source, inline: true },
                { name: 'Preview', value: content_preview ? content_preview.substring(0, 500) : 'N/A', inline: false }
            )
            .setTimestamp();
        if (this.notificationChannel) {
            await this.notificationChannel.send({ embeds: [embed] });
        }
    }

    async handleBreachNotification(breachData) {
        const { breach_id, severity, description, affected_users, affected_data, status } = breachData;
        const color = severity === 'critical' ? 0xff0000 : severity === 'high' ? 0xff6600 : 0xffff00;
        const embed = new EmbedBuilder()
            .setTitle(`🚨 DATA BREACH ${severity.toUpperCase()}`)
            .setColor(color)
            .addFields(
                { name: 'Breach ID', value: breach_id, inline: true },
                { name: 'Severity', value: severity, inline: true },
                { name: 'Status', value: status, inline: true },
                { name: 'Affected Users', value: `${affected_users}`, inline: true },
                { name: 'Affected Data', value: affected_data ? affected_data.join(', ') : 'Unknown', inline: false },
                { name: 'Description', value: description ? description.substring(0, 500) : 'N/A', inline: false }
            )
            .setFooter({ text: 'GDPR Breach Notification Required within 72h' })
            .setTimestamp();
        if (this.notificationChannel) {
            await this.notificationChannel.send({ embeds: [embed] });
        }
    }

    async handlePolicyViolation(violationData) {
        const { policy_name, rule_id, resource, action, user, decision, context } = violationData;
        const embed = new EmbedBuilder()
            .setTitle('🔒 Policy Violation Detected')
            .setColor(0xff0000)
            .addFields(
                { name: 'Policy', value: policy_name || 'N/A', inline: true },
                { name: 'Rule', value: rule_id, inline: true },
                { name: 'Resource', value: resource, inline: true },
                { name: 'Action', value: action, inline: true },
                { name: 'User', value: user, inline: true },
                { name: 'Decision', value: decision, inline: true },
                { name: 'Context', value: context ? JSON.stringify(context).substring(0, 500) : 'N/A', inline: false }
            )
            .setTimestamp();
        if (this.notificationChannel) {
            await this.notificationChannel.send({ embeds: [embed] });
        }
    }

    async handleAnomalyAlert(anomalyData) {
        const { user_id, anomaly_score, severity, action, details } = anomalyData;
        const embed = new EmbedBuilder()
            .setTitle('📈 Anomaly Detected')
            .setColor(severity === 'critical' ? 0xff0000 : severity === 'high' ? 0xff6600 : 0xffff00)
            .addFields(
                { name: 'User', value: user_id, inline: true },
                { name: 'Anomaly Score', value: anomaly_score.toFixed(3), inline: true },
                { name: 'Severity', value: severity, inline: true },
                { name: 'Action', value: action, inline: true },
                { name: 'Details', value: details ? JSON.stringify(details).substring(0, 500) : 'N/A', inline: false }
            )
            .setTimestamp();
        if (this.notificationChannel) {
            await this.notificationChannel.send({ embeds: [embed] });
        }
    }
}

module.exports = ComplianceNotifications;
