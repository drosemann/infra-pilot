const { EmbedBuilder, ActionRowBuilder, ButtonBuilder, ButtonStyle } = require('discord.js');
const axios = require('axios');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

class CodeReviewBot {
    constructor(client) {
        this.client = client;
        this.configs = new Map();
        this.webhookSecret = process.env.CODE_REVIEW_WEBHOOK_SECRET || 'default-secret';
        this.loadData();
    }

    loadData() {
        const configPath = path.join(__dirname, '..', 'data', 'code_review_config.json');
        try {
            if (fs.existsSync(configPath)) {
                const data = JSON.parse(fs.readFileSync(configPath, 'utf8'));
                for (const [guildId, config] of Object.entries(data)) {
                    this.configs.set(guildId, config);
                }
            }
        } catch (e) {
            console.error('Error loading code review configs:', e);
        }
    }

    saveConfig() {
        const configPath = path.join(__dirname, '..', 'data', 'code_review_config.json');
        try {
            const dir = path.dirname(configPath);
            if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
            const data = {};
            for (const [guildId, config] of this.configs) {
                data[guildId] = config;
            }
            fs.writeFileSync(configPath, JSON.stringify(data, null, 2));
        } catch (e) {
            console.error('Error saving code review configs:', e);
        }
    }

    getConfig(guildId) {
        if (!this.configs.has(guildId)) {
            this.configs.set(guildId, {
                enabled: false,
                aiEndpoint: process.env.AI_API_ENDPOINT || 'https://api.openai.com/v1/chat/completions',
                aiKey: process.env.AI_API_KEY || '',
                aiModel: process.env.AI_MODEL || 'gpt-4',
                reviewChannels: [],
                minReviewSize: 10
            });
        }
        return this.configs.get(guildId);
    }

    async handleCommand(interaction) {
        if (interaction.commandName !== 'codereview') return;

        const sub = interaction.options.getSubcommand();

        if (sub === 'config') {
            await this.handleConfig(interaction);
        } else if (sub === 'history') {
            await this.handleHistory(interaction);
        } else if (sub === 'enable') {
            await this.handleEnable(interaction);
        } else if (sub === 'disable') {
            await this.handleDisable(interaction);
        }
    }

    async handleConfig(interaction) {
        if (!interaction.member.permissions.has('ADMINISTRATOR')) {
            return interaction.reply({ content: 'You need Administrator permissions.', ephemeral: true });
        }

        const config = this.getConfig(interaction.guildId);
        const embed = new EmbedBuilder()
            .setTitle('AI Code Review Configuration')
            .setColor('#6C5CE7')
            .addFields([
                { name: 'Enabled', value: config.enabled ? '✅ Yes' : '❌ No', inline: true },
                { name: 'AI Model', value: config.aiModel, inline: true },
                { name: 'Min Review Size', value: `${config.minReviewSize} changes`, inline: true },
                { name: 'Review Channels', value: config.reviewChannels.length > 0 ? config.reviewChannels.map(id => `<#${id}>`).join(', ') : 'None set', inline: false }
            ])
            .setFooter({ text: 'Use /codereview enable/disable to toggle' });

        await interaction.reply({ embeds: [embed], ephemeral: true });
    }

    async handleHistory(interaction) {
        const historyPath = path.join(__dirname, '..', 'data', 'code_review_history.json');
        try {
            if (!fs.existsSync(historyPath)) {
                return interaction.reply({ content: 'No review history found.', ephemeral: true });
            }
            const history = JSON.parse(fs.readFileSync(historyPath, 'utf8'));
            const guildHistory = (history[interaction.guildId] || []).slice(-10);

            if (guildHistory.length === 0) {
                return interaction.reply({ content: 'No review history for this server.', ephemeral: true });
            }

            const embed = new EmbedBuilder()
                .setTitle('Code Review History')
                .setColor('#6C5CE7')
                .setDescription(guildHistory.map((r, i) =>
                    `**#${i + 1}** PR #${r.prNumber} - ${r.repo}\nStatus: ${r.status}\nFindings: ${r.issues} issues`
                ).join('\n\n'))
                .setFooter({ text: 'Last 10 reviews' });

            await interaction.reply({ embeds: [embed], ephemeral: true });
        } catch (e) {
            await interaction.reply({ content: 'Error loading review history.', ephemeral: true });
        }
    }

    async handleEnable(interaction) {
        if (!interaction.member.permissions.has('ADMINISTRATOR')) {
            return interaction.reply({ content: 'You need Administrator permissions.', ephemeral: true });
        }
        const config = this.getConfig(interaction.guildId);
        config.enabled = true;
        this.saveConfig();
        await interaction.reply({ content: '✅ Code review bot enabled for this server.', ephemeral: true });
    }

    async handleDisable(interaction) {
        if (!interaction.member.permissions.has('ADMINISTRATOR')) {
            return interaction.reply({ content: 'You need Administrator permissions.', ephemeral: true });
        }
        const config = this.getConfig(interaction.guildId);
        config.enabled = false;
        this.saveConfig();
        await interaction.reply({ content: '❌ Code review bot disabled for this server.', ephemeral: true });
    }

