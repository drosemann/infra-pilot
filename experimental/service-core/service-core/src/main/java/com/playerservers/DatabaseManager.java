package com.playerservers;

import com.zaxxer.hikari.HikariConfig;
import com.zaxxer.hikari.HikariDataSource;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;

public class DatabaseManager {

    private final PlayerServerPlugin plugin;
    private HikariDataSource dataSource;

    public DatabaseManager(PlayerServerPlugin plugin) {
        this.plugin = plugin;
    }

    public void connect() throws SQLException {
        HikariConfig config = new HikariConfig();
        config.setJdbcUrl("jdbc:mysql://" + plugin.getConfigManager().getString("database.host") + ":" + plugin.getConfigManager().getInt("database.port") + "/" + plugin.getConfigManager().getString("database.database"));
        config.setUsername(plugin.getConfigManager().getString("database.username"));
        config.setPassword(plugin.getConfigManager().getString("database.password"));
        config.setDriverClassName("com.mysql.cj.jdbc.Driver");
        config.setMaximumPoolSize(10);
        config.setMinimumIdle(5);
        config.setMaxLifetime(1800000);
        config.setConnectionTimeout(30000);
        config.setIdleTimeout(600000);
        config.setLeakDetectionThreshold(5000);
        dataSource = new HikariDataSource(config);
    }

    public void disconnect() {
        if (dataSource != null && !dataSource.isClosed()) {
            dataSource.close();
        }
    }

    public Connection getConnection() throws SQLException {
        return dataSource.getConnection();
    }

    public void setupDatabase() {
        try (Connection connection = getConnection(); Statement statement = connection.createStatement()) {
            String sql = "CREATE TABLE IF NOT EXISTS player_servers (" +
                "player_uuid VARCHAR(36) PRIMARY KEY," +
                "server_name VARCHAR(255) NOT NULL," +
                "server_status VARCHAR(50) NOT NULL," +
                "is_public BOOLEAN DEFAULT false," +
                "description TEXT," +
                "tags VARCHAR(255)," +
                "player_count INT DEFAULT 0," +
                "max_players INT DEFAULT 20," +
                "upvotes INT DEFAULT 0," +
                "downvotes INT DEFAULT 0," +
                "creation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP," +
                "last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP" +
                ")";
            statement.executeUpdate(sql);

            migratePlayerServersTable(connection);
            setupSocialTables(statement);
        } catch (SQLException e) {
            plugin.getLogger().severe("Error setting up database: " + e.getMessage());
        }
    }

    private void migratePlayerServersTable(Connection connection) {
        String[] columns = {
            "is_public BOOLEAN DEFAULT false",
            "description TEXT",
            "tags VARCHAR(255)",
            "player_count INT DEFAULT 0",
            "max_players INT DEFAULT 20",
            "upvotes INT DEFAULT 0",
            "downvotes INT DEFAULT 0",
            "last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
        };
        for (String columnDef : columns) {
            String colName = columnDef.split(" ")[0];
            try (Statement stmt = connection.createStatement()) {
                stmt.execute("ALTER TABLE player_servers ADD COLUMN IF NOT EXISTS " + columnDef);
            } catch (SQLException e) {
                // Column might already exist or MySQL version doesn't support IF NOT EXISTS
                // Try without IF NOT EXISTS and ignore error
                try (Statement stmt = connection.createStatement()) {
                    stmt.execute("ALTER TABLE player_servers ADD COLUMN " + columnDef);
                } catch (SQLException e2) {
                    // Column already exists, ignore
                }
            }
        }
    }

