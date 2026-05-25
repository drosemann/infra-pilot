package com.playerservers.features.community;

import com.playerservers.PlayerServerPlugin;
import com.playerservers.features.economy.EconomyManager;
import net.md_5.bungee.api.ChatColor;
import net.md_5.bungee.api.CommandSender;
import net.md_5.bungee.api.chat.ComponentBuilder;
import net.md_5.bungee.api.connection.ProxiedPlayer;
import net.md_5.bungee.api.plugin.Command;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.logging.Level;

public class ReferralManager {

    private final PlayerServerPlugin plugin;
    private final EconomyManager economyManager;
    private final Map<String, UUID> referralCodes;
    private final Map<UUID, Integer> referralCounts;

    public ReferralManager(PlayerServerPlugin plugin, EconomyManager economyManager) {
        this.plugin = plugin;
        this.economyManager = economyManager;
        this.referralCodes = new ConcurrentHashMap<>();
        this.referralCounts = new ConcurrentHashMap<>();
        initDatabase();
    }

    private void initDatabase() {
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            conn.createStatement().execute("CREATE TABLE IF NOT EXISTS referrals (" +
                "referral_code VARCHAR(16) PRIMARY KEY," +
                "owner_uuid VARCHAR(36) NOT NULL," +
                "total_referrals INT DEFAULT 0" +
                ")");
            conn.createStatement().execute("CREATE TABLE IF NOT EXISTS referral_redemptions (" +
                "redeemer_uuid VARCHAR(36) PRIMARY KEY," +
                "referral_code VARCHAR(16)," +
                "redeemed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP" +
                ")");
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to init referral DB", e);
        }
    }

    public boolean createCode(ProxiedPlayer owner, String code) {
        if (referralCodes.containsKey(code)) return false;
        referralCodes.put(code, owner.getUniqueId());
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "INSERT INTO referrals (referral_code, owner_uuid) VALUES (?,?)");
            stmt.setString(1, code);
            stmt.setString(2, owner.getUniqueId().toString());
            stmt.executeUpdate();
            return true;
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to create referral code", e);
            return false;
        }
    }

    public boolean redeemCode(ProxiedPlayer redeemer, String code) {
        if (!referralCodes.containsKey(code)) return false;

        UUID owner = referralCodes.get(code);
        if (owner.equals(redeemer.getUniqueId())) return false;

        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement check = conn.prepareStatement(
                "SELECT COUNT(*) FROM referral_redemptions WHERE redeemer_uuid = ?");
            check.setString(1, redeemer.getUniqueId().toString());
            ResultSet rs = check.executeQuery();
            if (rs.next() && rs.getInt(1) > 0) return false;
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to check redemption", e);
            return false;
        }

        double referrerReward = plugin.getConfigManager().getDouble("referral.referrer_reward", 25.0);
        double redeemerReward = plugin.getConfigManager().getDouble("referral.redeemer_reward", 10.0);

        economyManager.deposit(owner, referrerReward, "Referral reward for code: " + code);
        economyManager.deposit(redeemer.getUniqueId(), redeemerReward, "Referral code redemption: " + code);

        referralCounts.merge(owner, 1, Integer::sum);

        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "INSERT INTO referral_redemptions (redeemer_uuid, referral_code) VALUES (?,?)");
            stmt.setString(1, redeemer.getUniqueId().toString());
            stmt.setString(2, code);
            stmt.executeUpdate();

            PreparedStatement upd = conn.prepareStatement(
                "UPDATE referrals SET total_referrals = total_referrals + 1 WHERE referral_code = ?");
            upd.setString(1, code);
            upd.executeUpdate();
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to save redemption", e);
        }

        ProxiedPlayer referrer = plugin.getProxy().getPlayer(owner);
        if (referrer != null) {
            referrer.sendMessage(new ComponentBuilder(redeemer.getName() + " used your referral code! +$" +
                String.format("%.2f", referrerReward)).color(ChatColor.GREEN).create());
        }
        return true;
    }

    public int getReferralCount(UUID player) { return referralCounts.getOrDefault(player, 0); }

    public static class ReferralCommands {
        private final PlayerServerPlugin plugin;
        private final ReferralManager manager;

        public ReferralCommands(PlayerServerPlugin plugin, ReferralManager manager) {
            this.plugin = plugin;
            this.manager = manager;
            plugin.getProxy().getPluginManager().registerCommand(plugin, new ReferralCommand());
        }

        private class ReferralCommand extends Command {
            public ReferralCommand() { super("referral", "playerservers.referral", "ref"); }

            @Override
            public void execute(CommandSender sender, String[] args) {
                if (!(sender instanceof ProxiedPlayer)) return;
                ProxiedPlayer player = (ProxiedPlayer) sender;

                if (args.length == 0) {
                    player.sendMessage(new ComponentBuilder("=== Referrals ===").color(ChatColor.GOLD).create());
                    player.sendMessage(new ComponentBuilder("/referral create <code>").color(ChatColor.YELLOW)
                        .append(" - Create your referral code").color(ChatColor.WHITE).create());
                    player.sendMessage(new ComponentBuilder("/referral redeem <code>").color(ChatColor.YELLOW)
                        .append(" - Redeem a referral code").color(ChatColor.WHITE).create());
                    player.sendMessage(new ComponentBuilder("/referral count").color(ChatColor.YELLOW)
                        .append(" - Check your referrals").color(ChatColor.WHITE).create());
                    return;
                }

                switch (args[0].toLowerCase()) {
                    case "create":
                        if (args.length >= 2) {
                            if (manager.createCode(player, args[1])) {
                                player.sendMessage(new ComponentBuilder("Referral code created: " + args[1])
                                    .color(ChatColor.GREEN).create());
                            } else {
                                player.sendMessage(new ComponentBuilder("Code already taken or error creating")
                                    .color(ChatColor.RED).create());
                            }
                        }
                        break;
                    case "redeem":
                        if (args.length >= 2) {
                            if (manager.redeemCode(player, args[1])) {
                                player.sendMessage(new ComponentBuilder("Referral code redeemed! Welcome!")
                                    .color(ChatColor.GREEN).create());
                            } else {
                                player.sendMessage(new ComponentBuilder("Invalid code or already redeemed")
                                    .color(ChatColor.RED).create());
                            }
                        }
                        break;
                    case "count":
                        player.sendMessage(new ComponentBuilder("You have referred ")
                            .color(ChatColor.YELLOW)
                            .append(String.valueOf(manager.getReferralCount(player.getUniqueId())))
                            .color(ChatColor.GREEN)
                            .append(" players").color(ChatColor.YELLOW).create());
                        break;
                }
            }
        }
    }
}
