package com.playerservers.features.social;

import com.playerservers.PlayerServerPlugin;
import com.playerservers.features.economy.EconomyManager;
import net.md_5.bungee.api.connection.ProxiedPlayer;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import java.util.logging.Level;

public class ReviewManager {
    private final PlayerServerPlugin plugin;
    private final EconomyManager economyManager;

    public ReviewManager(PlayerServerPlugin plugin, EconomyManager economyManager) {
        this.plugin = plugin;
        this.economyManager = economyManager;
    }

    public boolean submitReview(UUID reviewer, String serverOwnerUuid, int rating, String comment) {
        if (rating < 1 || rating > 5) return false;
        if (reviewer.toString().equals(serverOwnerUuid)) return false;

        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement check = conn.prepareStatement(
                "SELECT COUNT(*) FROM server_reviews WHERE server_id = ? AND reviewer_uuid = ?");
            check.setString(1, serverOwnerUuid);
            check.setString(2, reviewer.toString());
            ResultSet rs = check.executeQuery();
            if (rs.next() && rs.getInt(1) > 0) return false;

            PreparedStatement insert = conn.prepareStatement(
                "INSERT INTO server_reviews (server_id, reviewer_uuid, rating, comment) VALUES (?, ?, ?, ?)");
            insert.setString(1, serverOwnerUuid);
            insert.setString(2, reviewer.toString());
            insert.setInt(3, rating);
            insert.setString(4, comment);
            insert.executeUpdate();

            if (comment != null && comment.length() > 20) {
                economyManager.deposit(reviewer, 5.0, "Quality review bonus");
            }

            return true;
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to submit review", e);
            return false;
        }
    }

    public List<ServerReview> getServerReviews(String serverOwnerUuid) {
        List<ServerReview> reviews = new ArrayList<>();
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "SELECT * FROM server_reviews WHERE server_id = ? ORDER BY created_at DESC");
            stmt.setString(1, serverOwnerUuid);
            ResultSet rs = stmt.executeQuery();
            while (rs.next()) {
                ServerReview review = new ServerReview(
                    rs.getInt("id"),
                    rs.getString("server_id"),
                    UUID.fromString(rs.getString("reviewer_uuid")),
                    rs.getInt("rating"),
                    rs.getString("comment"),
                    rs.getTimestamp("created_at"),
                    rs.getTimestamp("updated_at")
                );
                ProxiedPlayer rp = plugin.getProxy().getPlayer(review.getReviewerUuid());
                review.setReviewerName(rp != null ? rp.getName() : "Unknown");
                reviews.add(review);
            }
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to get server reviews", e);
        }
        return reviews;
    }

    public List<ServerReview> getPlayerReviews(UUID reviewer) {
        List<ServerReview> reviews = new ArrayList<>();
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "SELECT sr.*, ps.server_name FROM server_reviews sr " +
                "JOIN player_servers ps ON sr.server_id = ps.player_uuid " +
                "WHERE sr.reviewer_uuid = ? ORDER BY sr.created_at DESC");
            stmt.setString(1, reviewer.toString());
            ResultSet rs = stmt.executeQuery();
            while (rs.next()) {
                ServerReview review = new ServerReview(
                    rs.getInt("id"),
                    rs.getString("server_id"),
                    UUID.fromString(rs.getString("reviewer_uuid")),
                    rs.getInt("rating"),
                    rs.getString("comment"),
                    rs.getTimestamp("created_at"),
                    rs.getTimestamp("updated_at")
                );
                review.setReviewerName(rs.getString("server_name"));
                reviews.add(review);
            }
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to get player reviews", e);
        }
        return reviews;
    }

    public double getAverageRating(String serverOwnerUuid) {
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "SELECT COALESCE(AVG(rating), 0) FROM server_reviews WHERE server_id = ?");
            stmt.setString(1, serverOwnerUuid);
            ResultSet rs = stmt.executeQuery();
            if (rs.next()) return rs.getDouble(1);
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to get average rating", e);
        }
        return 0;
    }

    public int getReviewCount(String serverOwnerUuid) {
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "SELECT COUNT(*) FROM server_reviews WHERE server_id = ?");
            stmt.setString(1, serverOwnerUuid);
            ResultSet rs = stmt.executeQuery();
            if (rs.next()) return rs.getInt(1);
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to get review count", e);
        }
        return 0;
    }
}
