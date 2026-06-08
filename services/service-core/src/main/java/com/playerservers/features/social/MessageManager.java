package com.playerservers.features.social;

import com.playerservers.PlayerServerPlugin;
import net.md_5.bungee.api.connection.ProxiedPlayer;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Timestamp;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import java.util.logging.Level;

public class MessageManager {
    private final PlayerServerPlugin plugin;
    private final FriendManager friendManager;

    public MessageManager(PlayerServerPlugin plugin, FriendManager friendManager) {
        this.plugin = plugin;
        this.friendManager = friendManager;
    }

    public boolean sendMessage(UUID sender, UUID receiver, String message) {
        int maxLength = plugin.getConfigManager().getInt("social.messaging.max_message_length", 256);
        if (message.length() > maxLength) return false;
        if (friendManager.isBlocked(sender, receiver)) return false;

        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "INSERT INTO messages (sender_uuid, receiver_uuid, message) VALUES (?, ?, ?)");
            stmt.setString(1, sender.toString());
            stmt.setString(2, receiver.toString());
            stmt.setString(3, message);
            stmt.executeUpdate();
            return true;
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to send message", e);
            return false;
        }
    }

    public List<Message> getInbox(UUID player) {
        List<Message> messages = new ArrayList<>();
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "SELECT * FROM messages WHERE receiver_uuid = ? ORDER BY created_at DESC LIMIT 50");
            stmt.setString(1, player.toString());
            ResultSet rs = stmt.executeQuery();
            while (rs.next()) {
                Message msg = new Message(
                    rs.getInt("id"),
                    UUID.fromString(rs.getString("sender_uuid")),
                    UUID.fromString(rs.getString("receiver_uuid")),
                    rs.getString("message"),
                    rs.getBoolean("is_read"),
                    rs.getTimestamp("created_at")
                );
                ProxiedPlayer sender = plugin.getProxy().getPlayer(msg.getSenderUuid());
                msg.setSenderName(sender != null ? sender.getName() : "Unknown");
                messages.add(msg);
            }
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to get inbox", e);
        }
        return messages;
    }

    public List<Message> getConversation(UUID player1, UUID player2) {
        List<Message> messages = new ArrayList<>();
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "SELECT * FROM messages WHERE (sender_uuid = ? AND receiver_uuid = ?) " +
                "OR (sender_uuid = ? AND receiver_uuid = ?) ORDER BY created_at ASC");
            stmt.setString(1, player1.toString());
            stmt.setString(2, player2.toString());
            stmt.setString(3, player2.toString());
            stmt.setString(4, player1.toString());
            ResultSet rs = stmt.executeQuery();
            while (rs.next()) {
                Message msg = new Message(
                    rs.getInt("id"),
                    UUID.fromString(rs.getString("sender_uuid")),
                    UUID.fromString(rs.getString("receiver_uuid")),
                    rs.getString("message"),
                    rs.getBoolean("is_read"),
                    rs.getTimestamp("created_at")
                );
                ProxiedPlayer sender = plugin.getProxy().getPlayer(msg.getSenderUuid());
                msg.setSenderName(sender != null ? sender.getName() : "Unknown");
                messages.add(msg);
            }
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to get conversation", e);
        }
        return messages;
    }

    public int getUnreadCount(UUID player) {
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "SELECT COUNT(*) FROM messages WHERE receiver_uuid = ? AND is_read = false");
            stmt.setString(1, player.toString());
            ResultSet rs = stmt.executeQuery();
            if (rs.next()) return rs.getInt(1);
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to get unread count", e);
        }
        return 0;
    }

    public void markAsRead(UUID player, int messageId) {
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "UPDATE messages SET is_read = true WHERE id = ? AND receiver_uuid = ?");
            stmt.setInt(1, messageId);
            stmt.setString(2, player.toString());
            stmt.executeUpdate();
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to mark message as read", e);
        }
    }

    public void markAllAsRead(UUID player) {
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "UPDATE messages SET is_read = true WHERE receiver_uuid = ? AND is_read = false");
            stmt.setString(1, player.toString());
            stmt.executeUpdate();
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to mark all as read", e);
        }
    }

    public void clearInbox(UUID player) {
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "DELETE FROM messages WHERE receiver_uuid = ?");
            stmt.setString(1, player.toString());
            stmt.executeUpdate();
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to clear inbox", e);
        }
    }

    public int getMessageCount(UUID player) {
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "SELECT COUNT(*) FROM messages WHERE sender_uuid = ? AND created_at > DATE_SUB(NOW(), INTERVAL 1 MINUTE)");
            stmt.setString(1, player.toString());
            ResultSet rs = stmt.executeQuery();
            if (rs.next()) return rs.getInt(1);
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to count messages", e);
        }
        return 0;
    }
}
