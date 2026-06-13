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
import java.util.concurrent.TimeUnit;
import java.util.logging.Level;

public class InvitationManager {
    private final PlayerServerPlugin plugin;

    public InvitationManager(PlayerServerPlugin plugin) {
        this.plugin = plugin;
    }

    public boolean sendInvitation(UUID inviter, UUID invitee, String serverId,
                                 ServerInvitation.PermissionLevel permission) {
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement check = conn.prepareStatement(
                "SELECT COUNT(*) FROM server_invitations WHERE server_id = ? AND invitee_uuid = ? AND status = 'pending'");
            check.setString(1, serverId);
            check.setString(2, invitee.toString());
            ResultSet rs = check.executeQuery();
            if (rs.next() && rs.getInt(1) > 0) return false;

            Timestamp expiresAt = new Timestamp(System.currentTimeMillis() + TimeUnit.DAYS.toMillis(7));
            PreparedStatement insert = conn.prepareStatement(
                "INSERT INTO server_invitations (server_id, inviter_uuid, invitee_uuid, permission_level, status, expires_at) " +
                "VALUES (?, ?, ?, ?, 'pending', ?)");
            insert.setString(1, serverId);
            insert.setString(2, inviter.toString());
            insert.setString(3, invitee.toString());
            insert.setString(4, permission.name());
            insert.setTimestamp(5, expiresAt);
            insert.executeUpdate();
            return true;
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to send invitation", e);
            return false;
        }
    }

    public boolean acceptInvitation(int invitationId) {
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "UPDATE server_invitations SET status = 'accepted' WHERE id = ? AND status = 'pending' AND " +
                "(expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)");
            stmt.setInt(1, invitationId);
            return stmt.executeUpdate() > 0;
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to accept invitation", e);
            return false;
        }
    }

    public boolean declineInvitation(int invitationId) {
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "UPDATE server_invitations SET status = 'declined' WHERE id = ? AND status = 'pending'");
            stmt.setInt(1, invitationId);
            return stmt.executeUpdate() > 0;
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to decline invitation", e);
            return false;
        }
    }

    public List<ServerInvitation> getPendingInvitations(UUID player) {
        List<ServerInvitation> invitations = new ArrayList<>();
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "SELECT i.*, ps.server_name FROM server_invitations i " +
                "JOIN player_servers ps ON i.server_id = ps.player_uuid " +
                "WHERE i.invitee_uuid = ? AND i.status = 'pending' " +
                "AND (i.expires_at IS NULL OR i.expires_at > CURRENT_TIMESTAMP)");
            stmt.setString(1, player.toString());
            ResultSet rs = stmt.executeQuery();
            while (rs.next()) {
                ServerInvitation inv = new ServerInvitation(
                    rs.getInt("id"),
                    rs.getString("server_id"),
                    UUID.fromString(rs.getString("inviter_uuid")),
                    UUID.fromString(rs.getString("invitee_uuid")),
                    ServerInvitation.PermissionLevel.valueOf(rs.getString("permission_level")),
                    ServerInvitation.Status.valueOf(rs.getString("status")),
                    rs.getTimestamp("expires_at"),
                    rs.getTimestamp("created_at")
                );
                inv.setServerName(rs.getString("server_name"));
                ProxiedPlayer inviter = plugin.getProxy().getPlayer(inv.getInviterUuid());
                inv.setInviterName(inviter != null ? inviter.getName() : "Unknown");
                invitations.add(inv);
            }
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to get pending invitations", e);
        }
        return invitations;
    }

    public List<ServerInvitation> getSentInvitations(UUID player) {
        List<ServerInvitation> invitations = new ArrayList<>();
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "SELECT i.*, ps.server_name FROM server_invitations i " +
                "JOIN player_servers ps ON i.server_id = ps.player_uuid " +
                "WHERE i.inviter_uuid = ? ORDER BY i.created_at DESC");
            stmt.setString(1, player.toString());
            ResultSet rs = stmt.executeQuery();
            while (rs.next()) {
                ServerInvitation inv = new ServerInvitation(
                    rs.getInt("id"),
                    rs.getString("server_id"),
                    UUID.fromString(rs.getString("inviter_uuid")),
                    UUID.fromString(rs.getString("invitee_uuid")),
                    ServerInvitation.PermissionLevel.valueOf(rs.getString("permission_level")),
                    ServerInvitation.Status.valueOf(rs.getString("status")),
                    rs.getTimestamp("expires_at"),
                    rs.getTimestamp("created_at")
                );
                inv.setServerName(rs.getString("server_name"));
                ProxiedPlayer invitee = plugin.getProxy().getPlayer(inv.getInviteeUuid());
                inv.setInviterName(invitee != null ? invitee.getName() : "Unknown");
                invitations.add(inv);
            }
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to get sent invitations", e);
        }
        return invitations;
    }

    public void expireOldInvitations() {
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "UPDATE server_invitations SET status = 'expired' WHERE status = 'pending' " +
                "AND expires_at IS NOT NULL AND expires_at <= CURRENT_TIMESTAMP");
            stmt.executeUpdate();
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to expire old invitations", e);
        }
    }
}
