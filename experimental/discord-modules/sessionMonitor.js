const { EmbedBuilder } = require('discord.js');

class SessionMonitor {
    constructor(client) {
        this.client = client;
        this.activeSessions = new Map();
        this.alertChannel = null;
    }

    async initialize() {
        const channelId = process.env.SESSION_ALERT_CHANNEL_ID;
        if (channelId) {
            this.alertChannel = await this.client.channels.fetch(channelId).catch(() => null);
        }
    }

    async handleSessionCreated(sessionData) {
        const { user_id, ip_address, device_name, location, is_suspicious } = sessionData;
        if (!is_suspicious) return;

        const embed = new EmbedBuilder()
            .setTitle('⚠️ Suspicious Session Detected')
            .setColor(0xff6600)
            .addFields(
                { name: 'User', value: user_id, inline: true },
                { name: 'IP Address', value: ip_address, inline: true },
                { name: 'Device', value: device_name || 'Unknown', inline: true },
                { name: 'Location', value: location || 'Unknown', inline: true },
                { name: 'Anomaly', value: 'New device / impossible travel', inline: false },
                { name: 'Timestamp', value: new Date().toISOString(), inline: false }
            )
            .setFooter({ text: 'Infra Pilot Session Monitor' })
            .setTimestamp();

        if (this.alertChannel) {
            await this.alertChannel.send({ embeds: [embed] });
        }
    }

    async handleSessionRevoked(sessionData) {
        const { user_id, reason, revoked_by } = sessionData;
        const embed = new EmbedBuilder()
            .setTitle('🔒 Session Revoked')
            .setColor(0x00ff00)
            .addFields(
                { name: 'User', value: user_id, inline: true },
                { name: 'Revoked By', value: revoked_by || 'System', inline: true },
                { name: 'Reason', value: reason || 'Manual revocation', inline: false }
            )
            .setTimestamp();
        if (this.alertChannel) {
            await this.alertChannel.send({ embeds: [embed] });
        }
    }

    async handleBreakGlassTriggered(eventData) {
        const { user_id, resource, reason, ip_address } = eventData;
        const embed = new EmbedBuilder()
            .setTitle('🚨 BREAK GLASS ACCESS TRIGGERED')
            .setColor(0xff0000)
            .addFields(
                { name: 'User', value: user_id, inline: true },
                { name: 'Resource', value: resource, inline: true },
                { name: 'IP', value: ip_address || 'Unknown', inline: true },
                { name: 'Reason', value: reason || 'Emergency', inline: false }
            )
            .setFooter({ text: 'Immediate attention required' })
            .setTimestamp();
        if (this.alertChannel) {
            await this.alertChannel.send({ embeds: [embed] });
        }
    }

    async handlePAMRequest(eventData) {
        const { request_id, user_id, resource, role, reason, status } = eventData;
        const embed = new EmbedBuilder()
            .setTitle('🔑 PAM Access Request')
            .setColor(status === 'approved' ? 0x00ff00 : status === 'denied' ? 0xff0000 : 0xffff00)
            .addFields(
                { name: 'Request ID', value: request_id, inline: true },
                { name: 'User', value: user_id, inline: true },
                { name: 'Resource', value: resource, inline: true },
                { name: 'Role', value: role, inline: true },
                { name: 'Status', value: status, inline: true },
                { name: 'Reason', value: reason || 'N/A', inline: false }
            )
            .setTimestamp();
        if (this.alertChannel) {
            await this.alertChannel.send({ embeds: [embed] });
        }
    }
}

module.exports = SessionMonitor;
