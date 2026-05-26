const axios = require('axios');

const INTEGRATION_SERVICE_URL = process.env.INTEGRATION_SERVICE_URL || 'http://localhost:9000';

async function notifyIntegration(eventType, data) {
  try {
    await axios.post(`${INTEGRATION_SERVICE_URL}/api/notifications/server-event`, {
      event_type: eventType,
      server_name: data.serverName,
      details: data
    });
    console.log(`[Integration] Notified: ${eventType}`);
  } catch (error) {
    console.error(`[Integration] Failed to notify:`, error.message);
  }
}

async function notifyServerCreated(serverName, serverId) {
  return notifyIntegration('server_created', { serverName, serverId });
}

async function notifyServerStarted(serverName, serverId) {
  return notifyIntegration('server_started', { serverName, serverId });
}

async function notifyServerStopped(serverName, serverId) {
  return notifyIntegration('server_stopped', { serverName, serverId });
}

async function notifyServerDeleted(serverName, serverId) {
  return notifyIntegration('server_deleted', { serverName, serverId });
}

async function notifyServerError(serverName, serverId, error) {
  return notifyIntegration('server_error', { serverName, serverId, error });
}

async function syncUserToIntegration(userData) {
  try {
    const response = await axios.post(`${INTEGRATION_SERVICE_URL}/api/users`, userData);
    console.log(`[Integration] User synced: ${userData.email}`);
    return response.data;
  } catch (error) {
    console.error(`[Integration] User sync failed:`, error.message);
    return null;
  }
}

async function getUnifiedMetrics() {
  try {
    const response = await axios.get(`${INTEGRATION_SERVICE_URL}/api/metrics/dashboard`);
    return response.data;
  } catch (error) {
    console.error(`[Integration] Metrics fetch failed:`, error.message);
    return null;
  }
}

async function broadcastNotification(message) {
  try {
    await axios.post(`${INTEGRATION_SERVICE_URL}/api/notifications`, message);
    console.log(`[Integration] Notification broadcast`);
  } catch (error) {
    console.error(`[Integration] Broadcast failed:`, error.message);
  }
}

async function notifyGitPush(repo, branch, commits, channelId) {
  try {
    const commitLines = (commits || []).slice(0, 5).map(c =>
      `• \`${c.id?.slice(0, 7) || 'unknown'}\` ${c.message?.split('\n')[0] || 'no message'} — ${c.author?.name || 'unknown'}`
    ).join('\n');

    const message = {
      channel_id: channelId,
      embeds: [{
        title: `🚀 Push to ${repo}:${branch}`,
        description: commitLines || 'No commit details',
        color: 0x2ea043,
        timestamp: new Date().toISOString(),
        footer: { text: `${commits?.length || 0} commit(s) pushed` },
        url: `https://github.com/${repo}/commit/${commits?.[0]?.id || ''}`
      }]
    };

    await axios.post(`${INTEGRATION_SERVICE_URL}/api/notifications/discord`, message);
    console.log(`[Integration] Git push notification sent for ${repo}:${branch}`);
  } catch (error) {
    console.error(`[Integration] Git push notification failed:`, error.message);
  }
}

module.exports = {
  notifyIntegration,
  notifyServerCreated,
  notifyServerStarted,
  notifyServerStopped,
  notifyServerDeleted,
  notifyServerError,
  syncUserToIntegration,
  getUnifiedMetrics,
  broadcastNotification,
  notifyGitPush
};