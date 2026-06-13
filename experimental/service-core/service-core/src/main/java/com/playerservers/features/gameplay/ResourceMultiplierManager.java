package com.playerservers.features.gameplay;

import com.playerservers.PlayerServerPlugin;
import net.md_5.bungee.api.ChatColor;
import net.md_5.bungee.api.CommandSender;
import net.md_5.bungee.api.chat.ComponentBuilder;
import net.md_5.bungee.api.connection.ProxiedPlayer;
import net.md_5.bungee.api.plugin.Command;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.logging.Level;

public class ResourceMultiplierManager {

    private final PlayerServerPlugin plugin;
    private final Map<UUID, Map<String, Double>> playerMultipliers;

    public ResourceMultiplierManager(PlayerServerPlugin plugin) {
        this.plugin = plugin;
        this.playerMultipliers = new ConcurrentHashMap<>();
        initDatabase();
    }

    private void initDatabase() {
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            conn.createStatement().execute("CREATE TABLE IF NOT EXISTS player_multipliers (" +
                "uuid VARCHAR(36), boost_type VARCHAR(64), multiplier DOUBLE DEFAULT 1.0, " +
                "expires_at BIGINT DEFAULT 0, PRIMARY KEY (uuid, boost_type))");
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to init multipliers DB", e);
        }
    }

    public void setMultiplier(UUID player, String boostType, double multiplier, long durationMs) {
        playerMultipliers.computeIfAbsent(player, k -> new ConcurrentHashMap<>()).put(boostType, multiplier);
        long expiresAt = durationMs > 0 ? System.currentTimeMillis() + durationMs : Long.MAX_VALUE;
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "INSERT OR REPLACE INTO player_multipliers (uuid, boost_type, multiplier, expires_at) VALUES (?,?,?,?)");
            stmt.setString(1, player.toString());
            stmt.setString(2, boostType);
            stmt.setDouble(3, multiplier);
            stmt.setLong(4, expiresAt);
            stmt.executeUpdate();
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to save multiplier", e);
        }
    }

    public double getEffectiveMultiplier(UUID player, String boostType) {
        double base = 1.0;
        if (!playerMultipliers.containsKey(player)) return base;
        Map<String, Double> boosts = playerMultipliers.get(player);
        for (Map.Entry<String, Double> entry : boosts.entrySet()) {
            base *= entry.getValue();
        }
        return base;
    }

    public void cleanup() {
        long now = System.currentTimeMillis();
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "DELETE FROM player_multipliers WHERE expires_at > 0 AND expires_at < ?");
            stmt.setLong(1, now);
            stmt.executeUpdate();
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to cleanup multipliers", e);
        }
    }

    public static class MultiplierCommands {
        private final PlayerServerPlugin plugin;
        private final ResourceMultiplierManager manager;

        public MultiplierCommands(PlayerServerPlugin plugin, ResourceMultiplierManager manager) {
            this.plugin = plugin;
            this.manager = manager;
            plugin.getProxy().getPluginManager().registerCommand(plugin, new MultiplierAdminCommand());
        }

        private class MultiplierAdminCommand extends Command {
            public MultiplierAdminCommand() { super("multiplier", "playerservers.multiplier.admin"); }

            @Override
            public void execute(CommandSender sender, String[] args) {
                if (args.length >= 4 && "set".equalsIgnoreCase(args[0])) {
                    ProxiedPlayer target = plugin.getProxy().getPlayer(args[1]);
                    if (target == null) {
                        sender.sendMessage(new ComponentBuilder("Player not found").color(ChatColor.RED).create());
                        return;
                    }
                    try {
                        double mult = Double.parseDouble(args[2]);
                        long duration = Long.parseLong(args[3]) * 1000L;
                        manager.setMultiplier(target.getUniqueId(), "global", mult, duration);
                        sender.sendMessage(new ComponentBuilder("Set multiplier for " + target.getName())
                            .color(ChatColor.GREEN).create());
                    } catch (NumberFormatException e) {
                        sender.sendMessage(new ComponentBuilder("Usage: /multiplier set <player> <multiplier> <duration_seconds>")
                            .color(ChatColor.RED).create());
                    }
                } else {
                    sender.sendMessage(new ComponentBuilder("Usage: /multiplier set <player> <multiplier> <duration_seconds>")
                        .color(ChatColor.RED).create());
                }
            }
        }
    }
}