    async handleButton(interaction) {
        if (!interaction.customId.startsWith('codereview_')) return;

        const [action, prNumber, repo] = interaction.customId.split('_').slice(1);
        await interaction.deferUpdate();

        if (action === 'approve') {
            await this.updatePRStatus(repo, prNumber, 'success');
            await interaction.editReply({ content: `✅ PR #${prNumber} approved.`, embeds: [], components: [] });
        } else if (action === 'request_changes') {
            await this.updatePRStatus(repo, prNumber, 'failure');
            await interaction.editReply({ content: `🔴 Changes requested for PR #${prNumber}.`, embeds: [], components: [] });
        }
    }

    async handleWebhook(req, res) {
        const signature = req.headers['x-hub-signature-256'];
        if (signature) {
            const computed = 'sha256=' + crypto.createHmac('sha256', this.webhookSecret)
                .update(JSON.stringify(req.body)).digest('hex');
            if (!crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(computed))) {
                return res.status(401).json({ error: 'Invalid signature' });
            }
        }

        const event = req.headers['x-github-event'];
        if (event === 'pull_request' && (req.body.action === 'opened' || req.body.action === 'synchronize')) {
            const pr = req.body.pull_request;
            const repo = req.body.repository.full_name;
            await this.reviewPullRequest(repo, pr);
        }

