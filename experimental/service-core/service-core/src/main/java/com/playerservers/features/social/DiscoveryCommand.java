package com.playerservers.features.social;

import com.playerservers.PlayerServerPlugin;
import net.md_5.bungee.api.ChatColor;
import net.md_5.bungee.api.CommandSender;
import net.md_5.bungee.api.chat.ComponentBuilder;
import net.md_5.bungee.api.connection.ProxiedPlayer;
import net.md_5.bungee.api.plugin.Command;

import java.util.List;

public class DiscoveryCommand extends Command {
    private final PlayerServerPlugin plugin;
    private final ServerDiscoveryManager discoveryManager;

    public DiscoveryCommand(PlayerServerPlugin plugin, ServerDiscoveryManager discoveryManager) {
        super("browse", "playerservers.browse", "servers");
        this.plugin = plugin;
        this.discoveryManager = discoveryManager;
    }

    @Override
    public void execute(CommandSender sender, String[] args) {
        if (!(sender instanceof ProxiedPlayer)) {
            sender.sendMessage(new ComponentBuilder("Players only!").color(ChatColor.RED).create());
            return;
        }
        ProxiedPlayer player = (ProxiedPlayer) sender;

        if (args.length == 0) {
            showBrowse(player, 1);
            return;
        }

        switch (args[0].toLowerCase()) {
            case "search":
                if (args.length < 2) {
                    player.sendMessage(new ComponentBuilder("Usage: /browse search <query>").color(ChatColor.RED).create());
                    return;
                }
                String query = args[1];
                for (int i = 2; i < args.length; i++) query += " " + args[i];
                showSearch(player, query, 1);
                break;
            case "tag":
                if (args.length < 2) {
                    player.sendMessage(new ComponentBuilder("Usage: /browse tag <tag>").color(ChatColor.RED).create());
                    return;
                }
                showTagFilter(player, args[1], 1);
                break;
            case "top":
                showTopRated(player, 1);
                break;
            case "new":
                showNewest(player, 1);
                break;
            default:
                try {
                    int page = Integer.parseInt(args[0]);
                    showBrowse(player, page);
                } catch (NumberFormatException e) {
                    showHelp(player);
                }
        }
    }

    private void showBrowse(ProxiedPlayer player, int page) {
        int pageSize = plugin.getConfigManager().getInt("social.discovery.max_servers_per_page", 20);
        List<ServerListing> listings = discoveryManager.getPublicServers(page, pageSize);
        int total = discoveryManager.getPublicServerCount();
        int totalPages = Math.max(1, (int) Math.ceil((double) total / pageSize));

        player.sendMessage(new ComponentBuilder("=== Public Servers (Page " + page + "/" + totalPages + ") ===")
            .color(ChatColor.GOLD).create());
        if (listings.isEmpty()) {
            player.sendMessage(new ComponentBuilder("No public servers found.").color(ChatColor.GRAY).create());
            return;
        }
        for (ServerListing listing : listings) {
            String tags = listing.getTags() != null && !listing.getTags().isEmpty()
                ? " [" + String.join(", ", listing.getTags()) + "]" : "";
            player.sendMessage(new ComponentBuilder(" - " + listing.getServerName())
                .color(ChatColor.YELLOW)
                .append(" | Owner: " + listing.getOwnerName()).color(ChatColor.WHITE)
                .append(" | Players: " + listing.getPlayerCount() + "/" + listing.getMaxPlayers()).color(ChatColor.GREEN)
                .append(" | Rating: " + String.format("%.1f", listing.getAverageRating())).color(ChatColor.GOLD)
                .append(tags).color(ChatColor.GRAY).create());
        }
        if (page < totalPages) {
            player.sendMessage(new ComponentBuilder("Next page: /browse " + (page + 1))
                .color(ChatColor.AQUA).create());
        }
    }

    private void showSearch(ProxiedPlayer player, String query, int page) {
        int pageSize = plugin.getConfigManager().getInt("social.discovery.max_servers_per_page", 20);
        List<ServerListing> listings = discoveryManager.searchServers(query, page, pageSize);
        player.sendMessage(new ComponentBuilder("=== Search Results: '" + query + "' ===")
            .color(ChatColor.GOLD).create());
        if (listings.isEmpty()) {
            player.sendMessage(new ComponentBuilder("No results found.").color(ChatColor.GRAY).create());
            return;
        }
        for (ServerListing listing : listings) {
            player.sendMessage(new ComponentBuilder(" - " + listing.getServerName())
                .color(ChatColor.YELLOW)
                .append(" | " + listing.getOwnerName()).color(ChatColor.WHITE)
                .append(" | " + listing.getPlayerCount() + "/" + listing.getMaxPlayers() + " players")
                .color(ChatColor.GREEN).create());
        }
    }

