package com.playerservers.features.statistics;

import com.playerservers.PlayerServerPlugin;
import net.md_5.bungee.api.ChatColor;
import net.md_5.bungee.api.CommandSender;
import net.md_5.bungee.api.chat.ComponentBuilder;
import net.md_5.bungee.api.chat.TextComponent;
import net.md_5.bungee.api.connection.ProxiedPlayer;
import net.md_5.bungee.api.plugin.Command;
import net.md_5.bungee.api.plugin.TabExecutor;

import java.text.DecimalFormat;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;

public class StatisticsCommand extends Command implements TabExecutor {
    private final PlayerServerPlugin plugin;
    private final PlayerStatistics statistics;
    private final DecimalFormat df = new DecimalFormat("#,##0.00");

    public StatisticsCommand(PlayerServerPlugin plugin, PlayerStatistics statistics) {
        super("serverstats", "playerservers.stats", "stats", "metrics");
        this.plugin = plugin;
        this.statistics = statistics;
    }

    @Override
    public void execute(CommandSender sender, String[] args) {
        if (!(sender instanceof ProxiedPlayer)) {
            sender.sendMessage(new ComponentBuilder("This command can only be used by players!")
                .color(ChatColor.RED).create());
            return;
        }

        final ProxiedPlayer player = (ProxiedPlayer) sender;
        if (args.length == 0) {
            displayOwnStats(player);
        } else if (args.length == 1) {
            if (args[0].equalsIgnoreCase("help")) {
                showHelp(player);
            } else if (args[0].equalsIgnoreCase("reset") && player.hasPermission("playerservers.stats.reset")) {
                resetStats(player);
            } else if (player.hasPermission("playerservers.stats.others")) {
                ProxiedPlayer target = plugin.getProxy().getPlayer(args[0]);
                if (target != null) {
                    displayOtherStats(player, target);
                } else {
                    player.sendMessage(new ComponentBuilder("Player not found!")
                        .color(ChatColor.RED).create());
                }
            } else {
                player.sendMessage(new ComponentBuilder("You don't have permission to view other players' stats!")
                    .color(ChatColor.RED).create());
            }
        }
    }

    private void displayOwnStats(ProxiedPlayer player) {
        Map<String, Object> summary = statistics.getServerSummary(player.getUniqueId());
        
        ComponentBuilder message = new ComponentBuilder("=== Your Server Statistics ===\n")
            .color(ChatColor.GOLD)
            .append("Status: ").color(ChatColor.YELLOW)
            .append(summary.get("currentStatus").toString()).color(ChatColor.GREEN)
            .append("\n");

        // Current metrics
        message.append("Current Players: ").color(ChatColor.YELLOW)
            .append(summary.get("currentPlayers").toString()).color(ChatColor.GREEN)
            .append("\n");

        message.append("Current TPS: ").color(ChatColor.YELLOW)
            .append(df.format(summary.get("currentTPS"))).color(ChatColor.GREEN)
            .append("\n");

        // Peak metrics
        message.append("Peak Players: ").color(ChatColor.YELLOW)
            .append(summary.get("peakPlayers").toString()).color(ChatColor.GREEN)
            .append("\n");

        message.append("Peak Memory Usage: ").color(ChatColor.YELLOW)
            .append(formatMemory((Long) summary.get("peakMemoryUsage"))).color(ChatColor.GREEN)
            .append("\n");

        message.append("Peak CPU Usage: ").color(ChatColor.YELLOW)
            .append(df.format(summary.get("peakCpuUsage")) + "%").color(ChatColor.GREEN)
            .append("\n");

        // General stats
        message.append("Total Playtime: ").color(ChatColor.YELLOW)
            .append(formatTime((Long) summary.get("totalPlaytime"))).color(ChatColor.GREEN)
            .append("\n");

        message.append("Uptime: ").color(ChatColor.YELLOW)
            .append(df.format(summary.get("uptime")) + "%").color(ChatColor.GREEN);

        player.sendMessage(message.create());
    }

    private void displayOtherStats(ProxiedPlayer viewer, ProxiedPlayer target) {
        Map<String, Object> summary = statistics.getServerSummary(target.getUniqueId());
        
        ComponentBuilder message = new ComponentBuilder("=== " + target.getName() + "'s Server Statistics ===\n")
            .color(ChatColor.GOLD)
            .append("Status: ").color(ChatColor.YELLOW)
            .append(summary.get("currentStatus").toString()).color(ChatColor.GREEN)
            .append("\n");

        // Only show basic stats for other players
        message.append("Current Players: ").color(ChatColor.YELLOW)
            .append(summary.get("currentPlayers").toString()).color(ChatColor.GREEN)
            .append("\n");

        message.append("Peak Players: ").color(ChatColor.YELLOW)
            .append(summary.get("peakPlayers").toString()).color(ChatColor.GREEN)
            .append("\n");

        message.append("Uptime: ").color(ChatColor.YELLOW)
            .append(df.format(summary.get("uptime")) + "%").color(ChatColor.GREEN);

        viewer.sendMessage(message.create());
    }

    private void resetStats(ProxiedPlayer player) {
        PlayerStats stats = statistics.getPlayerStats(player.getUniqueId());
        stats.resetStats();
        statistics.updateStatistics(player.getUniqueId(), stats);
        
        player.sendMessage(new ComponentBuilder("Your server statistics have been reset!")
            .color(ChatColor.GREEN).create());
    }

    private void showHelp(ProxiedPlayer player) {
        ComponentBuilder help = new ComponentBuilder("=== Server Statistics Commands ===\n")
            .color(ChatColor.GOLD);

        help.append("/serverstats").color(ChatColor.YELLOW)
            .append(" - View your server statistics\n").color(ChatColor.WHITE);

        if (player.hasPermission("playerservers.stats.others")) {
            help.append("/serverstats <player>").color(ChatColor.YELLOW)
                .append(" - View another player's server statistics\n").color(ChatColor.WHITE);
        }

        if (player.hasPermission("playerservers.stats.reset")) {
            help.append("/serverstats reset").color(ChatColor.YELLOW)
                .append(" - Reset your server statistics\n").color(ChatColor.WHITE);
        }

        help.append("/serverstats help").color(ChatColor.YELLOW)
            .append(" - Show this help message").color(ChatColor.WHITE);

        player.sendMessage(help.create());
    }

    private String formatMemory(long bytes) {
        if (bytes < 1024) return bytes + " B";
        int exp = (int) (Math.log(bytes) / Math.log(1024));
        String pre = "KMGTPE".charAt(exp-1) + "";
        return String.format("%.1f %sB", bytes / Math.pow(1024, exp), pre);
    }

    private String formatTime(long hours) {
        long days = hours / 24;
        hours = hours % 24;
        
        if (days > 0) {
            return String.format("%d days, %d hours", days, hours);
        } else {
            return String.format("%d hours", hours);
        }
    }

    @Override
    public Iterable<String> onTabComplete(CommandSender sender, String[] args) {
        List<String> completions = new ArrayList<>();
        
        if (args.length == 1) {
            if (sender.hasPermission("playerservers.stats.others")) {
                String search = args[0].toLowerCase();
                for (ProxiedPlayer player : plugin.getProxy().getPlayers()) {
                    if (player.getName().toLowerCase().startsWith(search)) {
                        completions.add(player.getName());
                    }
                }
            }
            
            if ("help".startsWith(args[0].toLowerCase())) {
                completions.add("help");
            }
            
            if (sender.hasPermission("playerservers.stats.reset") && 
                "reset".startsWith(args[0].toLowerCase())) {
                completions.add("reset");
            }
        }
        
        return completions;
    }
}