        res.status(200).json({ status: 'ok' });
    }

    async reviewPullRequest(repo, pr) {
        if (!this.isValidGithubRepoFullName(repo)) return;
        const normalizedPrNumber = this.normalizePrNumber(pr && pr.number);
        if (normalizedPrNumber === null) return;

        const config = this.getConfig(pr.base.repo.owner.id.toString());
        if (!config || !config.enabled) return;

        const changedFiles = await this.fetchPRFiles(repo, normalizedPrNumber);
        if (changedFiles.length < config.minReviewSize) return;

        const securityIssues = this.scanForSecrets(changedFiles);
        const diffContent = changedFiles.map(f => `File: ${f.filename}\n${f.patch || '(binary)'}`).join('\n---\n');

        const aiReview = await this.runAIReview(diffContent, config);

        const allIssues = [...securityIssues, ...(aiReview.issues || [])];
        const embed = this.buildReviewEmbed(repo, pr, allIssues, aiReview.summary);

        const row = new ActionRowBuilder()
            .addComponents(
                new ButtonBuilder().setCustomId(`codereview_approve_${pr.number}_${repo}`).setLabel('Approve').setStyle(ButtonStyle.Success),
                new ButtonBuilder().setCustomId(`codereview_request_changes_${pr.number}_${repo}`).setLabel('Request Changes').setStyle(ButtonStyle.Danger)
            );

        const channelId = config.reviewChannels[0];
        if (channelId) {
            try {
                const channel = await this.client.channels.fetch(channelId);
                await channel.send({ embeds: [embed], components: [row] });
            } catch (e) {
                console.error('Failed to send review to channel:', e.message);
            }
        }

        this.saveReviewHistory(repo, pr.number, allIssues.length, aiReview.summary);
    }

    async fetchPRFiles(repo, prNumber) {
        try {
            if (!this.isValidGithubRepoFullName(repo)) return [];
            const normalizedPrNumber = this.normalizePrNumber(prNumber);
            if (normalizedPrNumber === null) return [];

            const [owner, repoName] = repo.split('/');
            const token = process.env.GITHUB_TOKEN;
            const headers = token ? { Authorization: `Bearer ${token}` } : {};
            const url = `https://api.github.com/repos/${encodeURIComponent(owner)}/${encodeURIComponent(repoName)}/pulls/${normalizedPrNumber}/files`;
            const res = await axios.get(url, { headers });
            return res.data;
        } catch (e) {
            console.error('Failed to fetch PR files:', e.message);
            return [];
        }
    }

    isValidGithubRepoFullName(repo) {
        return typeof repo === 'string' && /^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(repo);
    }

    normalizePrNumber(prNumber) {
        const n = Number(prNumber);
        if (!Number.isInteger(n) || n <= 0) return null;
        return n;
    }

    scanForSecrets(files) {
        const issues = [];
        const secretPatterns = [
            { regex: /(?:(['"]?)(?:(?:api|secret|token|password|key|auth|credential|private_key)[_ -]?(?:key|secret|token)?\s*[:=]\s*['"]?(?:[A-Za-z0-9+/]{20,}))\1)/gi, type: 'Hardcoded Secret' },
            { regex: /-----BEGIN (?:RSA |EC )?PRIVATE KEY-----/g, type: 'Private Key' },
            { regex: /(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,}/g, type: 'GitHub Token' },
            { regex: /AKIA[0-9A-Z]{16}/g, type: 'AWS Access Key' },
            { regex: /(?:AC|BC|AK|SK)[0-9a-zA-Z]{38}/g, type: 'Azure Key' },
            { regex: /(?:https?:\/\/)?[^@\s]+:[^@\s]+@[^\s]+/g, type: 'URL Embedded Credentials' }
        ];

        for (const file of files) {
            if (!file.patch) continue;
            for (const pattern of secretPatterns) {
                const matches = file.patch.match(pattern.regex);
                if (matches) {
                    issues.push({
                        file: file.filename,
                        type: pattern.type,
                        severity: 'CRITICAL',
                        description: `Potential ${pattern.type} detected in ${file.filename}`
                    });
                }
            }
        }

        return issues;
    }

    async runAIReview(diffContent, config) {
        try {
            const res = await axios.post(config.aiEndpoint, {
                model: config.aiModel,
                messages: [
                    {
                        role: 'system',
                        content: 'You are an AI code reviewer. Analyze the code diff and provide:\n1. A summary of changes\n2. Specific issues (bugs, security, performance, style)\n3. Suggestions for improvement\nRespond with JSON: { "summary": "...", "issues": [{ "file": "...", "line": N, "type": "bug|security|performance|style", "severity": "critical|major|minor", "description": "..." }] }'
                    },
                    { role: 'user', content: `Review this pull request diff:\n\n${diffContent.substring(0, 32000)}` }
                ],
                max_tokens: 2000
            }, {
                headers: {
                    'Authorization': `Bearer ${config.aiKey}`,
                    'Content-Type': 'application/json'
                }
            });

            try {
                return JSON.parse(res.data.choices[0].message.content);
            } catch {
                return { summary: 'AI review completed but could not parse structured response.', issues: [] };
            }
        } catch (e) {
            console.error('AI review failed:', e.message);
            return { summary: 'AI review unavailable.', issues: [] };
        }
    }

    buildReviewEmbed(repo, pr, issues, summary) {
        const criticalCount = issues.filter(i => i.severity === 'CRITICAL' || i.severity === 'critical').length;
        const majorCount = issues.filter(i => i.severity === 'major').length;
        const minorCount = issues.filter(i => i.severity === 'minor' || i.severity === 'major').length;

        const embed = new EmbedBuilder()
            .setTitle(`Code Review: ${repo}#${pr.number}`)
            .setURL(pr.html_url)
            .setDescription(summary ? summary.substring(0, 1000) : 'Review complete.')
            .setColor(criticalCount > 0 ? '#ff0000' : majorCount > 0 ? '#ffa500' : '#00ff00')
            .addFields(
                { name: 'Repository', value: repo, inline: true },
                { name: 'PR', value: `#${pr.number}`, inline: true },
                { name: 'Author', value: pr.user.login, inline: true },
                { name: 'Issues Found', value: `${issues.length} total\n🔴 ${criticalCount} critical\n🟠 ${majorCount} major\n🟡 ${minorCount} minor`, inline: true },
                { name: 'Files Changed', value: `${pr.changed_files}`, inline: true },
                { name: 'Status', value: pr.merged ? 'Merged' : pr.state, inline: true }
            )
            .setTimestamp();

        if (issues.length > 0) {
            const topIssues = issues.slice(0, 5);
            const filesSection = topIssues.map(i =>
                `**${i.file}** - ${i.type}\n${i.description}`
            ).join('\n\n');
            embed.addFields({ name: 'Top Issues', value: filesSection.substring(0, 1024), inline: false });
            if (issues.length > 5) {
                embed.setFooter({ text: `Showing top 5 of ${issues.length} issues. Full report in thread.` });
            }
        }

        return embed;
    }

    async updatePRStatus(repo, prNumber, state) {
        try {
            const token = process.env.GITHUB_TOKEN;
            if (!token) return;
            await axios.post(`https://api.github.com/repos/${repo}/statuses/${prNumber}`, {
                state: state === 'success' ? 'success' : 'failure',
                description: state === 'success' ? 'Code review passed' : 'Code review requested changes',
                context: 'infra-pilot/code-review'
            }, {
                headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }
            });
        } catch (e) {
            console.error('Failed to update PR status:', e.message);
        }
    }

    saveReviewHistory(repo, prNumber, issues, summary) {
        const historyPath = path.join(__dirname, '..', 'data', 'code_review_history.json');
        try {
            const dir = path.dirname(historyPath);
            if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
            let history = {};
            if (fs.existsSync(historyPath)) {
                history = JSON.parse(fs.readFileSync(historyPath, 'utf8'));
            }
            const entry = { repo, prNumber, issues, summary: summary || '', status: 'reviewed', timestamp: new Date().toISOString() };
            const guildId = 'global';
            if (!history[guildId]) history[guildId] = [];
            history[guildId].push(entry);
            if (history[guildId].length > 100) history[guildId] = history[guildId].slice(-100);
            fs.writeFileSync(historyPath, JSON.stringify(history, null, 2));
        } catch (e) {
            console.error('Error saving review history:', e.message);
        }
    }
}

module.exports = CodeReviewBot;