    private void setupSocialTables(Statement statement) throws SQLException {
        statement.executeUpdate("CREATE TABLE IF NOT EXISTS friends (" +
            "id INT AUTO_INCREMENT PRIMARY KEY," +
            "player_uuid VARCHAR(36) NOT NULL," +
            "friend_uuid VARCHAR(36) NOT NULL," +
            "status ENUM('pending','accepted','blocked') NOT NULL DEFAULT 'pending'," +
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP," +
            "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP," +
            "UNIQUE KEY unique_friendship (player_uuid, friend_uuid)," +
            "FOREIGN KEY (player_uuid) REFERENCES player_servers(player_uuid)," +
            "FOREIGN KEY (friend_uuid) REFERENCES player_servers(player_uuid)" +
            ")");

        statement.executeUpdate("CREATE TABLE IF NOT EXISTS server_invitations (" +
            "id INT AUTO_INCREMENT PRIMARY KEY," +
            "server_id VARCHAR(36) NOT NULL," +
            "inviter_uuid VARCHAR(36) NOT NULL," +
            "invitee_uuid VARCHAR(36) NOT NULL," +
            "permission_level ENUM('player','operator','admin') NOT NULL DEFAULT 'player'," +
            "status ENUM('pending','accepted','declined','expired') NOT NULL DEFAULT 'pending'," +
            "expires_at TIMESTAMP NULL," +
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP" +
            ")");

        statement.executeUpdate("CREATE TABLE IF NOT EXISTS server_reviews (" +
            "id INT AUTO_INCREMENT PRIMARY KEY," +
            "server_id VARCHAR(36) NOT NULL," +
            "reviewer_uuid VARCHAR(36) NOT NULL," +
            "rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5)," +
            "comment TEXT," +
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP," +
            "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP," +
            "UNIQUE KEY unique_review (server_id, reviewer_uuid)" +
            ")");

        statement.executeUpdate("CREATE TABLE IF NOT EXISTS player_profiles (" +
            "player_uuid VARCHAR(36) PRIMARY KEY," +
            "bio TEXT," +
            "avatar_url VARCHAR(255)," +
            "website VARCHAR(255)," +
            "discord VARCHAR(255)," +
            "total_playtime INT DEFAULT 0," +
            "servers_created INT DEFAULT 0," +
            "friends_count INT DEFAULT 0," +
            "reputation_score INT DEFAULT 0" +
            ")");

        statement.executeUpdate("CREATE TABLE IF NOT EXISTS messages (" +
            "id INT AUTO_INCREMENT PRIMARY KEY," +
            "sender_uuid VARCHAR(36) NOT NULL," +
            "receiver_uuid VARCHAR(36) NOT NULL," +
            "message TEXT NOT NULL," +
            "is_read BOOLEAN DEFAULT false," +
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP," +
            "INDEX idx_receiver (receiver_uuid, is_read)," +
            "INDEX idx_sender (sender_uuid)" +
            ")");

        statement.executeUpdate("CREATE TABLE IF NOT EXISTS communities (" +
            "id INT AUTO_INCREMENT PRIMARY KEY," +
            "name VARCHAR(64) NOT NULL UNIQUE," +
            "description TEXT," +
            "owner_uuid VARCHAR(36) NOT NULL," +
            "member_count INT DEFAULT 1," +
            "is_public BOOLEAN DEFAULT true," +
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP" +
            ")");

        statement.executeUpdate("CREATE TABLE IF NOT EXISTS community_members (" +
            "id INT AUTO_INCREMENT PRIMARY KEY," +
            "community_id INT NOT NULL," +
            "player_uuid VARCHAR(36) NOT NULL," +
            "role ENUM('owner','admin','member') NOT NULL DEFAULT 'member'," +
            "joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP," +
            "UNIQUE KEY unique_membership (community_id, player_uuid)," +
            "FOREIGN KEY (community_id) REFERENCES communities(id) ON DELETE CASCADE" +
            ")");

        statement.executeUpdate("CREATE TABLE IF NOT EXISTS activity_feed (" +
            "id INT AUTO_INCREMENT PRIMARY KEY," +
            "player_uuid VARCHAR(36) NOT NULL," +
            "activity_type VARCHAR(50) NOT NULL," +
            "target_id INT," +
            "metadata TEXT," +
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP," +
            "INDEX idx_player (player_uuid)," +
            "INDEX idx_type (activity_type)," +
            "INDEX idx_created (created_at)" +
            ")");
    }

    public boolean hasServer(String playerUUID) {
        String sql = "SELECT COUNT(*) FROM player_servers WHERE player_uuid = ?";
        try (Connection connection = getConnection(); PreparedStatement statement = connection.prepareStatement(sql)) {
            statement.setString(1, playerUUID);
            ResultSet resultSet = statement.executeQuery();
            if (resultSet.next()) return resultSet.getInt(1) > 0;
        } catch (SQLException e) {
            plugin.getLogger().severe("Error checking if player has a server: " + e.getMessage());
        }
        return false;
    }

    public void createServerEntry(String playerUUID, String serverName) {
        String sql = "INSERT INTO player_servers (player_uuid, server_name, server_status) VALUES (?, ?, ?)";
        try (Connection connection = getConnection(); PreparedStatement statement = connection.prepareStatement(sql)) {
            statement.setString(1, playerUUID);
            statement.setString(2, serverName);
            statement.setString(3, "STOPPED");
            statement.executeUpdate();
        } catch (SQLException e) {
            plugin.getLogger().severe("Error creating server entry: " + e.getMessage());
        }
    }

    public String getServerName(String playerUUID) {
        String sql = "SELECT server_name FROM player_servers WHERE player_uuid = ?";
        try (Connection connection = getConnection(); PreparedStatement statement = connection.prepareStatement(sql)) {
            statement.setString(1, playerUUID);
            ResultSet resultSet = statement.executeQuery();
            if (resultSet.next()) return resultSet.getString("server_name");
        } catch (SQLException e) {
            plugin.getLogger().severe("Error getting server name: " + e.getMessage());
        }
        return null;
    }

    public void deleteServerEntry(String playerUUID) {
        String sql = "DELETE FROM player_servers WHERE player_uuid = ?";
        try (Connection connection = getConnection(); PreparedStatement statement = connection.prepareStatement(sql)) {
            statement.setString(1, playerUUID);
            statement.executeUpdate();
        } catch (SQLException e) {
            plugin.getLogger().severe("Error deleting server entry: " + e.getMessage());
        }
    }

    public void updateServerStatus(String playerUUID, String status) {
        String sql = "UPDATE player_servers SET server_status = ? WHERE player_uuid = ?";
        try (Connection connection = getConnection(); PreparedStatement statement = connection.prepareStatement(sql)) {
            statement.setString(1, status);
            statement.setString(2, playerUUID);
            statement.executeUpdate();
        } catch (SQLException e) {
            plugin.getLogger().severe("Error updating server status: " + e.getMessage());
        }
    }

    public String getServerStatus(String playerUUID) {
        String sql = "SELECT server_status FROM player_servers WHERE player_uuid = ?";
        try (Connection connection = getConnection(); PreparedStatement statement = connection.prepareStatement(sql)) {
            statement.setString(1, playerUUID);
            ResultSet resultSet = statement.executeQuery();
            if (resultSet.next()) return resultSet.getString("server_status");
        } catch (SQLException e) {
            plugin.getLogger().severe("Error getting server status: " + e.getMessage());
        }
        return null;
    }
}
