const fs = require('fs');
const path = require('path');
const { query, getDbPool } = require('./db');

// Fallback path must be writable under read_only:true (see docker-compose.yml tmpfs: /tmp)
const SERVER_LIMITS_FILE = path.join('/tmp', 'server_limits.json');
// Legacy path for migration / inspection only
const LEGACY_LIMITS_FILE = path.join(__dirname, '..', 'server_limits.json');

let _ensureTablePromise = null;

async function _ensureTable() {
  if (!_ensureTablePromise) {
    _ensureTablePromise = query(`
      CREATE TABLE IF NOT EXISTS server_limits (
        user_id VARCHAR(255) NOT NULL,
        server_identifier VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, server_identifier)
      )
    `);
  }
  return _ensureTablePromise;
}

async function loadServerLimits() {
  try {
    await _ensureTable();
    const result = await query(
      'SELECT user_id, server_identifier FROM server_limits'
    );
    const limits = {};
    for (const row of result.rows) {
      if (!limits[row.user_id]) limits[row.user_id] = [];
      limits[row.user_id].push(row.server_identifier);
    }
    return limits;
  } catch (error) {
    console.error('[ServerLimits] DB load failed, trying JSON fallback:', error.message);
  }
  // Try new writable location first, then legacy for migration
  for (const candidate of [SERVER_LIMITS_FILE, LEGACY_LIMITS_FILE]) {
    try {
      if (fs.existsSync(candidate)) {
        return JSON.parse(fs.readFileSync(candidate, 'utf8'));
      }
    } catch (error) {
      console.error(`[ServerLimits] JSON fallback read failed (${candidate}):`, error.message);
    }
  }
  try {
    fs.writeFileSync(SERVER_LIMITS_FILE, JSON.stringify({}));
    return {};
  } catch (error) {
    console.error('[ServerLimits] JSON fallback init failed (read_only?):', error.message);
    // Preserve failure signal – caller can decide to fail server creation
    return {};
  }
}

async function saveServerLimits(userId, serverIdentifier) {
  try {
    await _ensureTable();
    await query(
      'INSERT INTO server_limits (user_id, server_identifier) VALUES ($1, $2) ON CONFLICT DO NOTHING',
      [userId, serverIdentifier]
    );
    return true;
  } catch (error) {
    console.error('[ServerLimits] DB save failed, using JSON fallback:', error.message);
    try {
      let limits = {};
      if (fs.existsSync(SERVER_LIMITS_FILE)) {
        limits = JSON.parse(fs.readFileSync(SERVER_LIMITS_FILE, 'utf8'));
      } else if (fs.existsSync(LEGACY_LIMITS_FILE)) {
        limits = JSON.parse(fs.readFileSync(LEGACY_LIMITS_FILE, 'utf8'));
      }
      if (!limits[userId]) limits[userId] = [];
      if (limits[userId].includes(serverIdentifier)) return true;
      limits[userId].push(serverIdentifier);
      fs.writeFileSync(SERVER_LIMITS_FILE, JSON.stringify(limits, null, 2));
      return true;
    } catch (fsError) {
      console.error('[ServerLimits] JSON fallback save failed (read_only? persistent volume needed):', fsError.message);
      // Explicit failure – callers should treat this as persistence error
      return false;
    }
  }
}

module.exports = { loadServerLimits, saveServerLimits };
