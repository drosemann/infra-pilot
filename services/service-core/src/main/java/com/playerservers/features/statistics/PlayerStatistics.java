package com.playerservers.features.statistics;

import com.playerservers.PlayerServerPlugin;
import com.playerservers.DatabaseManager;
import net.md_5.bungee.api.connection.ProxiedPlayer;
import net.md_5.bungee.config.Configuration;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.TimeUnit;
import java.util.logging.Level;

public class PlayerStatistics {
    private final PlayerServerPlugin plugin;
    private final DatabaseManager databaseManager;
    private final Map<UUID, PlayerStats> statsCache;
    private final Map<UUID, Long> lastUpdateTime;

    public PlayerStatistics(PlayerServerPlugin plugin) {
        this.plugin = plugin;
        this.databaseManager = plugin.getDatabaseManager();
        this.statsCache = new ConcurrentHashMap<>();
        this.lastUpdateTime = new ConcurrentHashMap<>();
        
        initializeDatabase();
        startStatisticsTracker();
    }

    private void initializeDatabase() {
        try (Connection conn = databaseManager.getConnection()) {
            String createTable = "CREATE TABLE IF NOT EXISTS player_statistics (" +
                "uuid VARCHAR(36) PRIMARY KEY," +
                "total_playtime BIGINT DEFAULT 0," +
                "peak_players INT DEFAULT 0," +
                "peak_memory_usage BIGINT DEFAULT 0," +
                "peak_cpu_usage DOUBLE DEFAULT 0," +
                "total_restarts INT DEFAULT 0," +
                "uptime_percentage DOUBLE DEFAULT 0," +
                "last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP" +
                ")";
            
            String createHistoryTable = "CREATE TABLE IF NOT EXISTS statistics_history (" +
                "id BIGINT AUTO_INCREMENT PRIMARY KEY," +
                "uuid VARCHAR(36)," +
                "timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP," +
                "cpu_usage DOUBLE," +
                "memory_usage BIGINT," +
                "player_count INT," +
                "tps DOUBLE," +
                "FOREIGN KEY (uuid) REFERENCES player_statistics(uuid)" +
                ")";
            
            conn.createStatement().execute(createTable);
            conn.createStatement().execute(createHistoryTable);
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to initialize statistics database", e);
        }
    }

    private void startStatisticsTracker() {
        plugin.getProxy().getScheduler().schedule(plugin, () -> {
            // Update statistics for all online players' servers
            for (Map.Entry<UUID, PlayerStats> entry : statsCache.entrySet()) {
                UUID uuid = entry.getKey();
                PlayerStats stats = entry.getValue();
                
                try {
                    updateStatistics(uuid, stats);
                } catch (Exception e) {
                    plugin.getLogger().log(Level.WARNING, 
                        "Failed to update statistics for " + uuid, e);
                }
            }
        }, 1, 1, TimeUnit.MINUTES);
    }

    public void trackPlayer(UUID uuid) {
        if (!statsCache.containsKey(uuid)) {
            loadPlayerStats(uuid);
        }
        lastUpdateTime.put(uuid, System.currentTimeMillis());
    }

    private void loadPlayerStats(UUID uuid) {
        try (Connection conn = databaseManager.getConnection()) {
            String query = "SELECT * FROM player_statistics WHERE uuid = ?";
            PreparedStatement stmt = conn.prepareStatement(query);
            stmt.setString(1, uuid.toString());
            ResultSet rs = stmt.executeQuery();

            PlayerStats stats;
            if (rs.next()) {
                stats = new PlayerStats(
                    rs.getLong("total_playtime"),
                    rs.getInt("peak_players"),
                    rs.getLong("peak_memory_usage"),
                    rs.getDouble("peak_cpu_usage"),
                    rs.getInt("total_restarts"),
                    rs.getDouble("uptime_percentage")
                );
            } else {
                stats = new PlayerStats();
                String insert = "INSERT INTO player_statistics (uuid) VALUES (?)";
                PreparedStatement insertStmt = conn.prepareStatement(insert);
                insertStmt.setString(1, uuid.toString());
                insertStmt.execute();
            }

            statsCache.put(uuid, stats);
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to load player statistics", e);
        }
    }

