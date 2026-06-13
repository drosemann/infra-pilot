package com.playerservers.features.social;

import com.playerservers.PlayerServerPlugin;
import net.md_5.bungee.api.connection.ProxiedPlayer;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.UUID;
import java.util.logging.Level;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.UUID;
import java.util.logging.Level;

public class ServerDiscoveryManager {
    private final PlayerServerPlugin plugin;

    public ServerDiscoveryManager(PlayerServerPlugin plugin) {
        this.plugin = plugin;
    }

    public List<ServerListing> getPublicServers(int page, int pageSize) {
        List<ServerListing> listings = new ArrayList<>();
        int offset = (page - 1) * pageSize;
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "SELECT ps.*, " +
                "(SELECT COALESCE(AVG(rating), 0) FROM server_reviews WHERE server_id = ps.player_uuid) as avg_rating, " +
                "(SELECT COUNT(*) FROM server_reviews WHERE server_id = ps.player_uuid) as review_count " +
                "FROM player_servers ps WHERE ps.is_public = true " +
                "ORDER BY ps.last_updated DESC LIMIT ? OFFSET ?");
            stmt.setInt(1, pageSize);
            stmt.setInt(2, offset);
            ResultSet rs = stmt.executeQuery();
            while (rs.next()) {
                listings.add(mapListing(rs));
            }
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to get public servers", e);
        }
        return listings;
    }

    public List<ServerListing> searchServers(String query, int page, int pageSize) {
        List<ServerListing> listings = new ArrayList<>();
        int offset = (page - 1) * pageSize;
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "SELECT ps.*, " +
                "(SELECT COALESCE(AVG(rating), 0) FROM server_reviews WHERE server_id = ps.player_uuid) as avg_rating, " +
                "(SELECT COUNT(*) FROM server_reviews WHERE server_id = ps.player_uuid) as review_count " +
                "FROM player_servers ps WHERE ps.is_public = true " +
                "AND (ps.server_name LIKE ? OR ps.description LIKE ? OR ps.tags LIKE ?) " +
                "ORDER BY ps.last_updated DESC LIMIT ? OFFSET ?");
            String searchPattern = "%" + query + "%";
            stmt.setString(1, searchPattern);
            stmt.setString(2, searchPattern);
            stmt.setString(3, searchPattern);
            stmt.setInt(4, pageSize);
            stmt.setInt(5, offset);
            ResultSet rs = stmt.executeQuery();
            while (rs.next()) {
                listings.add(mapListing(rs));
            }
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to search servers", e);
        }
        return listings;
    }

    public List<ServerListing> getServersByTag(String tag, int page, int pageSize) {
        List<ServerListing> listings = new ArrayList<>();
        int offset = (page - 1) * pageSize;
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "SELECT ps.*, " +
                "(SELECT COALESCE(AVG(rating), 0) FROM server_reviews WHERE server_id = ps.player_uuid) as avg_rating, " +
                "(SELECT COUNT(*) FROM server_reviews WHERE server_id = ps.player_uuid) as review_count " +
                "FROM player_servers ps WHERE ps.is_public = true " +
                "AND ps.tags LIKE ? ORDER BY ps.last_updated DESC LIMIT ? OFFSET ?");
            stmt.setString(1, "%" + tag + "%");
            stmt.setInt(2, pageSize);
            stmt.setInt(3, offset);
            ResultSet rs = stmt.executeQuery();
            while (rs.next()) {
                listings.add(mapListing(rs));
            }
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to get servers by tag", e);
        }
        return listings;
    }

    public List<ServerListing> getTopRatedServers(int page, int pageSize) {
        List<ServerListing> listings = new ArrayList<>();
        int offset = (page - 1) * pageSize;
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "SELECT ps.*, " +
                "(SELECT COALESCE(AVG(rating), 0) FROM server_reviews WHERE server_id = ps.player_uuid) as avg_rating, " +
                "(SELECT COUNT(*) FROM server_reviews WHERE server_id = ps.player_uuid) as review_count " +
                "FROM player_servers ps WHERE ps.is_public = true " +
                "ORDER BY avg_rating DESC, ps.upvotes DESC LIMIT ? OFFSET ?");
            stmt.setInt(1, pageSize);
            stmt.setInt(2, offset);
            ResultSet rs = stmt.executeQuery();
            while (rs.next()) {
                listings.add(mapListing(rs));
            }
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to get top rated servers", e);
        }
        return listings;
    }

    public List<ServerListing> getNewestServers(int page, int pageSize) {
        List<ServerListing> listings = new ArrayList<>();
        int offset = (page - 1) * pageSize;
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "SELECT ps.*, " +
                "(SELECT COALESCE(AVG(rating), 0) FROM server_reviews WHERE server_id = ps.player_uuid) as avg_rating, " +
                "(SELECT COUNT(*) FROM server_reviews WHERE server_id = ps.player_uuid) as review_count " +
                "FROM player_servers ps WHERE ps.is_public = true " +
                "ORDER BY ps.creation_time DESC LIMIT ? OFFSET ?");
            stmt.setInt(1, pageSize);
            stmt.setInt(2, offset);
            ResultSet rs = stmt.executeQuery();
            while (rs.next()) {
                listings.add(mapListing(rs));
            }
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to get newest servers", e);
        }
        return listings;
    }

    public boolean setServerPublic(String playerUuid, boolean isPublic, String description, String tags) {
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "UPDATE player_servers SET is_public = ?, description = ?, tags = ?, last_updated = CURRENT_TIMESTAMP " +
                "WHERE player_uuid = ?");
            stmt.setBoolean(1, isPublic);
            stmt.setString(2, description);
            stmt.setString(3, tags);
            stmt.setString(4, playerUuid);
            return stmt.executeUpdate() > 0;
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to toggle server public status", e);
            return false;
        }
    }

    public void upvoteServer(String playerUuid) {
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "UPDATE player_servers SET upvotes = upvotes + 1 WHERE player_uuid = ?");
            stmt.setString(1, playerUuid);
            stmt.executeUpdate();
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to upvote server", e);
        }
    }

    public void downvoteServer(String playerUuid) {
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "UPDATE player_servers SET downvotes = downvotes + 1 WHERE player_uuid = ?");
            stmt.setString(1, playerUuid);
            stmt.executeUpdate();
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to downvote server", e);
        }
    }

    public int getPublicServerCount() {
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "SELECT COUNT(*) FROM player_servers WHERE is_public = true");
            ResultSet rs = stmt.executeQuery();
            if (rs.next()) return rs.getInt(1);
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to count public servers", e);
        }
        return 0;
    }

    private ServerListing mapListing(ResultSet rs) throws SQLException {
        ServerListing listing = new ServerListing(
            0,
            rs.getString("player_uuid"),
            rs.getString("server_name"),
            rs.getString("description"),
            rs.getString("tags") != null ? Arrays.asList(rs.getString("tags").split(",")) : new ArrayList<String>(),
            rs.getInt("player_count"),
            rs.getInt("max_players"),
            rs.getInt("upvotes"),
            rs.getInt("downvotes"),
            rs.getBoolean("is_public"),
            rs.getTimestamp("last_updated")
        );
        listing.setAverageRating(rs.getDouble("avg_rating"));
        listing.setReviewCount(rs.getInt("review_count"));

        String ownerUuid = rs.getString("player_uuid");
        if (ownerUuid != null) {
            ProxiedPlayer owner = plugin.getProxy().getPlayer(UUID.fromString(ownerUuid));
            listing.setOwnerName(owner != null ? owner.getName() : "Unknown");
        }
        return listing;
    }
}
