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
import java.sql.Timestamp;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import java.util.logging.Level;

public class CommunityManager {
    private final PlayerServerPlugin plugin;

    public CommunityManager(PlayerServerPlugin plugin) {
        this.plugin = plugin;
    }

    public boolean createCommunity(UUID owner, String name, String description, boolean isPublic) {
        int maxCommunities = plugin.getConfigManager().getInt("social.communities.max_communities_per_player", 5);
        if (getPlayerCommunityCount(owner) >= maxCommunities) return false;

        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement check = conn.prepareStatement(
                "SELECT COUNT(*) FROM communities WHERE name = ?");
            check.setString(1, name);
            ResultSet rs = check.executeQuery();
            if (rs.next() && rs.getInt(1) > 0) return false;

            PreparedStatement insert = conn.prepareStatement(
                "INSERT INTO communities (name, description, owner_uuid, is_public) VALUES (?, ?, ?, ?)",
                PreparedStatement.RETURN_GENERATED_KEYS);
            insert.setString(1, name);
            insert.setString(2, description);
            insert.setString(3, owner.toString());
            insert.setBoolean(4, isPublic);
            insert.executeUpdate();

            ResultSet keys = insert.getGeneratedKeys();
            if (keys.next()) {
                int communityId = keys.getInt(1);
                addMember(communityId, owner, Community.MemberRole.owner);
            }
            return true;
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to create community", e);
            return false;
        }
    }

    public boolean joinCommunity(int communityId, UUID player) {
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement check = conn.prepareStatement(
                "SELECT COUNT(*) FROM community_members WHERE community_id = ? AND player_uuid = ?");
            check.setInt(1, communityId);
            check.setString(2, player.toString());
            ResultSet rs = check.executeQuery();
            if (rs.next() && rs.getInt(1) > 0) return false;

            int maxMembers = plugin.getConfigManager().getInt("social.communities.max_members_per_community", 100);
            PreparedStatement count = conn.prepareStatement(
                "SELECT COUNT(*) FROM community_members WHERE community_id = ?");
            count.setInt(1, communityId);
            ResultSet cr = count.executeQuery();
            if (cr.next() && cr.getInt(1) >= maxMembers) return false;

            return addMember(communityId, player, Community.MemberRole.member);
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to join community", e);
            return false;
        }
    }

    public boolean leaveCommunity(int communityId, UUID player) {
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "DELETE FROM community_members WHERE community_id = ? AND player_uuid = ? AND role != 'owner'");
            stmt.setInt(1, communityId);
            stmt.setString(2, player.toString());
            int removed = stmt.executeUpdate();

            if (removed > 0) {
                PreparedStatement update = conn.prepareStatement(
                    "UPDATE communities SET member_count = member_count - 1 WHERE id = ?");
                update.setInt(1, communityId);
                update.executeUpdate();
                return true;
            }
            return false;
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to leave community", e);
            return false;
        }
    }

    public boolean inviteToCommunity(int communityId, UUID inviter, UUID invitee) {
        if (!isMember(communityId, inviter)) return false;
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "SELECT role FROM community_members WHERE community_id = ? AND player_uuid = ?");
            stmt.setInt(1, communityId);
            stmt.setString(2, inviter.toString());
            ResultSet rs = stmt.executeQuery();
            if (!rs.next()) return false;
            String role = rs.getString("role");
            if (!"owner".equals(role) && !"admin".equals(role)) return false;
        } catch (SQLException e) {
            return false;
        }
        return joinCommunity(communityId, invitee);
    }

    public List<Community> listCommunities(int page, int pageSize) {
        List<Community> communities = new ArrayList<>();
        int offset = (page - 1) * pageSize;
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "SELECT * FROM communities WHERE is_public = true ORDER BY member_count DESC LIMIT ? OFFSET ?");
            stmt.setInt(1, pageSize);
            stmt.setInt(2, offset);
            ResultSet rs = stmt.executeQuery();
            while (rs.next()) {
                communities.add(mapCommunity(rs));
            }
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to list communities", e);
        }
        return communities;
    }

    public Community getCommunity(int communityId) {
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "SELECT * FROM communities WHERE id = ?");
            stmt.setInt(1, communityId);
            ResultSet rs = stmt.executeQuery();
            if (rs.next()) {
                Community community = mapCommunity(rs);
                community.setMembers(getMembers(communityId));
                return community;
            }
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to get community", e);
        }
        return null;
    }

    public List<Community> getPlayerCommunities(UUID player) {
        List<Community> communities = new ArrayList<>();
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "SELECT c.*, cm.role FROM communities c " +
                "JOIN community_members cm ON c.id = cm.community_id " +
                "WHERE cm.player_uuid = ? ORDER BY c.name");
            stmt.setString(1, player.toString());
            ResultSet rs = stmt.executeQuery();
            while (rs.next()) {
                Community community = mapCommunity(rs);
                community.setUserRole(Community.MemberRole.valueOf(rs.getString("role")));
                communities.add(community);
            }
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to get player communities", e);
        }
        return communities;
    }

    public boolean isMember(int communityId, UUID player) {
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "SELECT COUNT(*) FROM community_members WHERE community_id = ? AND player_uuid = ?");
            stmt.setInt(1, communityId);
            stmt.setString(2, player.toString());
            ResultSet rs = stmt.executeQuery();
            return rs.next() && rs.getInt(1) > 0;
        } catch (SQLException e) {
            return false;
        }
    }

    public Community.MemberRole getMemberRole(int communityId, UUID player) {
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "SELECT role FROM community_members WHERE community_id = ? AND player_uuid = ?");
            stmt.setInt(1, communityId);
            stmt.setString(2, player.toString());
            ResultSet rs = stmt.executeQuery();
            if (rs.next()) {
                return Community.MemberRole.valueOf(rs.getString("role"));
            }
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to get member role", e);
        }
        return null;
    }

    public boolean setMemberRole(int communityId, UUID admin, UUID target, Community.MemberRole newRole) {
        Community.MemberRole adminRole = getMemberRole(communityId, admin);
        if (adminRole != Community.MemberRole.owner) return false;

        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "UPDATE community_members SET role = ? WHERE community_id = ? AND player_uuid = ?");
            stmt.setString(1, newRole.name());
            stmt.setInt(2, communityId);
            stmt.setString(3, target.toString());
            return stmt.executeUpdate() > 0;
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to set member role", e);
            return false;
        }
    }

    private boolean addMember(int communityId, UUID player, Community.MemberRole role) {
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement insert = conn.prepareStatement(
                "INSERT INTO community_members (community_id, player_uuid, role) VALUES (?, ?, ?)");
            insert.setInt(1, communityId);
            insert.setString(2, player.toString());
            insert.setString(3, role.name());
            insert.executeUpdate();

            PreparedStatement update = conn.prepareStatement(
                "UPDATE communities SET member_count = member_count + 1 WHERE id = ?");
            update.setInt(1, communityId);
            update.executeUpdate();
            return true;
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to add member", e);
            return false;
        }
    }

    private List<CommunityMember> getMembers(int communityId) {
        List<CommunityMember> members = new ArrayList<>();
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "SELECT * FROM community_members WHERE community_id = ? ORDER BY joined_at ASC");
            stmt.setInt(1, communityId);
            ResultSet rs = stmt.executeQuery();
            while (rs.next()) {
                CommunityMember member = new CommunityMember(
                    rs.getInt("id"),
                    rs.getInt("community_id"),
                    UUID.fromString(rs.getString("player_uuid")),
                    Community.MemberRole.valueOf(rs.getString("role")),
                    rs.getTimestamp("joined_at")
                );
                ProxiedPlayer mp = plugin.getProxy().getPlayer(member.getPlayerUuid());
                member.setPlayerName(mp != null ? mp.getName() : "Unknown");
                members.add(member);
            }
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to get members", e);
        }
        return members;
    }

    private int getPlayerCommunityCount(UUID player) {
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "SELECT COUNT(*) FROM community_members WHERE player_uuid = ?");
            stmt.setString(1, player.toString());
            ResultSet rs = stmt.executeQuery();
            if (rs.next()) return rs.getInt(1);
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to count communities", e);
        }
        return 0;
    }

    private Community mapCommunity(ResultSet rs) throws SQLException {
        Community community = new Community(
            rs.getInt("id"),
            rs.getString("name"),
            rs.getString("description"),
            UUID.fromString(rs.getString("owner_uuid")),
            rs.getInt("member_count"),
            rs.getBoolean("is_public"),
            rs.getTimestamp("created_at")
        );
        ProxiedPlayer owner = plugin.getProxy().getPlayer(community.getOwnerUuid());
        community.setOwnerName(owner != null ? owner.getName() : "Unknown");
        return community;
    }
}