    public void updateStatistics(UUID uuid, PlayerStats currentStats) {
        try (Connection conn = databaseManager.getConnection()) {
            conn.setAutoCommit(false);

            // Update main statistics
            String updateStats = "UPDATE player_statistics " +
                "SET total_playtime = ?," +
                "peak_players = ?," +
                "peak_memory_usage = ?," +
                "peak_cpu_usage = ?," +
                "total_restarts = ?," +
                "uptime_percentage = ?," +
                "last_updated = CURRENT_TIMESTAMP " +
                "WHERE uuid = ?";

            PreparedStatement statsStmt = conn.prepareStatement(updateStats);
            statsStmt.setLong(1, currentStats.getTotalPlaytime());
            statsStmt.setInt(2, currentStats.getPeakPlayers());
            statsStmt.setLong(3, currentStats.getPeakMemoryUsage());
            statsStmt.setDouble(4, currentStats.getPeakCpuUsage());
            statsStmt.setInt(5, currentStats.getTotalRestarts());
            statsStmt.setDouble(6, currentStats.getUptimePercentage());
            statsStmt.setString(7, uuid.toString());
            statsStmt.execute();

            // Record history point
            String insertHistory = "INSERT INTO statistics_history " +
                "(uuid, cpu_usage, memory_usage, player_count, tps) " +
                "VALUES (?, ?, ?, ?, ?)";

            PreparedStatement historyStmt = conn.prepareStatement(insertHistory);
            historyStmt.setString(1, uuid.toString());
            historyStmt.setDouble(2, currentStats.getCurrentCpuUsage());
            historyStmt.setLong(3, currentStats.getCurrentMemoryUsage());
            historyStmt.setInt(4, currentStats.getCurrentPlayers());
            historyStmt.setDouble(5, currentStats.getCurrentTPS());
            historyStmt.execute();

            conn.commit();
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to update statistics", e);
        }
    }

    public PlayerStats getPlayerStats(UUID uuid) {
        return statsCache.computeIfAbsent(uuid, k -> {
            loadPlayerStats(k);
            return statsCache.get(k);
        });
    }

    public Map<String, Object> getServerSummary(UUID uuid) {
        PlayerStats stats = getPlayerStats(uuid);
        Map<String, Object> summary = new HashMap<>();
        
        summary.put("totalPlaytime", TimeUnit.MILLISECONDS.toHours(stats.getTotalPlaytime()));
        summary.put("peakPlayers", stats.getPeakPlayers());
        summary.put("peakMemoryUsage", stats.getPeakMemoryUsage());
        summary.put("peakCpuUsage", stats.getPeakCpuUsage());
        summary.put("uptime", stats.getUptimePercentage());
        summary.put("currentStatus", stats.getCurrentStatus());
        summary.put("currentPlayers", stats.getCurrentPlayers());
        summary.put("currentTPS", stats.getCurrentTPS());
        
        return summary;
    }

    public void recordRestart(UUID uuid) {
        PlayerStats stats = getPlayerStats(uuid);
        stats.incrementRestarts();
        updateStatistics(uuid, stats);
    }

    public void updateResourceUsage(UUID uuid, double cpuUsage, long memoryUsage, 
                                  int playerCount, double tps) {
        PlayerStats stats = getPlayerStats(uuid);
        stats.updateCurrentMetrics(cpuUsage, memoryUsage, playerCount, tps);
        
        // Update peak values if necessary
        stats.updatePeaks();
        
        // Only update database every 5 minutes to avoid excessive writes
        Long lastUpdate = lastUpdateTime.get(uuid);
        if (lastUpdate == null || 
            System.currentTimeMillis() - lastUpdate >= TimeUnit.MINUTES.toMillis(5)) {
            updateStatistics(uuid, stats);
            lastUpdateTime.put(uuid, System.currentTimeMillis());
        }
    }

    public void cleanup() {
        // Save all cached statistics before shutdown
        for (Map.Entry<UUID, PlayerStats> entry : statsCache.entrySet()) {
            updateStatistics(entry.getKey(), entry.getValue());
        }
        
        // Clear caches
        statsCache.clear();
        lastUpdateTime.clear();
    }
}