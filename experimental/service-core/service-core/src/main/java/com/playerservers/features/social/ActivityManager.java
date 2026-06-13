package com.playerservers.features.social;

import com.playerservers.PlayerServerPlugin;
import net.md_5.bungee.api.connection.ProxiedPlayer;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.logging.Level;

public class ActivityManager {
    private final PlayerServerPlugin plugin;
    private final FriendManager friendManager;

    public ActivityManager(PlayerServerPlugin plugin, FriendManager friendManager) {
        this.plugin = plugin;
        this.friendManager = friendManager;
    }

    public void logActivity(UUID playerUuid, Activity.ActivityType type, int targetId, Map<String, Object> metadata) {
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "INSERT INTO activity_feed (player_uuid, activity_type, target_id, metadata) VALUES (?, ?, ?, ?)");
            stmt.setString(1, playerUuid.toString());
            stmt.setString(2, type.name());

            if (targetId > 0) {
                stmt.setInt(3, targetId);
            } else {
                stmt.setNull(3, java.sql.Types.INTEGER);
            }

            if (metadata != null && !metadata.isEmpty()) {
                stmt.setString(4, metadata.toString());
            } else {
                stmt.setNull(4, java.sql.Types.VARCHAR);
            }
            stmt.executeUpdate();
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to log activity", e);
        }
    }

    public List<Activity> getActivityFeed(int page, int pageSize) {
        List<Activity> activities = new ArrayList<>();
        int offset = (page - 1) * pageSize;
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "SELECT * FROM activity_feed ORDER BY created_at DESC LIMIT ? OFFSET ?");
            stmt.setInt(1, pageSize);
            stmt.setInt(2, offset);
            ResultSet rs = stmt.executeQuery();
            while (rs.next()) {
                activities.add(mapActivity(rs));
            }
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to get activity feed", e);
        }
        return activities;
    }

    public List<Activity> getFriendActivities(UUID player, int page, int pageSize) {
        List<Activity> activities = new ArrayList<>();
        List<Friend> friends = friendManager.getFriends(player);
        if (friends.isEmpty()) return activities;

        int offset = (page - 1) * pageSize;
        StringBuilder placeholders = new StringBuilder();
        for (int i = 0; i < friends.size(); i++) {
            if (i > 0) placeholders.append(",");
            placeholders.append("?");
        }

        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            String sql = "SELECT * FROM activity_feed WHERE player_uuid IN (" + placeholders.toString() +
                ") ORDER BY created_at DESC LIMIT ? OFFSET ?";
            PreparedStatement stmt = conn.prepareStatement(sql);
            int index = 1;
            for (Friend friend : friends) {
                stmt.setString(index++, friend.getFriendUuid().toString());
            }
            stmt.setInt(index++, pageSize);
            stmt.setInt(index, offset);
            ResultSet rs = stmt.executeQuery();
            while (rs.next()) {
                activities.add(mapActivity(rs));
            }
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to get friend activities", e);
        }
        return activities;
    }

    public List<Activity> getServerActivities(String serverOwnerUuid, int page, int pageSize) {
        List<Activity> activities = new ArrayList<>();
        int offset = (page - 1) * pageSize;
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "SELECT * FROM activity_feed WHERE player_uuid = ? AND " +
                "(activity_type = 'server_created' OR activity_type = 'server_started' OR activity_type = 'server_stopped') " +
                "ORDER BY created_at DESC LIMIT ? OFFSET ?");
            stmt.setString(1, serverOwnerUuid);
            stmt.setInt(2, pageSize);
            stmt.setInt(3, offset);
            ResultSet rs = stmt.executeQuery();
            while (rs.next()) {
                activities.add(mapActivity(rs));
            }
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to get server activities", e);
        }
        return activities;
    }

    private Activity mapActivity(ResultSet rs) throws SQLException {
        Activity activity = new Activity(
            rs.getInt("id"),
            UUID.fromString(rs.getString("player_uuid")),
            Activity.ActivityType.valueOf(rs.getString("activity_type")),
            rs.getInt("target_id"),
            parseMetadata(rs.getString("metadata")),
            rs.getTimestamp("created_at")
        );
        ProxiedPlayer player = plugin.getProxy().getPlayer(activity.getPlayerUuid());
        activity.setPlayerName(player != null ? player.getName() : "Unknown");
        return activity;
    }

    private Map<String, Object> parseMetadata(String metadata) {
        Map<String, Object> result = new HashMap<>();
        if (metadata == null || metadata.isEmpty()) return result;

        String content = metadata.replace("{", "").replace("}", "");
        String[] pairs = content.split(", ");
        for (String pair : pairs) {
            String[] kv = pair.split("=");
            if (kv.length == 2) {
                result.put(kv[0].trim(), kv[1].trim());
            }
        }
        return result;
    }
}