    private void showTagFilter(ProxiedPlayer player, String tag, int page) {
        int pageSize = plugin.getConfigManager().getInt("social.discovery.max_servers_per_page", 20);
        List<ServerListing> listings = discoveryManager.getServersByTag(tag, page, pageSize);
        player.sendMessage(new ComponentBuilder("=== Servers tagged '" + tag + "' ===")
            .color(ChatColor.GOLD).create());
        if (listings.isEmpty()) {
            player.sendMessage(new ComponentBuilder("No servers found with that tag.").color(ChatColor.GRAY).create());
            return;
        }
        for (ServerListing listing : listings) {
            player.sendMessage(new ComponentBuilder(" - " + listing.getServerName())
                .color(ChatColor.YELLOW)
                .append(" | " + listing.getOwnerName()).color(ChatColor.WHITE)
                .append(" | Players: " + listing.getPlayerCount() + "/" + listing.getMaxPlayers())
                .color(ChatColor.GREEN).create());
        }
    }

    private void showTopRated(ProxiedPlayer player, int page) {
        int pageSize = plugin.getConfigManager().getInt("social.discovery.max_servers_per_page", 20);
        List<ServerListing> listings = discoveryManager.getTopRatedServers(page, pageSize);
        player.sendMessage(new ComponentBuilder("=== Top Rated Servers ===").color(ChatColor.GOLD).create());
        if (listings.isEmpty()) {
            player.sendMessage(new ComponentBuilder("No servers found.").color(ChatColor.GRAY).create());
            return;
        }
        int rank = 1 + (page - 1) * pageSize;
        for (ServerListing listing : listings) {
            player.sendMessage(new ComponentBuilder(" #" + rank + " " + listing.getServerName())
                .color(ChatColor.YELLOW)
                .append(" | Rating: " + String.format("%.1f", listing.getAverageRating())).color(ChatColor.GOLD)
                .append(" | Reviews: " + listing.getReviewCount()).color(ChatColor.GRAY).create());
            rank++;
        }
    }

    private void showNewest(ProxiedPlayer player, int page) {
        int pageSize = plugin.getConfigManager().getInt("social.discovery.max_servers_per_page", 20);
        List<ServerListing> listings = discoveryManager.getNewestServers(page, pageSize);
        player.sendMessage(new ComponentBuilder("=== Newest Servers ===").color(ChatColor.GOLD).create());
        if (listings.isEmpty()) {
            player.sendMessage(new ComponentBuilder("No servers found.").color(ChatColor.GRAY).create());
            return;
        }
        for (ServerListing listing : listings) {
            player.sendMessage(new ComponentBuilder(" - " + listing.getServerName())
                .color(ChatColor.YELLOW)
                .append(" | " + listing.getOwnerName()).color(ChatColor.WHITE)
                .append(" | Created: " + listing.getLastUpdated()).color(ChatColor.GRAY).create());
        }
    }

    private void showHelp(ProxiedPlayer player) {
        player.sendMessage(new ComponentBuilder("=== Browse Commands ===").color(ChatColor.GOLD).create());
        player.sendMessage(new ComponentBuilder("/browse").color(ChatColor.YELLOW)
            .append(" - Open server browser").color(ChatColor.WHITE).create());
        player.sendMessage(new ComponentBuilder("/browse search <query>").color(ChatColor.YELLOW)
            .append(" - Search servers").color(ChatColor.WHITE).create());
        player.sendMessage(new ComponentBuilder("/browse tag <tag>").color(ChatColor.YELLOW)
            .append(" - Filter by tag").color(ChatColor.WHITE).create());
        player.sendMessage(new ComponentBuilder("/browse top").color(ChatColor.YELLOW)
            .append(" - Show top rated servers").color(ChatColor.WHITE).create());
        player.sendMessage(new ComponentBuilder("/browse new").color(ChatColor.YELLOW)
            .append(" - Show newest servers").color(ChatColor.WHITE).create());
    }
}
