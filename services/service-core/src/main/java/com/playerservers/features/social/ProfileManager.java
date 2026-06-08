package com.playerservers.features.social;

import com.playerservers.PlayerServerPlugin;
import com.playerservers.features.statistics.PlayerStatistics;
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
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.logging.Level;

public class ProfileManager {
    private final PlayerServerPlugin plugin;
    private final FriendManager friendManager;
    private final PlayerStatistics playerStatistics;

    public ProfileManager(PlayerServerPlugin plugin, FriendManager friendManager, PlayerStatistics playerStatistics) {
        this.plugin = plugin;
        this.friendManager = friendManager;
        this.playerStatistics = playerStatistics;
    }

    public PlayerProfile getProfile(UUID playerUuid) {
        PlayerProfile profile = new PlayerProfile(playerUuid);
        ProxiedPlayer player = plugin.getProxy().getPlayer(playerUuid);
        profile.setPlayerName(player != null ? player.getName() : "Unknown");

        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "SELECT * FROM player_profiles WHERE player_uuid = ?");
            stmt.setString(1, playerUuid.toString());
            ResultSet rs = stmt.executeQuery();

            if (rs.next()) {
                profile.setBio(rs.getString("bio"));
                profile.setAvatarUrl(rs.getString("avatar_url"));
                profile.setWebsite(rs.getString("website"));
                profile.setDiscord(rs.getString("discord"));
                profile.setTotalPlaytime(rs.getInt("total_playtime"));
                profile.setServersCreated(rs.getInt("servers_created"));
                profile.setFriendsCount(rs.getInt("friends_count"));
                profile.setReputationScore(rs.getInt("reputation_score"));
            }
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to get profile", e);
        }

        profile.setFriends(friendManager.getFriends(playerUuid));

        List<String> ownedServers = new ArrayList<>();
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "SELECT server_name FROM player_servers WHERE player_uuid = ?");
            stmt.setString(1, playerUuid.toString());
            ResultSet rs = stmt.executeQuery();
            while (rs.next()) {
                ownedServers.add(rs.getString("server_name"));
            }
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to get owned servers", e);
        }
        profile.setOwnedServers(ownedServers);

        Map<String, Object> stats = playerStatistics.getServerSummary(playerUuid);
        profile.setStatistics(stats);

        return profile;
    }

    public boolean setBio(UUID playerUuid, String bio) {
        int maxLength = plugin.getConfigManager().getInt("social.profiles.bio_max_length", 500);
        if (bio.length() > maxLength) return false;

        return updateProfileField(playerUuid, "bio", bio);
    }

    public boolean setWebsite(UUID playerUuid, String website) {
        return updateProfileField(playerUuid, "website", website);
    }

    public boolean setDiscord(UUID playerUuid, String discord) {
        return updateProfileField(playerUuid, "discord", discord);
    }

    private boolean updateProfileField(UUID playerUuid, String field, String value) {
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement check = conn.prepareStatement(
                "SELECT COUNT(*) FROM player_profiles WHERE player_uuid = ?");
            check.setString(1, playerUuid.toString());
            ResultSet rs = check.executeQuery();
            boolean exists = rs.next() && rs.getInt(1) > 0;

            if (exists) {
                PreparedStatement update = conn.prepareStatement(
                    "UPDATE player_profiles SET " + field + " = ? WHERE player_uuid = ?");
                update.setString(1, value);
                update.setString(2, playerUuid.toString());
                update.executeUpdate();
            } else {
                PreparedStatement insert = conn.prepareStatement(
                    "INSERT INTO player_profiles (player_uuid, " + field + ") VALUES (?, ?)");
                insert.setString(1, playerUuid.toString());
                insert.setString(2, value);
                insert.executeUpdate();
            }
            return true;
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to update profile field", e);
            return false;
        }
    }

    public void updatePlaytime(UUID playerUuid, int minutes) {
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "INSERT INTO player_profiles (player_uuid, total_playtime) VALUES (?, ?) " +
                "ON DUPLICATE KEY UPDATE total_playtime = total_playtime + ?");
            stmt.setString(1, playerUuid.toString());
            stmt.setInt(2, minutes);
            stmt.setInt(3, minutes);
            stmt.executeUpdate();
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to update playtime", e);
        }
    }

    public void incrementServersCreated(UUID playerUuid) {
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "INSERT INTO player_profiles (player_uuid, servers_created) VALUES (?, 1) " +
                "ON DUPLICATE KEY UPDATE servers_created = servers_created + 1");
            stmt.setString(1, playerUuid.toString());
            stmt.executeUpdate();
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to increment servers created", e);
        }
    }

    public void updateReputation(UUID playerUuid, int delta) {
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "INSERT INTO player_profiles (player_uuid, reputation_score) VALUES (?, ?) " +
                "ON DUPLICATE KEY UPDATE reputation_score = reputation_score + ?");
            stmt.setString(1, playerUuid.toString());
            stmt.setInt(2, delta);
            stmt.setInt(3, delta);
            stmt.executeUpdate();
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to update reputation", e);
        }
    }
}
