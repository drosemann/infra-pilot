package com.playerservers.features.social;

import com.playerservers.PlayerServerPlugin;
import net.md_5.bungee.api.ChatColor;
import net.md_5.bungee.api.CommandSender;
import net.md_5.bungee.api.chat.ComponentBuilder;
import net.md_5.bungee.api.connection.ProxiedPlayer;
import net.md_5.bungee.api.plugin.Command;

import java.util.UUID;

public class FriendCommand extends Command {
    private final PlayerServerPlugin plugin;
    private final FriendManager friendManager;

    public FriendCommand(PlayerServerPlugin plugin, FriendManager friendManager) {
        super("friend", "playerservers.friend", "f");
        this.plugin = plugin;
        this.friendManager = friendManager;
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
                if (args.length < 2) {
                    player.sendMessage(new ComponentBuilder("Usage: /friend add <player>").color(ChatColor.RED).create());
                    return;
                }
                handleAdd(player, args[1]);
                break;
            case "accept":
                if (args.length < 2) {
                    player.sendMessage(new ComponentBuilder("Usage: /friend accept <player>").color(ChatColor.RED).create());
                    return;
                }
                handleAccept(player, args[1]);
                break;
            case "remove":
                if (args.length < 2) {
                    player.sendMessage(new ComponentBuilder("Usage: /friend remove <player>").color(ChatColor.RED).create());
                    return;
                }
                handleRemove(player, args[1]);
                break;
            case "block":
                if (args.length < 2) {
                    player.sendMessage(new ComponentBuilder("Usage: /friend block <player>").color(ChatColor.RED).create());
                    return;
                }
                handleBlock(player, args[1]);
                break;
            case "list":
                handleList(player);
                break;
            case "pending":
                handlePending(player);
                break;
            default:
                showHelp(player);
        }
    }

    private void handleAdd(ProxiedPlayer player, String targetName) {
        ProxiedPlayer target = plugin.getProxy().getPlayer(targetName);
        if (target == null) {
            player.sendMessage(new ComponentBuilder("Player not found!").color(ChatColor.RED).create());
            return;
        }
        if (friendManager.sendFriendRequest(player.getUniqueId(), target.getUniqueId())) {
            player.sendMessage(new ComponentBuilder("Friend request sent to " + target.getName())
                .color(ChatColor.GREEN).create());
            target.sendMessage(new ComponentBuilder(player.getName() + " sent you a friend request! Use /friend accept " + player.getName())
                .color(ChatColor.YELLOW).create());
        } else {
            player.sendMessage(new ComponentBuilder("Could not send friend request. Already friends or pending.")
                .color(ChatColor.RED).create());
        }
    }

    private void handleAccept(ProxiedPlayer player, String requesterName) {
        ProxiedPlayer requester = plugin.getProxy().getPlayer(requesterName);
        if (requester == null) {
            player.sendMessage(new ComponentBuilder("Player not found!").color(ChatColor.RED).create());
            return;
        }
        if (friendManager.acceptFriendRequest(player.getUniqueId(), requester.getUniqueId())) {
            player.sendMessage(new ComponentBuilder("You are now friends with " + requester.getName())
                .color(ChatColor.GREEN).create());
            requester.sendMessage(new ComponentBuilder(player.getName() + " accepted your friend request!")
                .color(ChatColor.GREEN).create());
        } else {
            player.sendMessage(new ComponentBuilder("No pending request from that player.")
                .color(ChatColor.RED).create());
        }
    }

    private void handleRemove(ProxiedPlayer player, String friendName) {
        ProxiedPlayer target = plugin.getProxy().getPlayer(friendName);
        if (target == null) {
            player.sendMessage(new ComponentBuilder("Player not found!").color(ChatColor.RED).create());
            return;
        }
        if (friendManager.removeFriend(player.getUniqueId(), target.getUniqueId())) {
            player.sendMessage(new ComponentBuilder("Removed " + target.getName() + " from your friends.")
                .color(ChatColor.GREEN).create());
        } else {
            player.sendMessage(new ComponentBuilder("Could not remove friend.").color(ChatColor.RED).create());
        }
    }

    private void handleBlock(ProxiedPlayer player, String targetName) {
        ProxiedPlayer target = plugin.getProxy().getPlayer(targetName);
        if (target == null) {
            player.sendMessage(new ComponentBuilder("Player not found!").color(ChatColor.RED).create());
            return;
        }
        if (friendManager.blockPlayer(player.getUniqueId(), target.getUniqueId())) {
            player.sendMessage(new ComponentBuilder("Blocked " + target.getName()).color(ChatColor.GREEN).create());
        }
    }

    private void handleList(ProxiedPlayer player) {
        java.util.List<Friend> friends = friendManager.getFriends(player.getUniqueId());
        player.sendMessage(new ComponentBuilder("=== Friends (" + friends.size() + ") ===").color(ChatColor.GOLD).create());
        if (friends.isEmpty()) {
            player.sendMessage(new ComponentBuilder("You have no friends yet.").color(ChatColor.GRAY).create());
            return;
        }
        for (Friend friend : friends) {
            ChatColor statusColor = friend.isFriendOnline() ? ChatColor.GREEN : ChatColor.GRAY;
            String status = friend.isFriendOnline() ? " ONLINE" : " OFFLINE";
            player.sendMessage(new ComponentBuilder(" - " + friend.getFriendName())
                .color(ChatColor.YELLOW)
                .append(status).color(statusColor).create());
        }
    }

    private void handlePending(ProxiedPlayer player) {
        java.util.List<Friend> pending = friendManager.getPendingRequests(player.getUniqueId());
        player.sendMessage(new ComponentBuilder("=== Pending Requests ===").color(ChatColor.GOLD).create());
        if (pending.isEmpty()) {
            player.sendMessage(new ComponentBuilder("No pending requests.").color(ChatColor.GRAY).create());
            return;
        }
        for (Friend req : pending) {
            player.sendMessage(new ComponentBuilder(" - " + req.getFriendName())
                .color(ChatColor.YELLOW)
                .append(" [Accept]").color(ChatColor.GREEN)
                .create());
        }
    }

    private void showHelp(ProxiedPlayer player) {
        player.sendMessage(new ComponentBuilder("=== Friend Commands ===").color(ChatColor.GOLD).create());
        player.sendMessage(new ComponentBuilder("/friend add <player>").color(ChatColor.YELLOW)
            .append(" - Send friend request").color(ChatColor.WHITE).create());
        player.sendMessage(new ComponentBuilder("/friend accept <player>").color(ChatColor.YELLOW)
            .append(" - Accept friend request").color(ChatColor.WHITE).create());
        player.sendMessage(new ComponentBuilder("/friend remove <player>").color(ChatColor.YELLOW)
            .append(" - Remove friend").color(ChatColor.WHITE).create());
        player.sendMessage(new ComponentBuilder("/friend block <player>").color(ChatColor.YELLOW)
            .append(" - Block player").color(ChatColor.WHITE).create());
        player.sendMessage(new ComponentBuilder("/friend list").color(ChatColor.YELLOW)
            .append(" - List friends").color(ChatColor.WHITE).create());
        player.sendMessage(new ComponentBuilder("/friend pending").color(ChatColor.YELLOW)
            .append(" - Show pending requests").color(ChatColor.WHITE).create());
    }
}
