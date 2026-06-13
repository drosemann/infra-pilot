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
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.logging.Level;

public class PermissionManager {

    private final PlayerServerPlugin plugin;
    private final Map<String, List<String>> groupPermissions;
    private final Map<UUID, List<TempPermission>> tempPermissions;

    public PermissionManager(PlayerServerPlugin plugin) {
        this.plugin = plugin;
        this.groupPermissions = new ConcurrentHashMap<>();
        this.tempPermissions = new ConcurrentHashMap<>();
        initDatabase();
        loadDefaults();
    }

    private void initDatabase() {
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            conn.createStatement().execute("CREATE TABLE IF NOT EXISTS permission_groups (" +
                "group_name VARCHAR(64), permission VARCHAR(128), " +
                "PRIMARY KEY (group_name, permission))");
            conn.createStatement().execute("CREATE TABLE IF NOT EXISTS player_permissions (" +
                "uuid VARCHAR(36), permission VARCHAR(128), expires_at BIGINT DEFAULT 0, " +
                "PRIMARY KEY (uuid, permission))");
            conn.createStatement().execute("CREATE TABLE IF NOT EXISTS player_groups (" +
                "uuid VARCHAR(36), group_name VARCHAR(64), " +
                "PRIMARY KEY (uuid, group_name))");
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to init permissions DB", e);
        }
    }

    private void loadDefaults() {
        addGroupPermission("default", "playerservers.command.server");
        addGroupPermission("default", "playerservers.economy.balance");
        addGroupPermission("vip", "playerservers.economy.balance");
        addGroupPermission("vip", "playerservers.ptime");
        addGroupPermission("vip", "playerservers.pweather");
        addGroupPermission("vip", "playerservers.cooldown.vip");
        addGroupPermission("admin", "playerservers.*");
    }

    public void addGroupPermission(String group, String permission) {
        groupPermissions.computeIfAbsent(group, k -> new ArrayList<>()).add(permission);
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "INSERT IGNORE INTO permission_groups (group_name, permission) VALUES (?,?)");
            stmt.setString(1, group);
            stmt.setString(2, permission);
            stmt.executeUpdate();
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to save group perm", e);
        }
    }

    public void addTempPermission(UUID player, String permission, long durationMs) {
        tempPermissions.computeIfAbsent(player, k -> new ArrayList<>())
            .add(new TempPermission(permission, System.currentTimeMillis() + durationMs));
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "INSERT OR REPLACE INTO player_permissions (uuid, permission, expires_at) VALUES (?,?,?)");
            stmt.setString(1, player.toString());
            stmt.setString(2, permission);
            stmt.setLong(3, System.currentTimeMillis() + durationMs);
            stmt.executeUpdate();
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to save temp perm", e);
        }
    }

    public void addPlayerToGroup(UUID player, String group) {
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "INSERT IGNORE INTO player_groups (uuid, group_name) VALUES (?,?)");
            stmt.setString(1, player.toString());
            stmt.setString(2, group);
            stmt.executeUpdate();
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to add player to group", e);
        }
    }

    public boolean hasPermission(UUID player, String permission) {
        List<TempPermission> temps = tempPermissions.get(player);
        if (temps != null) {
            long now = System.currentTimeMillis();
            for (TempPermission tp : temps) {
                if (tp.permission.equals(permission) && tp.expiresAt > now) return true;
            }
        }

        ProxiedPlayer p = plugin.getProxy().getPlayer(player);
        if (p != null && p.hasPermission(permission)) return true;

        for (List<String> perms : groupPermissions.values()) {
            if (perms.contains(permission) || perms.contains("playerservers.*")) return true;
        }
        return false;
    }

    public void cleanupTemp() {
        long now = System.currentTimeMillis();
        tempPermissions.values().forEach(list -> list.removeIf(tp -> tp.expiresAt <= now));
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "DELETE FROM player_permissions WHERE expires_at > 0 AND expires_at < ?");
            stmt.setLong(1, now);
            stmt.executeUpdate();
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to cleanup temp perms", e);
        }
    }

    private static class TempPermission {
        final String permission;
        final long expiresAt;

        TempPermission(String permission, long expiresAt) {
            this.permission = permission;
            this.expiresAt = expiresAt;
        }
    }

    public static class PermissionCommands {
        private final PlayerServerPlugin plugin;
        private final PermissionManager manager;

        public PermissionCommands(PlayerServerPlugin plugin, PermissionManager manager) {
            this.plugin = plugin;
            this.manager = manager;
            plugin.getProxy().getPluginManager().registerCommand(plugin, new PermissionCommand());
            plugin.getProxy().getPluginManager().registerCommand(plugin, new GroupCommand());
        }

        private class PermissionCommand extends Command {
            public PermissionCommand() { super("permissions", "playerservers.permissions", "perms"); }

            @Override
            public void execute(CommandSender sender, String[] args) {
                if (args.length < 1) {
                    sender.sendMessage(new ComponentBuilder("Usage: /permissions <add|remove|check> <player> <permission> [duration]")
                        .color(ChatColor.RED).create());
                    return;
                }
                if ("check".equalsIgnoreCase(args[0]) && args.length >= 2) {
                    ProxiedPlayer target = plugin.getProxy().getPlayer(args[1]);
                    if (target != null) {
                        boolean has = args.length >= 3 ? manager.hasPermission(target.getUniqueId(), args[2]) : true;
                        sender.sendMessage(new ComponentBuilder(target.getName() + " has permission" +
                            (args.length >= 3 ? " " + args[2] : "") + ": " + has)
                            .color(has ? ChatColor.GREEN : ChatColor.RED).create());
                    }
                } else {
                    sender.sendMessage(new ComponentBuilder("Usage: /permissions <add|remove|check> <player> <permission> [duration]")
                        .color(ChatColor.RED).create());
                }
            }
        }

        private class GroupCommand extends Command {
            public GroupCommand() { super("group", "playerservers.permissions.group"); }

            @Override
            public void execute(CommandSender sender, String[] args) {
                if (args.length >= 2 && "add".equalsIgnoreCase(args[0])) {
                    ProxiedPlayer target = plugin.getProxy().getPlayer(args[1]);
                    if (target != null && args.length >= 3) {
                        manager.addPlayerToGroup(target.getUniqueId(), args[2]);
                        sender.sendMessage(new ComponentBuilder("Added " + target.getName() + " to group " + args[2])
                            .color(ChatColor.GREEN).create());
                    }
                } else if (args.length >= 2 && "perm".equalsIgnoreCase(args[0]) && args.length >= 3) {
                    manager.addGroupPermission(args[1], args[2]);
                    sender.sendMessage(new ComponentBuilder("Added permission " + args[2] + " to group " + args[1])
                        .color(ChatColor.GREEN).create());
                } else {
                    sender.sendMessage(new ComponentBuilder("Usage: /group <add <player> <group>|perm <group> <permission>>")
                        .color(ChatColor.RED).create());
                }
            }
        }
    }
}
