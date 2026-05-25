package com.playerservers.features.economy;

import com.playerservers.PlayerServerPlugin;
import com.playerservers.DatabaseManager;
import net.md_5.bungee.api.connection.ProxiedPlayer;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.UUID;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.logging.Level;

public class EconomyManager {
    private final PlayerServerPlugin plugin;
    private final DatabaseManager databaseManager;
    private final Map<UUID, Double> balanceCache;
    private final Map<String, Double> activityRewards;

    public EconomyManager(PlayerServerPlugin plugin) {
        this.plugin = plugin;
        this.databaseManager = plugin.getDatabaseManager();
        this.balanceCache = new ConcurrentHashMap<>();
        this.activityRewards = new HashMap<>();
        
        initializeDatabase();
        setupDefaultRewards();
    }

    private void initializeDatabase() {
        try (Connection conn = databaseManager.getConnection()) {
            String createTable = "CREATE TABLE IF NOT EXISTS player_economy (" +
                "uuid VARCHAR(36) PRIMARY KEY," +
                "balance DOUBLE DEFAULT 0," +
                "total_earned DOUBLE DEFAULT 0," +
                "total_spent DOUBLE DEFAULT 0," +
                "last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP" +
                ")";
            
            conn.createStatement().execute(createTable);
            
            String createTransactionTable = "CREATE TABLE IF NOT EXISTS economy_transactions (" +
                "id BIGINT AUTO_INCREMENT PRIMARY KEY," +
                "uuid VARCHAR(36)," +
                "amount DOUBLE," +
                "type VARCHAR(32)," +
                "description TEXT," +
                "timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP," +
                "FOREIGN KEY (uuid) REFERENCES player_economy(uuid)" +
                ")";
            
            conn.createStatement().execute(createTransactionTable);
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to initialize economy database", e);
        }
    }

    private void setupDefaultRewards() {
        activityRewards.put("BLOCK_BREAK", 0.01);
        activityRewards.put("BLOCK_PLACE", 0.01);
        activityRewards.put("PLAYER_KILL", 5.0);
        activityRewards.put("MOB_KILL", 0.5);
        activityRewards.put("FISH_CATCH", 1.0);
        activityRewards.put("CRAFT_ITEM", 0.1);
        activityRewards.put("VOTE", 10.0);
        activityRewards.put("PLAYTIME_HOUR", 5.0);
    }

    public void loadPlayerBalance(ProxiedPlayer player) {
        UUID uuid = player.getUniqueId();
        if (!balanceCache.containsKey(uuid)) {
            try (Connection conn = databaseManager.getConnection()) {
                String query = "SELECT balance FROM player_economy WHERE uuid = ?";
                PreparedStatement stmt = conn.prepareStatement(query);
                stmt.setString(1, uuid.toString());
                ResultSet rs = stmt.executeQuery();

                if (rs.next()) {
                    balanceCache.put(uuid, rs.getDouble("balance"));
                } else {
                    String insert = "INSERT INTO player_economy (uuid, balance) VALUES (?, 0)";
                    PreparedStatement insertStmt = conn.prepareStatement(insert);
                    insertStmt.setString(1, uuid.toString());
                    insertStmt.execute();
                    balanceCache.put(uuid, 0.0);
                }
            } catch (SQLException e) {
                plugin.getLogger().log(Level.SEVERE, "Failed to load player balance", e);
            }
        }
    }

    public double getBalance(UUID uuid) {
        return balanceCache.getOrDefault(uuid, 0.0);
    }

    public boolean hasBalance(UUID uuid, double amount) {
        return getBalance(uuid) >= amount;
    }

    public synchronized boolean withdraw(UUID uuid, double amount, String reason) {
        if (!hasBalance(uuid, amount)) {
            return false;
        }

        double newBalance = getBalance(uuid) - amount;
        balanceCache.put(uuid, newBalance);
        
        try (Connection conn = databaseManager.getConnection()) {
            conn.setAutoCommit(false);
            
            String updateBalance = "UPDATE player_economy SET balance = ?, total_spent = total_spent + ? WHERE uuid = ?";
            PreparedStatement balanceStmt = conn.prepareStatement(updateBalance);
            balanceStmt.setDouble(1, newBalance);
            balanceStmt.setDouble(2, amount);
            balanceStmt.setString(3, uuid.toString());
            balanceStmt.execute();

            String insertTransaction = "INSERT INTO economy_transactions (uuid, amount, type, description) VALUES (?, ?, ?, ?)";
            PreparedStatement transactionStmt = conn.prepareStatement(insertTransaction);
            transactionStmt.setString(1, uuid.toString());
            transactionStmt.setDouble(2, -amount);
            transactionStmt.setString(3, "WITHDRAW");
            transactionStmt.setString(4, reason);
            transactionStmt.execute();

            conn.commit();
            return true;
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to withdraw funds", e);
            return false;
        }
    }

    public synchronized boolean deposit(UUID uuid, double amount, String reason) {
        double newBalance = getBalance(uuid) + amount;
        balanceCache.put(uuid, newBalance);
        
        try (Connection conn = databaseManager.getConnection()) {
            conn.setAutoCommit(false);
            
            String updateBalance = "UPDATE player_economy SET balance = ?, total_earned = total_earned + ? WHERE uuid = ?";
            PreparedStatement balanceStmt = conn.prepareStatement(updateBalance);
            balanceStmt.setDouble(1, newBalance);
            balanceStmt.setDouble(2, amount);
            balanceStmt.setString(3, uuid.toString());
            balanceStmt.execute();

            String insertTransaction = "INSERT INTO economy_transactions (uuid, amount, type, description) VALUES (?, ?, ?, ?)";
            PreparedStatement transactionStmt = conn.prepareStatement(insertTransaction);
            transactionStmt.setString(1, uuid.toString());
            transactionStmt.setDouble(2, amount);
            transactionStmt.setString(3, "DEPOSIT");
            transactionStmt.setString(4, reason);
            transactionStmt.execute();

            conn.commit();
            return true;
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to deposit funds", e);
            return false;
        }
    }

    public void rewardActivity(UUID uuid, String activity) {
        if (activityRewards.containsKey(activity)) {
            double amount = activityRewards.get(activity);
            deposit(uuid, amount, "Activity reward: " + activity);
        }
    }

    public Map<UUID, Double> getTopBalances(int limit) {
        Map<UUID, Double> topBalances = new HashMap<>();
        
        try (Connection conn = databaseManager.getConnection()) {
            String query = "SELECT uuid, balance FROM player_economy ORDER BY balance DESC LIMIT ?";
            PreparedStatement stmt = conn.prepareStatement(query);
            stmt.setInt(1, limit);
            ResultSet rs = stmt.executeQuery();

            while (rs.next()) {
                UUID uuid = UUID.fromString(rs.getString("uuid"));
                double balance = rs.getDouble("balance");
                topBalances.put(uuid, balance);
            }
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to get top balances", e);
        }
        
        return topBalances;
    }

    public void saveAllBalances() {
        try (Connection conn = databaseManager.getConnection()) {
            String update = "UPDATE player_economy SET balance = ? WHERE uuid = ?";
            PreparedStatement stmt = conn.prepareStatement(update);
            
            for (Map.Entry<UUID, Double> entry : balanceCache.entrySet()) {
                stmt.setDouble(1, entry.getValue());
                stmt.setString(2, entry.getKey().toString());
                stmt.addBatch();
            }
            
            stmt.executeBatch();
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to save balances", e);
        }
    }
}