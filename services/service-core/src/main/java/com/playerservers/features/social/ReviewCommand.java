package com.playerservers.features.social;

import com.playerservers.PlayerServerPlugin;
import net.md_5.bungee.api.ChatColor;
import net.md_5.bungee.api.CommandSender;
import net.md_5.bungee.api.chat.ComponentBuilder;
import net.md_5.bungee.api.connection.ProxiedPlayer;
import net.md_5.bungee.api.plugin.Command;

import java.util.List;

public class ReviewCommand extends Command {
    private final PlayerServerPlugin plugin;
    private final ReviewManager reviewManager;

    public ReviewCommand(PlayerServerPlugin plugin, ReviewManager reviewManager) {
        super("rate", "playerservers.rate", "review");
        this.plugin = plugin;
        this.reviewManager = reviewManager;
    }

    @Override
    public void execute(CommandSender sender, String[] args) {
        if (!(sender instanceof ProxiedPlayer)) {
            sender.sendMessage(new ComponentBuilder("Players only!").color(ChatColor.RED).create());
            return;
        }
        ProxiedPlayer player = (ProxiedPlayer) sender;

        if (args.length == 0) {
            showHelp(player);
            return;
        }

        switch (args[0].toLowerCase()) {
            case "add":
                if (args.length < 3) {
                    player.sendMessage(new ComponentBuilder("Usage: /rate add <player> <rating> [comment]").color(ChatColor.RED).create());
                    return;
                }
                String comment = args.length >= 4 ? args[3] : "";
                for (int i = 4; i < args.length; i++) comment += " " + args[i];
                handleAdd(player, args[1], args[2], comment);
                break;
            case "list":
                if (args.length >= 2) {
                    showServerReviews(player, args[1]);
                } else {
                    showMyReviews(player);
                }
                break;
            case "my":
                showMyReviews(player);
                break;
            default:
                showHelp(player);
        }
    }

    private void handleAdd(ProxiedPlayer player, String targetName, String ratingStr, String comment) {
        ProxiedPlayer target = plugin.getProxy().getPlayer(targetName);
        if (target == null) {
            player.sendMessage(new ComponentBuilder("Player not found!").color(ChatColor.RED).create());
            return;
        }
        if (!plugin.getDatabaseManager().hasServer(target.getUniqueId().toString())) {
            player.sendMessage(new ComponentBuilder("That player doesn't have a server!").color(ChatColor.RED).create());
            return;
        }
        int rating;
        try {
            rating = Integer.parseInt(ratingStr);
        } catch (NumberFormatException e) {
            player.sendMessage(new ComponentBuilder("Rating must be a number 1-5!").color(ChatColor.RED).create());
            return;
        }
        if (reviewManager.submitReview(player.getUniqueId(), target.getUniqueId().toString(), rating, comment)) {
            player.sendMessage(new ComponentBuilder("Review submitted! Rating: " + rating + "/5")
                .color(ChatColor.GREEN).create());
        } else {
            player.sendMessage(new ComponentBuilder("Could not submit review. Already reviewed or invalid.")
                .color(ChatColor.RED).create());
        }
    }

    private void showServerReviews(ProxiedPlayer player, String targetName) {
        ProxiedPlayer target = plugin.getProxy().getPlayer(targetName);
        String ownerUuid = target != null ? target.getUniqueId().toString() : targetName;
        List<ServerReview> reviews = reviewManager.getServerReviews(ownerUuid);
        double avg = reviewManager.getAverageRating(ownerUuid);

        player.sendMessage(new ComponentBuilder("=== Reviews for " + targetName + " ===").color(ChatColor.GOLD)
            .append(" (Avg: " + String.format("%.1f", avg) + "/5)").color(ChatColor.YELLOW).create());
        if (reviews.isEmpty()) {
            player.sendMessage(new ComponentBuilder("No reviews yet.").color(ChatColor.GRAY).create());
            return;
        }
        for (ServerReview review : reviews) {
            String stars = getStars(review.getRating());
            player.sendMessage(new ComponentBuilder(" " + stars + " ").color(ChatColor.GOLD)
                .append("by " + review.getReviewerName()).color(ChatColor.YELLOW).create());
            if (review.getComment() != null && !review.getComment().isEmpty()) {
                player.sendMessage(new ComponentBuilder("  " + review.getComment()).color(ChatColor.WHITE).create());
            }
        }
    }

    private void showMyReviews(ProxiedPlayer player) {
        List<ServerReview> reviews = reviewManager.getPlayerReviews(player.getUniqueId());
        player.sendMessage(new ComponentBuilder("=== Your Reviews ===").color(ChatColor.GOLD).create());
        if (reviews.isEmpty()) {
            player.sendMessage(new ComponentBuilder("You haven't reviewed any servers yet.").color(ChatColor.GRAY).create());
            return;
        }
        for (ServerReview review : reviews) {
            String stars = getStars(review.getRating());
            player.sendMessage(new ComponentBuilder(" " + stars + " ").color(ChatColor.GOLD)
                .append(review.getReviewerName()).color(ChatColor.YELLOW).create());
        }
    }

    private String getStars(int rating) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < 5; i++) {
            sb.append(i < rating ? "\u2605" : "\u2606");
        }
        return sb.toString();
    }

    private void showHelp(ProxiedPlayer player) {
        player.sendMessage(new ComponentBuilder("=== Review Commands ===").color(ChatColor.GOLD).create());
        player.sendMessage(new ComponentBuilder("/rate add <player> <1-5> [comment]").color(ChatColor.YELLOW)
            .append(" - Rate a player's server").color(ChatColor.WHITE).create());
        player.sendMessage(new ComponentBuilder("/rate list <player>").color(ChatColor.YELLOW)
            .append(" - View server reviews").color(ChatColor.WHITE).create());
        player.sendMessage(new ComponentBuilder("/rate my").color(ChatColor.YELLOW)
            .append(" - View your reviews").color(ChatColor.WHITE).create());
    }
}
