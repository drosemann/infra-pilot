package com.playerservers.features.server;

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

public class VIPPerksManager {

    private final PlayerServerPlugin plugin;
    private final Map<String, RankTier> rankTiers;
    private final Map<UUID, String> playerRanks;
    private final Map<UUID, Long> rankExpirations;

    public VIPPerksManager(PlayerServerPlugin plugin) {
        this.plugin = plugin;
        this.rankTiers = new ConcurrentHashMap<>();
        this.playerRanks = new ConcurrentHashMap<>();
        this.rankExpirations = new ConcurrentHashMap<>();
        initDatabase();
        loadDefaultTiers();
    }

    private void initDatabase() {
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            conn.createStatement().execute("CREATE TABLE IF NOT EXISTS vip_ranks (" +
                "uuid VARCHAR(36) PRIMARY KEY," +
                "rank_name VARCHAR(64)," +
                "expires_at BIGINT DEFAULT 0," +
                "assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP" +
                ")");
            conn.createStatement().execute("CREATE TABLE IF NOT EXISTS rank_perks (" +
                "rank_name VARCHAR(64), perk_flag VARCHAR(64), " +
                "PRIMARY KEY (rank_name, perk_flag))");
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to init VIP DB", e);
        }
    }

    private void loadDefaultTiers() {
        RankTier vip = new RankTier("vip", "§a[VIP]");
        vip.addPerk("fly");
        vip.addPerk("nickname");
        vip.addPerk("color_chat");
        vip.addPerk("join_priority_high");
        rankTiers.put("vip", vip);

        RankTier vipPlus = new RankTier("vip+", "§b[VIP+]");
        vipPlus.addPerk("fly");
        vipPlus.addPerk("nickname");
        vipPlus.addPerk("color_chat");
        vipPlus.addPerk("join_priority_highest");
        vipPlus.addPerk("command_pweather");
        vipPlus.addPerk("command_ptime");
        rankTiers.put("vip+", vipPlus);

        RankTier mvp = new RankTier("mvp", "§d[MVP]");
        mvp.addPerk("fly");
        mvp.addPerk("nickname");
        mvp.addPerk("color_chat");
        mvp.addPerk("join_priority_highest");
        mvp.addPerk("command_pweather");
        mvp.addPerk("command_ptime");
        mvp.addPerk("world_border_edit");
        mvp.addPerk("market_fee_exempt");
        rankTiers.put("mvp", mvp);
    }

    public void setRank(UUID player, String rankName, long durationMs) {
        playerRanks.put(player, rankName);
        long expires = durationMs > 0 ? System.currentTimeMillis() + durationMs : Long.MAX_VALUE;
        rankExpirations.put(player, expires);

        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "INSERT OR REPLACE INTO vip_ranks (uuid, rank_name, expires_at) VALUES (?,?,?)");
            stmt.setString(1, player.toString());
            stmt.setString(2, rankName);
            stmt.setLong(3, expires);
            stmt.executeUpdate();
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to save VIP rank", e);
        }
    }

    public boolean hasPerk(UUID player, String perkFlag) {
        String rank = playerRanks.get(player);
        if (rank == null) return false;
        Long expires = rankExpirations.get(player);
        if (expires != null && expires < System.currentTimeMillis() && expires != Long.MAX_VALUE) return false;
        RankTier tier = rankTiers.get(rank);
        return tier != null && tier.hasPerk(perkFlag);
    }

    public String getRankDisplay(UUID player) {
        String rank = playerRanks.get(player);
        RankTier tier = rankTiers.get(rank);
        return tier != null ? tier.displayPrefix : "";
    }

    public static class RankTier {
        public final String name;
        public final String displayPrefix;
        private final java.util.Set<String> perks;

        RankTier(String name, String displayPrefix) {
            this.name = name;
            this.displayPrefix = displayPrefix;
            this.perks = java.util.Collections.newSetFromMap(new ConcurrentHashMap<>());
        }

        public void addPerk(String perk) { perks.add(perk); }
        public boolean hasPerk(String perk) { return perks.contains(perk); }
        public java.util.Set<String> getPerks() { return perks; }
    }

    public static class VIPCommands {
        private final PlayerServerPlugin plugin;
        private final VIPPerksManager manager;

        public VIPCommands(PlayerServerPlugin plugin, VIPPerksManager manager) {
            this.plugin = plugin;
            this.manager = manager;
            plugin.getProxy().getPluginManager().registerCommand(plugin, new VIPCommand());
        }

        private class VIPCommand extends Command {
            public VIPCommand() { super("vip", "playerservers.vip"); }

            @Override
            public void execute(CommandSender sender, String[] args) {
                if (!(sender instanceof ProxiedPlayer)) return;
                ProxiedPlayer player = (ProxiedPlayer) sender;
                String prefix = manager.getRankDisplay(player.getUniqueId());
                player.sendMessage(new ComponentBuilder("Your rank: ").color(ChatColor.YELLOW)
                    .append(prefix.isEmpty() ? "None" : prefix).color(ChatColor.GREEN).create());
            }
        }

        public static class VIPAdminCommands extends Command {
            private final VIPPerksManager manager;

            public VIPAdminCommands(VIPPerksManager manager) {
                super("vipadmin", "playerservers.vip.admin");
                this.manager = manager;
            }

            @Override
            public void execute(CommandSender sender, String[] args) {
                if (args.length >= 3 && "set".equalsIgnoreCase(args[0])) {
                    ProxiedPlayer target = manager.plugin.getProxy().getPlayer(args[1]);
                    if (target == null) {
                        sender.sendMessage(new ComponentBuilder("Player not found").color(ChatColor.RED).create());
                        return;
                    }
                    try {
                        long duration = Long.parseLong(args[3]) * 1000L;
                        manager.setRank(target.getUniqueId(), args[2], duration);
                        sender.sendMessage(new ComponentBuilder("Set " + target.getName() + " to " + args[2])
                            .color(ChatColor.GREEN).create());
                    } catch (NumberFormatException e) {
                        sender.sendMessage(new ComponentBuilder("Usage: /vipadmin set <player> <rank> <duration_seconds>")
                            .color(ChatColor.RED).create());
                    }
                } else {
                    sender.sendMessage(new ComponentBuilder("Usage: /vipadmin set <player> <rank> <duration_seconds>")
                        .color(ChatColor.RED).create());
                }
            }
        }
    }
}
