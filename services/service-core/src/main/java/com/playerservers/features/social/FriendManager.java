package com.playerservers.features.social;

import com.playerservers.PlayerServerPlugin;
import net.md_5.bungee.api.connection.ProxiedPlayer;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import java.util.logging.Level;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.sql.Timestamp;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import java.util.logging.Level;

public class FriendManager {
    private final PlayerServerPlugin plugin;

    public FriendManager(PlayerServerPlugin plugin) {
        this.plugin = plugin;
    }

    public boolean sendFriendRequest(UUID sender, UUID target) {
        if (sender.equals(target)) return false;
        if (!canHaveMoreFriends(sender)) return false;

        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement check = conn.prepareStatement(
                "SELECT status FROM friends WHERE player_uuid = ? AND friend_uuid = ?");
            check.setString(1, sender.toString());
            check.setString(2, target.toString());
            ResultSet rs = check.executeQuery();
            if (rs.next()) {
                String status = rs.getString("status");
                if ("accepted".equals(status) || "pending".equals(status)) return false;
                if ("blocked".equals(status)) return false;
            }

            PreparedStatement insert = conn.prepareStatement(
                "INSERT INTO friends (player_uuid, friend_uuid, status) VALUES (?, ?, 'pending')");
            insert.setString(1, sender.toString());
            insert.setString(2, target.toString());
            insert.executeUpdate();

            PreparedStatement reverse = conn.prepareStatement(
                "INSERT INTO friends (player_uuid, friend_uuid, status) VALUES (?, ?, 'pending')");
            reverse.setString(1, target.toString());
            reverse.setString(2, sender.toString());
            reverse.executeUpdate();

            return true;
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to send friend request", e);
            return false;
        }
    }

    public boolean acceptFriendRequest(UUID player, UUID requester) {
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "UPDATE friends SET status = 'accepted', updated_at = CURRENT_TIMESTAMP " +
                "WHERE player_uuid = ? AND friend_uuid = ? AND status = 'pending'");
            stmt.setString(1, player.toString());
            stmt.setString(2, requester.toString());
            int updated = stmt.executeUpdate();

            if (updated > 0) {
                PreparedStatement reverse = conn.prepareStatement(
                    "UPDATE friends SET status = 'accepted', updated_at = CURRENT_TIMESTAMP " +
                    "WHERE player_uuid = ? AND friend_uuid = ? AND status = 'pending'");
                reverse.setString(1, requester.toString());
                reverse.setString(2, player.toString());
                reverse.executeUpdate();
                return true;
            }
            return false;
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to accept friend request", e);
            return false;
        }
    }

    public boolean removeFriend(UUID player, UUID friend) {
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            conn.setAutoCommit(false);
            PreparedStatement stmt1 = conn.prepareStatement(
                "DELETE FROM friends WHERE player_uuid = ? AND friend_uuid = ?");
            stmt1.setString(1, player.toString());
            stmt1.setString(2, friend.toString());
            stmt1.executeUpdate();

            PreparedStatement stmt2 = conn.prepareStatement(
                "DELETE FROM friends WHERE player_uuid = ? AND friend_uuid = ?");
            stmt2.setString(1, friend.toString());
            stmt2.setString(2, player.toString());
            stmt2.executeUpdate();
            conn.commit();
            return true;
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to remove friend", e);
            return false;
        }
    }

    public boolean blockPlayer(UUID player, UUID target) {
        removeFriend(player, target);
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "INSERT INTO friends (player_uuid, friend_uuid, status) VALUES (?, ?, 'blocked') " +
                "ON DUPLICATE KEY UPDATE status = 'blocked', updated_at = CURRENT_TIMESTAMP");
            stmt.setString(1, player.toString());
            stmt.setString(2, target.toString());
            stmt.executeUpdate();
            return true;
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to block player", e);
            return false;
        }
    }

    public boolean isBlocked(UUID player, UUID target) {
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "SELECT status FROM friends WHERE player_uuid = ? AND friend_uuid = ? AND status = 'blocked'");
            stmt.setString(1, player.toString());
            stmt.setString(2, target.toString());
            return stmt.executeQuery().next();
        } catch (SQLException e) {
            return false;
        }
    }

    public List<Friend> getFriends(UUID player) {
        List<Friend> friends = new ArrayList<>();
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "SELECT f.*, p.server_status as friend_status FROM friends f " +
                "LEFT JOIN player_servers p ON f.friend_uuid = p.player_uuid " +
                "WHERE f.player_uuid = ? AND f.status = 'accepted'");
            stmt.setString(1, player.toString());
            ResultSet rs = stmt.executeQuery();
            while (rs.next()) {
                Friend friend = new Friend(
                    rs.getInt("id"),
                    UUID.fromString(rs.getString("player_uuid")),
                    UUID.fromString(rs.getString("friend_uuid")),
                    Friend.Status.valueOf(rs.getString("status")),
                    rs.getTimestamp("created_at"),
                    rs.getTimestamp("updated_at")
                );
                ProxiedPlayer fp = plugin.getProxy().getPlayer(friend.getFriendUuid());
                friend.setFriendOnline(fp != null);
                friend.setFriendName(fp != null ? fp.getName() : "Unknown");
                friends.add(friend);
            }
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to get friends list", e);
        }
        return friends;
    }

    public List<Friend> getPendingRequests(UUID player) {
        List<Friend> requests = new ArrayList<>();
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "SELECT * FROM friends WHERE player_uuid = ? AND status = 'pending' " +
                "AND friend_uuid NOT IN (SELECT player_uuid FROM friends WHERE friend_uuid = ? AND status = 'pending')");
            stmt.setString(1, player.toString());
            stmt.setString(2, player.toString());
            ResultSet rs = stmt.executeQuery();
            while (rs.next()) {
                Friend friend = new Friend(
                    rs.getInt("id"),
                    UUID.fromString(rs.getString("player_uuid")),
                    UUID.fromString(rs.getString("friend_uuid")),
                    Friend.Status.valueOf(rs.getString("status")),
                    rs.getTimestamp("created_at"),
                    rs.getTimestamp("updated_at")
                );
                ProxiedPlayer fp = plugin.getProxy().getPlayer(friend.getFriendUuid());
                friend.setFriendName(fp != null ? fp.getName() : "Unknown");
                requests.add(friend);
            }
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to get pending requests", e);
        }
        return requests;
    }

    public int getFriendCount(UUID player) {
        return getFriends(player).size();
    }

    public boolean areFriends(UUID player1, UUID player2) {
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "SELECT COUNT(*) FROM friends WHERE player_uuid = ? AND friend_uuid = ? AND status = 'accepted'");
            stmt.setString(1, player1.toString());
            stmt.setString(2, player2.toString());
            ResultSet rs = stmt.executeQuery();
            return rs.next() && rs.getInt(1) > 0;
        } catch (SQLException e) {
            return false;
        }
    }

    private boolean canHaveMoreFriends(UUID player) {
        int maxFriends = plugin.getConfigManager().getInt("social.friends.max_friends", 100);
        return getFriendCount(player) < maxFriends;
    }
}
