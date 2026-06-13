package com.playerservers.features.social;

import com.playerservers.PlayerServerPlugin;
import net.md_5.bungee.api.ChatColor;
import net.md_5.bungee.api.chat.ClickEvent;
import net.md_5.bungee.api.chat.ComponentBuilder;
import net.md_5.bungee.api.chat.TextComponent;
import net.md_5.bungee.api.connection.ProxiedPlayer;

import java.util.List;

public class ActivityGUI {
    private final PlayerServerPlugin plugin;
    private final ActivityManager activityManager;

    public ActivityGUI(PlayerServerPlugin plugin, ActivityManager activityManager) {
        this.plugin = plugin;
        this.activityManager = activityManager;
    }

    public void openFeed(ProxiedPlayer player, int page) {
        List<Activity> activities = activityManager.getActivityFeed(page, 10);

        player.sendMessage(new ComponentBuilder("=== Activity Feed ===").color(ChatColor.GOLD).create());

        TextComponent friends = new TextComponent("[Friends] ");
        friends.setColor(ChatColor.GREEN);
        friends.setClickEvent(new ClickEvent(ClickEvent.Action.RUN_COMMAND, "/feed friends"));

        TextComponent servers = new TextComponent("[My Server]");
        servers.setColor(ChatColor.YELLOW);
        servers.setClickEvent(new ClickEvent(ClickEvent.Action.RUN_COMMAND, "/feed servers"));

        player.sendMessage(friends, servers);

        if (activities.isEmpty()) {
            player.sendMessage(new ComponentBuilder("No activity yet.").color(ChatColor.GRAY).create());
            return;
        }

        for (Activity activity : activities) {
            TextComponent name = new TextComponent(" " + activity.getPlayerName());
            name.setColor(ChatColor.YELLOW);

            TextComponent action = new TextComponent(" " + activity.getFormattedMessage());
            action.setColor(ChatColor.WHITE);

            player.sendMessage(name, action);
        }

        if (page > 1) {
            TextComponent prev = new TextComponent("[Previous Page]");
            prev.setColor(ChatColor.AQUA);
            prev.setClickEvent(new ClickEvent(ClickEvent.Action.RUN_COMMAND, "/feed " + (page - 1)));
            player.sendMessage(prev);
        }

        if (activities.size() >= 10) {
            TextComponent next = new TextComponent("[Next Page]");
            next.setColor(ChatColor.AQUA);
            next.setClickEvent(new ClickEvent(ClickEvent.Action.RUN_COMMAND, "/feed " + (page + 1)));
            player.sendMessage(next);
        }
    }
}
