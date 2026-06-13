package com.playerservers.features.statistics;

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
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.logging.Level;

public class AchievementsManager {

    private final PlayerServerPlugin plugin;
    private final Map<String, AchievementDef> achievements;
    private final Map<UUID, List<String>> playerAchievements;

    public AchievementsManager(PlayerServerPlugin plugin) {
        this.plugin = plugin;
        this.achievements = new ConcurrentHashMap<>();
        this.playerAchievements = new ConcurrentHashMap<>();
        loadDefinitions();
        initDatabase();
    }

    private void loadDefinitions() {
        achievements.put("first_join", new AchievementDef("first_join", "First Steps", "Join the server for the first time", 5.0, "JOIN"));
        achievements.put("play_10_hours", new AchievementDef("play_10_hours", "Dedicated Player", "Play for 10 hours total", 50.0, "PLAYTIME_600"));
        achievements.put("play_50_hours", new AchievementDef("play_50_hours", "Veteran", "Play for 50 hours total", 200.0, "PLAYTIME_3000"));
        achievements.put("earn_1000", new AchievementDef("earn_1000", "Entrepreneur", "Earn a total of $1,000", 25.0, "EARN_1000"));
        achievements.put("earn_10000", new AchievementDef("earn_10000", "Tycoon", "Earn a total of $10,000", 100.0, "EARN_10000"));
        achievements.put("first_death", new AchievementDef("first_death", "Welcome to Minecraft", "Die for the first time", 1.0, "DEATH"));
        achievements.put("visit_world", new AchievementDef("visit_world", "Explorer", "Visit another player's server", 10.0, "VISIT"));
        achievements.put("vote_10", new AchievementDef("vote_10", "Active Voter", "Vote 10 times", 30.0, "VOTE_10"));
        achievements.put("create_server", new AchievementDef("create_server", "Server Owner", "Create your own server", 100.0, "CREATE_SERVER"));
    }

    private void initDatabase() {
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            conn.createStatement().execute("CREATE TABLE IF NOT EXISTS player_achievements (" +
                "uuid VARCHAR(36), achievement_id VARCHAR(64), earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, " +
                "PRIMARY KEY (uuid, achievement_id))");
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to init achievements DB", e);
        }
    }

    public boolean award(UUID playerUuid, String achievementId) {
        if (playerAchievements.containsKey(playerUuid) && playerAchievements.get(playerUuid).contains(achievementId)) {
            return false;
        }
        AchievementDef def = achievements.get(achievementId);
        if (def == null) return false;

        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "INSERT IGNORE INTO player_achievements (uuid, achievement_id) VALUES (?, ?)");
            stmt.setString(1, playerUuid.toString());
            stmt.setString(2, achievementId);
            stmt.executeUpdate();

            playerAchievements.computeIfAbsent(playerUuid, k -> new ArrayList<>()).add(achievementId);

            ProxiedPlayer player = plugin.getProxy().getPlayer(playerUuid);
            if (player != null) {
                plugin.getProxy().broadcast(new ComponentBuilder(" ")
                    .append(player.getName()).color(ChatColor.GOLD)
                    .append(" has earned the achievement ").color(ChatColor.YELLOW)
                    .append("[" + def.displayName + "]").color(ChatColor.AQUA)
                    .append("!").color(ChatColor.YELLOW).create());
            }
            return true;
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to award achievement", e);
            return false;
        }
    }

    public List<String> getAchievements(UUID uuid) {
        return playerAchievements.computeIfAbsent(uuid, k -> {
            List<String> list = new ArrayList<>();
            try (Connection conn = plugin.getDatabaseManager().getConnection()) {
                PreparedStatement stmt = conn.prepareStatement(
                    "SELECT achievement_id FROM player_achievements WHERE uuid = ?");
                stmt.setString(1, uuid.toString());
                ResultSet rs = stmt.executeQuery();
                while (rs.next()) list.add(rs.getString("achievement_id"));
            } catch (SQLException e) {
                plugin.getLogger().log(Level.SEVERE, "Failed to load achievements", e);
            }
            return list;
        });
    }

    public AchievementDef getDef(String id) { return achievements.get(id); }
    public Map<String, AchievementDef> getAllDefs() { return achievements; }

    public static class AchievementDef {
        public final String id;
        public final String displayName;
        public final String description;
        public final double reward;
        public final String trigger;

        public AchievementDef(String id, String displayName, String description, double reward, String trigger) {
            this.id = id;
            this.displayName = displayName;
            this.description = description;
            this.reward = reward;
            this.trigger = trigger;
        }
    }

    public static class AchievementCommands {
        private final PlayerServerPlugin plugin;
        private final AchievementsManager manager;

        public AchievementCommands(PlayerServerPlugin plugin, AchievementsManager manager) {
            this.plugin = plugin;
            this.manager = manager;
            plugin.getProxy().getPluginManager().registerCommand(plugin, new AchievementCommand());
            plugin.getProxy().getPluginManager().registerCommand(plugin, new AchievementAdminCommand());
        }

        private class AchievementCommand extends Command {
            public AchievementCommand() { super("achievements", "playerservers.achievements", "achievement", "ach"); }

            @Override
            public void execute(CommandSender sender, String[] args) {
                if (!(sender instanceof ProxiedPlayer)) {
                    sender.sendMessage(new ComponentBuilder("Players only").color(ChatColor.RED).create());
                    return;
                }
                ProxiedPlayer player = (ProxiedPlayer) sender;
                List<String> earned = manager.getAchievements(player.getUniqueId());
                player.sendMessage(new ComponentBuilder("=== Achievements (" + earned.size() + "/" + manager.getAllDefs().size() + ") ===")
                    .color(ChatColor.GOLD).create());
                for (AchievementDef def : manager.getAllDefs().values()) {
                    boolean has = earned.contains(def.id);
                    ChatColor color = has ? ChatColor.GREEN : ChatColor.GRAY;
                    String status = has ? " [UNLOCKED]" : " [LOCKED]";
                    player.sendMessage(new ComponentBuilder(def.displayName).color(color)
                        .append(status).color(has ? ChatColor.GREEN : ChatColor.DARK_GRAY)
                        .append(" - " + def.description).color(ChatColor.WHITE).create());
                }
            }
        }

        private class AchievementAdminCommand extends Command {
            public AchievementAdminCommand() { super("achievementadmin", "playerservers.achievements.admin"); }

            @Override
            public void execute(CommandSender sender, String[] args) {
                if (args.length >= 2 && "give".equalsIgnoreCase(args[0])) {
                    ProxiedPlayer target = plugin.getProxy().getPlayer(args[1]);
                    if (target != null && args.length >= 3) {
                        if (manager.award(target.getUniqueId(), args[2])) {
                            sender.sendMessage(new ComponentBuilder("Achievement awarded!").color(ChatColor.GREEN).create());
                        } else {
                            sender.sendMessage(new ComponentBuilder("Already has it or invalid ID").color(ChatColor.RED).create());
                        }
                    }
                } else {
                    sender.sendMessage(new ComponentBuilder("Usage: /achievementadmin give <player> <id>")
                        .color(ChatColor.RED).create());
                }
            }
        }
    }
}
