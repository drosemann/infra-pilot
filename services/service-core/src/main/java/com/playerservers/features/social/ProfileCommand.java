package com.playerservers.features.social;

import com.playerservers.PlayerServerPlugin;
import net.md_5.bungee.api.ChatColor;
import net.md_5.bungee.api.CommandSender;
import net.md_5.bungee.api.chat.ComponentBuilder;
import net.md_5.bungee.api.connection.ProxiedPlayer;
import net.md_5.bungee.api.plugin.Command;

import java.util.UUID;

public class ProfileCommand extends Command {
    private final PlayerServerPlugin plugin;
    private final ProfileManager profileManager;

    public ProfileCommand(PlayerServerPlugin plugin, ProfileManager profileManager) {
        super("profile", "playerservers.profile", "p");
        this.plugin = plugin;
        this.profileManager = profileManager;
    }

    @Override
    public void execute(CommandSender sender, String[] args) {
        if (!(sender instanceof ProxiedPlayer)) {
            sender.sendMessage(new ComponentBuilder("Players only!").color(ChatColor.RED).create());
            return;
        }
        ProxiedPlayer player = (ProxiedPlayer) sender;

        if (args.length == 0) {
            showProfile(player, player.getUniqueId());
            return;
        }

        if (args[0].equalsIgnoreCase("set")) {
            if (args.length < 3) {
                player.sendMessage(new ComponentBuilder("Usage: /profile set <bio|discord|website> <value>")
                    .color(ChatColor.RED).create());
                return;
            }
            String value = args[2];
            for (int i = 3; i < args.length; i++) value += " " + args[i];
            handleSet(player, args[1], value);
            return;
        }

        ProxiedPlayer target = plugin.getProxy().getPlayer(args[0]);
        if (target != null) {
            showProfile(player, target.getUniqueId());
        } else {
            player.sendMessage(new ComponentBuilder("Player not found!").color(ChatColor.RED).create());
        }
    }

    private void showProfile(ProxiedPlayer viewer, UUID targetUuid) {
        PlayerProfile profile = profileManager.getProfile(targetUuid);

        viewer.sendMessage(new ComponentBuilder("=== " + profile.getPlayerName() + "'s Profile ===")
            .color(ChatColor.GOLD).create());

        if (profile.getBio() != null && !profile.getBio().isEmpty()) {
            viewer.sendMessage(new ComponentBuilder("Bio: ").color(ChatColor.YELLOW)
                .append(profile.getBio()).color(ChatColor.WHITE).create());
        }
        viewer.sendMessage(new ComponentBuilder("Servers: ").color(ChatColor.YELLOW)
            .append(String.valueOf(profile.getServersCreated())).color(ChatColor.GREEN)
            .append(" | Friends: ").color(ChatColor.YELLOW)
            .append(String.valueOf(profile.getFriendsCount())).color(ChatColor.GREEN)
            .append(" | Reputation: ").color(ChatColor.YELLOW)
            .append(String.valueOf(profile.getReputationScore())).color(ChatColor.GREEN).create());

        if (profile.getWebsite() != null && !profile.getWebsite().isEmpty()) {
            viewer.sendMessage(new ComponentBuilder("Website: ").color(ChatColor.YELLOW)
                .append(profile.getWebsite()).color(ChatColor.BLUE).create());
        }
        if (profile.getDiscord() != null && !profile.getDiscord().isEmpty()) {
            viewer.sendMessage(new ComponentBuilder("Discord: ").color(ChatColor.YELLOW)
                .append(profile.getDiscord()).color(ChatColor.AQUA).create());
        }

        if (profile.getOwnedServers() != null && !profile.getOwnedServers().isEmpty()) {
            viewer.sendMessage(new ComponentBuilder("Owned Servers:").color(ChatColor.YELLOW).create());
            for (String server : profile.getOwnedServers()) {
                viewer.sendMessage(new ComponentBuilder(" - " + server).color(ChatColor.GREEN).create());
            }
        }

        if (profile.getFriends() != null && !profile.getFriends().isEmpty()) {
            viewer.sendMessage(new ComponentBuilder("Friends (" + profile.getFriends().size() + "):").color(ChatColor.YELLOW).create());
            int count = 0;
            for (Friend friend : profile.getFriends()) {
                if (count >= 10) {
                    viewer.sendMessage(new ComponentBuilder(" ... and " + (profile.getFriends().size() - 10) + " more")
                        .color(ChatColor.GRAY).create());
                    break;
                }
                String status = friend.isFriendOnline() ? " [ONLINE]" : "";
                viewer.sendMessage(new ComponentBuilder(" - " + friend.getFriendName())
                    .color(ChatColor.YELLOW)
                    .append(status).color(friend.isFriendOnline() ? ChatColor.GREEN : ChatColor.GRAY).create());
                count++;
            }
        }

        if (profile.getStatistics() != null) {
            viewer.sendMessage(new ComponentBuilder("Server Stats:").color(ChatColor.YELLOW).create());
            viewer.sendMessage(new ComponentBuilder(" Playtime: " + profile.getStatistics().get("totalPlaytime") + " hours")
                .color(ChatColor.GREEN).create());
        }
    }

    private void handleSet(ProxiedPlayer player, String field, String value) {
        boolean success;
        switch (field.toLowerCase()) {
            case "bio":
                success = profileManager.setBio(player.getUniqueId(), value);
                break;
            case "discord":
                success = profileManager.setDiscord(player.getUniqueId(), value);
                break;
            case "website":
                success = profileManager.setWebsite(player.getUniqueId(), value);
                break;
            default:
                player.sendMessage(new ComponentBuilder("Invalid field. Use: bio, discord, website")
                    .color(ChatColor.RED).create());
                return;
        }
        if (success) {
            player.sendMessage(new ComponentBuilder("Profile updated!").color(ChatColor.GREEN).create());
        } else {
            player.sendMessage(new ComponentBuilder("Failed to update profile (too long?).").color(ChatColor.RED).create());
        }
    }
}
