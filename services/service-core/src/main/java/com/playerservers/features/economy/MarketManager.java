package com.playerservers.features.economy;

import com.playerservers.PlayerServerPlugin;
import net.md_5.bungee.api.ChatColor;
import net.md_5.bungee.api.CommandSender;
import net.md_5.bungee.api.chat.ComponentBuilder;
import net.md_5.bungee.api.chat.HoverEvent;
import net.md_5.bungee.api.chat.TextComponent;
import net.md_5.bungee.api.connection.ProxiedPlayer;
import net.md_5.bungee.api.plugin.Command;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import java.util.logging.Level;

public class MarketManager {

    private final PlayerServerPlugin plugin;
    private final EconomyManager economyManager;
    private final double listingFee;
    private final double saleTax;

    public MarketManager(PlayerServerPlugin plugin, EconomyManager economyManager) {
        this.plugin = plugin;
        this.economyManager = economyManager;
        this.listingFee = plugin.getConfigManager().getDouble("economy.market_listing_fee", 5.0);
        this.saleTax = plugin.getConfigManager().getDouble("economy.market_sale_tax", 0.03);
        initDatabase();
    }

    private void initDatabase() {
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            conn.createStatement().execute("CREATE TABLE IF NOT EXISTS market_listings (" +
                "id BIGINT AUTO_INCREMENT PRIMARY KEY," +
                "seller_uuid VARCHAR(36)," +
                "item_name VARCHAR(128)," +
                "item_data TEXT," +
                "price DOUBLE," +
                "quantity INT," +
                "listed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP" +
                ")");
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to init market DB", e);
        }
    }

    public boolean listItem(UUID seller, String itemName, String itemData, double price, int quantity) {
        if (!economyManager.withdraw(seller, listingFee, "Market listing fee")) return false;
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "INSERT INTO market_listings (seller_uuid, item_name, item_data, price, quantity) VALUES (?,?,?,?,?)");
            stmt.setString(1, seller.toString());
            stmt.setString(2, itemName);
            stmt.setString(3, itemData);
            stmt.setDouble(4, price);
            stmt.setInt(5, quantity);
            stmt.executeUpdate();
            return true;
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to create listing", e);
            return false;
        }
    }

    public boolean buyItem(UUID buyer, long listingId, int quantity) {
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            conn.setAutoCommit(false);
            PreparedStatement getStmt = conn.prepareStatement(
                "SELECT seller_uuid, price, quantity FROM market_listings WHERE id = ?");
            getStmt.setLong(1, listingId);
            ResultSet rs = getStmt.executeQuery();
            if (!rs.next()) return false;

            String sellerStr = rs.getString("seller_uuid");
            double unitPrice = rs.getDouble("price");
            int available = rs.getInt("quantity");
            if (quantity > available) quantity = available;

            double totalCost = unitPrice * quantity;
            double taxAmount = totalCost * saleTax;
            double sellerRevenue = totalCost - taxAmount;

            if (!economyManager.hasBalance(buyer, totalCost)) return false;

            if (economyManager.withdraw(buyer, totalCost, "Market purchase")) {
                economyManager.deposit(UUID.fromString(sellerStr), sellerRevenue, "Market sale");

                if (quantity >= available) {
                    PreparedStatement delStmt = conn.prepareStatement("DELETE FROM market_listings WHERE id = ?");
                    delStmt.setLong(1, listingId);
                    delStmt.executeUpdate();
                } else {
                    PreparedStatement updStmt = conn.prepareStatement(
                        "UPDATE market_listings SET quantity = quantity - ? WHERE id = ?");
                    updStmt.setInt(1, quantity);
                    updStmt.setLong(2, listingId);
                    updStmt.executeUpdate();
                }
                conn.commit();
                return true;
            }
            conn.rollback();
            return false;
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to buy item", e);
            return false;
        }
    }

    public List<String> searchItems(String query) {
        List<String> results = new ArrayList<>();
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "SELECT id, seller_uuid, item_name, price, quantity FROM market_listings WHERE item_name LIKE ? LIMIT 50");
            stmt.setString(1, "%" + query + "%");
            ResultSet rs = stmt.executeQuery();
            while (rs.next()) {
                results.add("ID:" + rs.getLong("id") + " | " + rs.getString("item_name") +
                    " x" + rs.getInt("quantity") + " | $" + String.format("%.2f", rs.getDouble("price")));
            }
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to search market", e);
        }
        return results;
    }

    public void cancelListing(UUID seller, long listingId) {
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "DELETE FROM market_listings WHERE id = ? AND seller_uuid = ?");
            stmt.setLong(1, listingId);
            stmt.setString(2, seller.toString());
            stmt.executeUpdate();
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to cancel listing", e);
        }
    }

    public static class MarketCommands {
        private final PlayerServerPlugin plugin;
        private final MarketManager market;

        public MarketCommands(PlayerServerPlugin plugin, MarketManager market) {
            this.plugin = plugin;
            this.market = market;
            plugin.getProxy().getPluginManager().registerCommand(plugin, new MarketCommand());
        }

        private class MarketCommand extends Command {
            public MarketCommand() { super("market", "playerservers.economy.market"); }

            @Override
            public void execute(CommandSender sender, String[] args) {
                if (!(sender instanceof ProxiedPlayer)) {
                    sender.sendMessage(new ComponentBuilder("Players only").color(ChatColor.RED).create());
                    return;
                }
                ProxiedPlayer player = (ProxiedPlayer) sender;
                if (args.length < 1) {
                    showHelp(player);
                    return;
                }
                switch (args[0].toLowerCase()) {
                    case "sell":
                        if (args.length >= 4) {
                            try {
                                double price = Double.parseDouble(args[2]);
                                int qty = Integer.parseInt(args[3]);
                                if (market.listItem(player.getUniqueId(), args[1], args[1], price, qty)) {
                                    player.sendMessage(new ComponentBuilder("Listed " + args[1] + " x" + qty + " for $" + price)
                                        .color(ChatColor.GREEN).create());
                                } else {
                                    player.sendMessage(new ComponentBuilder("Failed to list item (need $" +
                                        plugin.getConfigManager().getDouble("economy.market_listing_fee", 5.0) + " fee)")
                                        .color(ChatColor.RED).create());
                                }
                            } catch (NumberFormatException e) {
                                player.sendMessage(new ComponentBuilder("Usage: /market sell <item> <price> <quantity>")
                                    .color(ChatColor.RED).create());
                            }
                        }
                        break;
                    case "buy":
                        if (args.length >= 2) {
                            try {
                                long id = Long.parseLong(args[1]);
                                int qty = args.length >= 3 ? Integer.parseInt(args[2]) : 1;
                                if (market.buyItem(player.getUniqueId(), id, qty)) {
                                    player.sendMessage(new ComponentBuilder("Purchase successful!").color(ChatColor.GREEN).create());
                                } else {
                                    player.sendMessage(new ComponentBuilder("Purchase failed (insufficient funds or listing gone)")
                                        .color(ChatColor.RED).create());
                                }
                            } catch (NumberFormatException e) {
                                player.sendMessage(new ComponentBuilder("Invalid ID or quantity").color(ChatColor.RED).create());
                            }
                        }
                        break;
                    case "search":
                        if (args.length >= 2) {
                            List<String> results = market.searchItems(args[1]);
                            player.sendMessage(new ComponentBuilder("=== Market Search Results ===").color(ChatColor.GOLD).create());
                            for (String result : results) {
                                player.sendMessage(new ComponentBuilder("  " + result).color(ChatColor.WHITE).create());
                            }
                        }
                        break;
                    case "cancel":
                        if (args.length >= 2) {
                            try {
                                market.cancelListing(player.getUniqueId(), Long.parseLong(args[1]));
                                player.sendMessage(new ComponentBuilder("Listing cancelled").color(ChatColor.GREEN).create());
                            } catch (NumberFormatException e) {
                                player.sendMessage(new ComponentBuilder("Invalid ID").color(ChatColor.RED).create());
                            }
                        }
                        break;
                    default:
                        showHelp(player);
                }
            }

            private void showHelp(ProxiedPlayer player) {
                player.sendMessage(new ComponentBuilder("=== Market Commands ===").color(ChatColor.GOLD).create());
                player.sendMessage(new ComponentBuilder("/market sell <item> <price> <qty>").color(ChatColor.YELLOW).create());
                player.sendMessage(new ComponentBuilder("/market buy <id> [qty]").color(ChatColor.YELLOW).create());
                player.sendMessage(new ComponentBuilder("/market search <query>").color(ChatColor.YELLOW).create());
                player.sendMessage(new ComponentBuilder("/market cancel <id>").color(ChatColor.YELLOW).create());
            }
        }
    }
}
