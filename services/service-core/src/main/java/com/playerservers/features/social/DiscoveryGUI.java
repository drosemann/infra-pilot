package com.playerservers.features.social;

import com.playerservers.PlayerServerPlugin;
import net.md_5.bungee.api.ChatColor;
import net.md_5.bungee.api.chat.ClickEvent;
import net.md_5.bungee.api.chat.ComponentBuilder;
import net.md_5.bungee.api.chat.TextComponent;
import net.md_5.bungee.api.connection.ProxiedPlayer;

import java.util.List;

public class DiscoveryGUI {
    private final PlayerServerPlugin plugin;
    private final ServerDiscoveryManager discoveryManager;

    public DiscoveryGUI(PlayerServerPlugin plugin, ServerDiscoveryManager discoveryManager) {
        this.plugin = plugin;
        this.discoveryManager = discoveryManager;
    }

    public void openBrowser(ProxiedPlayer player, int page) {
        int pageSize = plugin.getConfigManager().getInt("social.discovery.max_servers_per_page", 20);
        List<ServerListing> listings = discoveryManager.getPublicServers(page, pageSize);
        int total = discoveryManager.getPublicServerCount();
        int totalPages = Math.max(1, (int) Math.ceil((double) total / pageSize));

        player.sendMessage(new ComponentBuilder("=== Server Browser (Page " + page + "/" + totalPages + ") ===")
            .color(ChatColor.GOLD).create());

        TextComponent search = new TextComponent("[Search] ");
        search.setColor(ChatColor.AQUA);
        search.setClickEvent(new ClickEvent(ClickEvent.Action.SUGGEST_COMMAND, "/browse search "));

        TextComponent top = new TextComponent("[Top Rated] ");
        top.setColor(ChatColor.GOLD);
        top.setClickEvent(new ClickEvent(ClickEvent.Action.RUN_COMMAND, "/browse top"));

        TextComponent newest = new TextComponent("[Newest]");
        newest.setColor(ChatColor.GREEN);
        newest.setClickEvent(new ClickEvent(ClickEvent.Action.RUN_COMMAND, "/browse new"));

        player.sendMessage(search, top, newest);
        player.sendMessage(new ComponentBuilder("---").color(ChatColor.GRAY).create());

        if (listings.isEmpty()) {
            player.sendMessage(new ComponentBuilder("No public servers available.").color(ChatColor.GRAY).create());
            return;
        }

        for (ServerListing listing : listings) {
            ComponentBuilder entry = new ComponentBuilder("[" + listing.getOwnerName() + "'s Server]")
                .color(ChatColor.YELLOW)
                .event(new ClickEvent(ClickEvent.Action.RUN_COMMAND, "/server join " + listing.getPlayerUuid()));

            TextComponent info = new TextComponent(" " + listing.getPlayerCount() + "/" + listing.getMaxPlayers() + " players");
            info.setColor(ChatColor.GREEN);

            TextComponent rating = new TextComponent(" \u2605" + String.format("%.1f", listing.getAverageRating()));
            rating.setColor(ChatColor.GOLD);

            player.sendMessage(entry.append("").append(info).append(rating));
        }

        if (page < totalPages) {
            TextComponent next = new TextComponent("[Next Page]");
            next.setColor(ChatColor.AQUA);
            next.setClickEvent(new ClickEvent(ClickEvent.Action.RUN_COMMAND, "/browse " + (page + 1)));
            player.sendMessage(next);
        }
    }

    public void openSearch(ProxiedPlayer player, String query, int page) {
        int pageSize = plugin.getConfigManager().getInt("social.discovery.max_servers_per_page", 20);
        List<ServerListing> listings = discoveryManager.searchServers(query, page, pageSize);

        player.sendMessage(new ComponentBuilder("=== Search: '" + query + "' ===").color(ChatColor.GOLD).create());
        if (listings.isEmpty()) {
            player.sendMessage(new ComponentBuilder("No results found.").color(ChatColor.GRAY).create());
            return;
        }
        for (ServerListing listing : listings) {
            TextComponent entry = new TextComponent("[" + listing.getServerName() + "]");
            entry.setColor(ChatColor.YELLOW);
            entry.setClickEvent(new ClickEvent(ClickEvent.Action.RUN_COMMAND, "/server join " + listing.getPlayerUuid()));

            TextComponent info = new TextComponent(" by " + listing.getOwnerName() + " - " + listing.getPlayerCount() + " players");
            info.setColor(ChatColor.WHITE);

            player.sendMessage(entry, info);
        }
    }
}
