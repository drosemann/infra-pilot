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
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.logging.Level;

public class VoteRewardsManager {

    private final PlayerServerPlugin plugin;
    private final EconomyManager economyManager;
    private final Map<UUID, Integer> voteStreaks;
    private final AtomicInteger votePartyCount;
    private final int votePartyTarget;

    public VoteRewardsManager(PlayerServerPlugin plugin, EconomyManager economyManager) {
        this.plugin = plugin;
        this.economyManager = economyManager;
        this.voteStreaks = new ConcurrentHashMap<>();
        this.votePartyTarget = plugin.getConfigManager().getInt("vote.vote_party_target", 100);
        this.votePartyCount = new AtomicInteger(0);
        initDatabase();
    }

    private void initDatabase() {
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            conn.createStatement().execute("CREATE TABLE IF NOT EXISTS player_votes (" +
                "uuid VARCHAR(36), vote_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP, " +
                "vote_streak INT DEFAULT 0)");
            // Also create a cumulative table
            conn.createStatement().execute("CREATE TABLE IF NOT EXISTS vote_totals (" +
                "uuid VARCHAR(36) PRIMARY KEY, total_votes INT DEFAULT 0, " +
                "current_streak INT DEFAULT 0, last_vote_date DATE)");
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to init vote DB", e);
        }
    }

    public void processVote(UUID player) {
        double reward = plugin.getConfigManager().getDouble("vote.reward_amount", 10.0);
        economyManager.deposit(player, reward, "Vote reward");

        int streak = voteStreaks.merge(player, 1, (old, one) -> old + 1);
        plugin.getActivityRewardListener().handleVote(player);

        ProxiedPlayer p = plugin.getProxy().getPlayer(player);
        if (p != null) {
            p.sendMessage(new ComponentBuilder("Thanks for voting! +$" + String.format("%.2f", reward))
                .color(ChatColor.GREEN).create());
            p.sendMessage(new ComponentBuilder("Vote streak: " + streak + " days")
                .color(ChatColor.YELLOW).create());
        }

        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "INSERT INTO player_votes (uuid) VALUES (?)");
            stmt.setString(1, player.toString());
            stmt.executeUpdate();

            PreparedStatement totalStmt = conn.prepareStatement(
                "INSERT INTO vote_totals (uuid, total_votes, current_streak, last_vote_date) VALUES (?,1,1,CURRENT_DATE) " +
                "ON DUPLICATE KEY UPDATE total_votes = total_votes + 1, current_streak = current_streak + 1, last_vote_date = CURRENT_DATE");
            totalStmt.setString(1, player.toString());
            totalStmt.executeUpdate();
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to save vote", e);
        }

        if (votePartyCount.incrementAndGet() >= votePartyTarget) {
            triggerVoteParty();
        }
    }

    private void triggerVoteParty() {
        votePartyCount.set(0);
        double partyReward = plugin.getConfigManager().getDouble("vote.vote_party_reward", 50.0);
        plugin.getProxy().broadcast(new ComponentBuilder("Vote party! Everyone receives $" +
            String.format("%.2f", partyReward) + "!").color(ChatColor.GOLD).create());

        for (ProxiedPlayer player : plugin.getProxy().getPlayers()) {
            economyManager.deposit(player.getUniqueId(), partyReward, "Vote party reward");
        }
    }

    public int getVoteStreak(UUID player) { return voteStreaks.getOrDefault(player, 0); }
    public int getVotePartyCount() { return votePartyCount.get(); }

    public static class VoteCommands {
        private final PlayerServerPlugin plugin;
        private final VoteRewardsManager manager;

        public VoteCommands(PlayerServerPlugin plugin, VoteRewardsManager manager) {
            this.plugin = plugin;
            this.manager = manager;
            plugin.getProxy().getPluginManager().registerCommand(plugin, new VoteCommand());
        }

        private class VoteCommand extends Command {
            public VoteCommand() { super("vote", "playerservers.vote"); }

            @Override
            public void execute(CommandSender sender, String[] args) {
                if (!(sender instanceof ProxiedPlayer)) return;
                ProxiedPlayer player = (ProxiedPlayer) sender;
                player.sendMessage(new ComponentBuilder("=== Vote Info ===").color(ChatColor.GOLD).create());
                player.sendMessage(new ComponentBuilder("Your vote streak: ").color(ChatColor.YELLOW)
                    .append(String.valueOf(manager.getVoteStreak(player.getUniqueId()))).color(ChatColor.GREEN).create());
                player.sendMessage(new ComponentBuilder("Vote party progress: ").color(ChatColor.YELLOW)
                    .append(manager.getVotePartyCount() + " / " + 
                        plugin.getConfigManager().getInt("vote.vote_party_target", 100))
                    .color(ChatColor.GREEN).create());
            }
        }
    }
}
