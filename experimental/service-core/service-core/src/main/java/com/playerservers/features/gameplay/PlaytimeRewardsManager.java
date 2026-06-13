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
import java.util.concurrent.TimeUnit;
import java.util.logging.Level;

public class PlaytimeRewardsManager {

    private final PlayerServerPlugin plugin;
    private final Map<UUID, Long> playerPlaytime;
    private final Map<UUID, Integer> lastRewardTier;

    public PlaytimeRewardsManager(PlayerServerPlugin plugin) {
        this.plugin = plugin;
        this.playerPlaytime = new ConcurrentHashMap<>();
        this.lastRewardTier = new ConcurrentHashMap<>();
        initDatabase();
        startTracking();
    }

    private void initDatabase() {
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            conn.createStatement().execute("CREATE TABLE IF NOT EXISTS player_playtime (" +
                "uuid VARCHAR(36) PRIMARY KEY," +
                "total_minutes BIGINT DEFAULT 0," +
                "last_reward_tier INT DEFAULT 0" +
                ")");
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to init playtime DB", e);
        }
    }

    private void startTracking() {
        plugin.getProxy().getScheduler().schedule(plugin, () -> {
            for (ProxiedPlayer player : plugin.getProxy().getPlayers()) {
                UUID uuid = player.getUniqueId();
                long current = playerPlaytime.getOrDefault(uuid, 0L) + 1;
                playerPlaytime.put(uuid, current);
                checkRewards(player, uuid, current);
            }
        }, 1, 1, TimeUnit.MINUTES);
    }

    private void checkRewards(ProxiedPlayer player, UUID uuid, long totalMinutes) {
        int[] tiers = {60, 360, 600, 1440, 4320, 10080}; // 1h, 6h, 10h, 24h, 3d, 7d
        double[] rewards = {10, 25, 50, 100, 250, 500};

        int lastTier = lastRewardTier.getOrDefault(uuid, 0);
        for (int i = lastTier; i < tiers.length; i++) {
            if (totalMinutes >= tiers[i]) {
                plugin.getEconomyManager().deposit(uuid, rewards[i], "Playtime reward: " + tiers[i] + " minutes");
                lastRewardTier.put(uuid, i + 1);
                player.sendMessage(new ComponentBuilder("You earned $" + String.format("%.0f", rewards[i]))
                    .color(ChatColor.GREEN)
                    .append(" for playing " + tiers[i] + " minutes!").color(ChatColor.YELLOW).create());
            }
        }

        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "INSERT OR REPLACE INTO player_playtime (uuid, total_minutes, last_reward_tier) VALUES (?,?,?)");
            stmt.setString(1, uuid.toString());
            stmt.setLong(2, totalMinutes);
            stmt.setInt(3, lastRewardTier.getOrDefault(uuid, 0));
            stmt.executeUpdate();
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to save playtime", e);
        }
    }

    public long getPlaytime(UUID uuid) { return playerPlaytime.getOrDefault(uuid, 0L); }

    public static class PlaytimeCommands {
        private final PlayerServerPlugin plugin;
        private final PlaytimeRewardsManager manager;

        public PlaytimeCommands(PlayerServerPlugin plugin, PlaytimeRewardsManager manager) {
            this.plugin = plugin;
            this.manager = manager;
            plugin.getProxy().getPluginManager().registerCommand(plugin, new PlaytimeCommand());
        }

        private class PlaytimeCommand extends Command {
            public PlaytimeCommand() { super("playtime", "playerservers.playtime"); }

            @Override
            public void execute(CommandSender sender, String[] args) {
                if (!(sender instanceof ProxiedPlayer)) return;
                ProxiedPlayer player = (ProxiedPlayer) sender;
                long minutes = manager.getPlaytime(player.getUniqueId());
                long hours = minutes / 60;
                long mins = minutes % 60;
                player.sendMessage(new ComponentBuilder("Your playtime: ").color(ChatColor.YELLOW)
                    .append(hours + " hours, " + mins + " minutes").color(ChatColor.GREEN).create());
            }
        }
    }
}
