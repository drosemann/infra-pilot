package com.playerservers.features.social;

import com.playerservers.PlayerServerPlugin;
import net.md_5.bungee.api.ChatColor;
import net.md_5.bungee.api.CommandSender;
import net.md_5.bungee.api.chat.ComponentBuilder;
import net.md_5.bungee.api.connection.ProxiedPlayer;
import net.md_5.bungee.api.plugin.Command;

import java.util.List;

public class ActivityCommand extends Command {
    private final PlayerServerPlugin plugin;
    private final ActivityManager activityManager;

    public ActivityCommand(PlayerServerPlugin plugin, ActivityManager activityManager) {
        super("feed", "playerservers.feed", "activity");
        this.plugin = plugin;
        this.activityManager = activityManager;
    }

    @Override
    public void execute(CommandSender sender, String[] args) {
        if (!(sender instanceof ProxiedPlayer)) {
            sender.sendMessage(new ComponentBuilder("Players only!").color(ChatColor.RED).create());
            return;
        }
        ProxiedPlayer player = (ProxiedPlayer) sender;

        int page = 1;
        if (args.length > 0 && args[0].equalsIgnoreCase("friends")) {
            showFriendFeed(player, page);
            return;
        }
        if (args.length > 0 && args[0].equalsIgnoreCase("servers")) {
            showServerFeed(player, page);
            return;
        }
        if (args.length > 0) {
            try {
                page = Integer.parseInt(args[0]);
            } catch (NumberFormatException e) {
                showHelp(player);
                return;
            }
        }
        showGlobalFeed(player, page);
    }

    private void showGlobalFeed(ProxiedPlayer player, int page) {
        List<Activity> activities = activityManager.getActivityFeed(page, 10);
        player.sendMessage(new ComponentBuilder("=== Activity Feed (Page " + page + ") ===")
            .color(ChatColor.GOLD).create());
        if (activities.isEmpty()) {
            player.sendMessage(new ComponentBuilder("No recent activity.").color(ChatColor.GRAY).create());
            return;
        }
        for (Activity activity : activities) {
            player.sendMessage(new ComponentBuilder(" " + activity.getPlayerName())
                .color(ChatColor.YELLOW)
                .append(" " + activity.getFormattedMessage()).color(ChatColor.WHITE).create());
        }
    }

    private void showFriendFeed(ProxiedPlayer player, int page) {
        List<Activity> activities = activityManager.getFriendActivities(player.getUniqueId(), page, 10);
        player.sendMessage(new ComponentBuilder("=== Friend Activity (Page " + page + ") ===")
            .color(ChatColor.GOLD).create());
        if (activities.isEmpty()) {
            player.sendMessage(new ComponentBuilder("No friend activity yet.").color(ChatColor.GRAY).create());
            return;
        }
        for (Activity activity : activities) {
            player.sendMessage(new ComponentBuilder(" " + activity.getPlayerName())
                .color(ChatColor.YELLOW)
                .append(" " + activity.getFormattedMessage()).color(ChatColor.WHITE).create());
        }
    }

    private void showServerFeed(ProxiedPlayer player, int page) {
        List<Activity> activities = activityManager.getServerActivities(
            player.getUniqueId().toString(), page, 10);
        player.sendMessage(new ComponentBuilder("=== Server Activity ===").color(ChatColor.GOLD).create());
        if (activities.isEmpty()) {
            player.sendMessage(new ComponentBuilder("No server activity yet.").color(ChatColor.GRAY).create());
            return;
        }
        for (Activity activity : activities) {
            player.sendMessage(new ComponentBuilder(" " + activity.getFormattedMessage())
                .color(ChatColor.WHITE).create());
        }
    }

    private void showHelp(ProxiedPlayer player) {
        player.sendMessage(new ComponentBuilder("=== Activity Feed Commands ===").color(ChatColor.GOLD).create());
        player.sendMessage(new ComponentBuilder("/feed").color(ChatColor.YELLOW)
            .append(" - View global activity feed").color(ChatColor.WHITE).create());
        player.sendMessage(new ComponentBuilder("/feed friends").color(ChatColor.YELLOW)
            .append(" - View friend activities").color(ChatColor.WHITE).create());
        player.sendMessage(new ComponentBuilder("/feed servers").color(ChatColor.YELLOW)
            .append(" - View server activities").color(ChatColor.WHITE).create());
    }
}
