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
                "creation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP" +
                ")";
            statement.executeUpdate(sql);
        } catch (SQLException e) {
            plugin.getLogger().severe("Error setting up database: " + e.getMessage());
        }
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
