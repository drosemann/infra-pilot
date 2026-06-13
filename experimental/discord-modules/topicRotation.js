const fs = require('fs');
const path = require('path');
const cron = require('node-cron');

class TopicRotation {
    constructor(client) {
        this.client = client;
        this.rotations = new Map();
        this.jobs = new Map();
        this.loadRotations();
    }

    loadRotations() {
        const filePath = path.join(__dirname, '..', 'topic_rotations.json');
        try {
            if (fs.existsSync(filePath)) {
                const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
                for (const [channelId, config] of Object.entries(data)) {
                    this.rotations.set(channelId, config);
                }
            }
        } catch (e) {
            console.error('Error loading topic rotations:', e);
        }
    }

    saveRotations() {
        const filePath = path.join(__dirname, '..', 'topic_rotations.json');
        try {
            const data = {};
            for (const [channelId, config] of this.rotations) {
                data[channelId] = config;
            }
            fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
        } catch (e) {
            console.error('Error saving topic rotations:', e);
        }
    }

    initialize(client) {
        for (const [channelId, config] of this.rotations) {
            this.startRotation(channelId, config);
        }
    }

    startRotation(channelId, config) {
        if (this.jobs.has(channelId)) {
            this.jobs.get(channelId).stop();
        }

        const schedule = config.interval || '0 0 * * *'; // default: daily
        if (cron.validate(schedule)) {
            const job = cron.schedule(schedule, () => this.rotateTopic(channelId));
            this.jobs.set(channelId, job);
            this.rotateTopic(channelId); // initial rotation
        }
    }

    async rotateTopic(channelId) {
        const config = this.rotations.get(channelId);
        if (!config || !config.topics || config.topics.length === 0) return;

        try {
            const channel = await this.client.channels.fetch(channelId).catch(() => null);
            if (!channel) return;

            const currentIndex = config.currentIndex || 0;
            const nextIndex = (currentIndex + 1) % config.topics.length;
            const newTopic = config.topics[nextIndex];

            await channel.setTopic(newTopic, 'Topic-Rotation');
            config.currentIndex = nextIndex;
            this.saveRotations();
        } catch (e) {
            console.error(`Error rotating topic for ${channelId}:`, e.message);
        }
    }

    async handleCommand(interaction) {
        // reserved for future topic rotation commands
    }
}

module.exports = TopicRotation;
