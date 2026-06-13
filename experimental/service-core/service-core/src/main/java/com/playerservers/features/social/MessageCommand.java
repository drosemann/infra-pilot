package com.playerservers.features.social;

import com.playerservers.PlayerServerPlugin;
import net.md_5.bungee.api.ChatColor;
import net.md_5.bungee.api.CommandSender;
import net.md_5.bungee.api.chat.ComponentBuilder;
import net.md_5.bungee.api.connection.ProxiedPlayer;
import net.md_5.bungee.api.plugin.Command;

import java.util.List;
import java.util.UUID;

public class MessageCommand extends Command {
    private final PlayerServerPlugin plugin;
    private final MessageManager messageManager;
    private final java.util.Map<UUID, UUID> lastSender;

    public MessageCommand(PlayerServerPlugin plugin, MessageManager messageManager) {
        super("msg", "playerservers.msg", "tell", "whisper", "message");
        this.plugin = plugin;
        this.messageManager = messageManager;
        this.lastSender = new java.util.concurrent.ConcurrentHashMap<>();
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
            case "send":
                if (args.length < 3) {
                    player.sendMessage(new ComponentBuilder("Usage: /msg send <player> <message>").color(ChatColor.RED).create());
                    return;
                }
                String msg = args[2];
                for (int i = 3; i < args.length; i++) msg += " " + args[i];
                handleSend(player, args[1], msg);
                break;
            case "r":
            case "reply":
                if (args.length < 2) {
                    player.sendMessage(new ComponentBuilder("Usage: /msg reply <message>").color(ChatColor.RED).create());
                    return;
                }
                String reply = args[1];
                for (int i = 2; i < args.length; i++) reply += " " + args[i];
                handleReply(player, reply);
                break;
            case "inbox":
                showInbox(player);
                break;
            case "clear":
                handleClear(player);
                break;
            default:
                String message = args[1];
                for (int i = 2; i < args.length; i++) message += " " + args[i];
                handleSend(player, args[0], message);
        }
    }

    private void handleSend(ProxiedPlayer player, String targetName, String message) {
        int rateLimit = plugin.getConfigManager().getInt("social.messaging.rate_limit_per_minute", 10);
        if (messageManager.getMessageCount(player.getUniqueId()) >= rateLimit) {
            player.sendMessage(new ComponentBuilder("You're sending messages too fast!").color(ChatColor.RED).create());
            return;
        }

        ProxiedPlayer target = plugin.getProxy().getPlayer(targetName);
        if (target == null) {
            player.sendMessage(new ComponentBuilder("Player not found!").color(ChatColor.RED).create());
            return;
        }
        if (target.equals(player)) {
            player.sendMessage(new ComponentBuilder("You can't message yourself!").color(ChatColor.RED).create());
            return;
        }

        if (messageManager.sendMessage(player.getUniqueId(), target.getUniqueId(), message)) {
            player.sendMessage(new ComponentBuilder("[You -> " + target.getName() + "] " + message)
                .color(ChatColor.GRAY).create());
            target.sendMessage(new ComponentBuilder("[" + player.getName() + " -> You] " + message)
                .color(ChatColor.GRAY).create());
            lastSender.put(target.getUniqueId(), player.getUniqueId());
        } else {
            player.sendMessage(new ComponentBuilder("Could not send message (blocked or too long).")
                .color(ChatColor.RED).create());
        }
    }

    private void handleReply(ProxiedPlayer player, String message) {
        UUID last = lastSender.get(player.getUniqueId());
        if (last == null) {
            player.sendMessage(new ComponentBuilder("No one to reply to!").color(ChatColor.RED).create());
            return;
        }
        ProxiedPlayer target = plugin.getProxy().getPlayer(last);
        if (target == null) {
            player.sendMessage(new ComponentBuilder("Player is no longer online.").color(ChatColor.RED).create());
            return;
        }
        handleSend(player, target.getName(), message);
    }

    private void showInbox(ProxiedPlayer player) {
        List<Message> messages = messageManager.getInbox(player.getUniqueId());
        int unread = messageManager.getUnreadCount(player.getUniqueId());

        player.sendMessage(new ComponentBuilder("=== Inbox (" + unread + " unread) ===").color(ChatColor.GOLD).create());
        if (messages.isEmpty()) {
            player.sendMessage(new ComponentBuilder("Your inbox is empty.").color(ChatColor.GRAY).create());
            return;
        }
        for (Message msg : messages) {
            String readStatus = msg.isRead() ? "" : " [NEW]";
            player.sendMessage(new ComponentBuilder(" #" + msg.getId() + " ").color(ChatColor.YELLOW)
                .append("From: " + msg.getSenderName()).color(ChatColor.WHITE)
                .append(readStatus).color(ChatColor.GREEN)
                .append("\n  " + msg.getMessage()).color(ChatColor.GRAY).create());
            messageManager.markAsRead(player.getUniqueId(), msg.getId());
        }
    }

    private void handleClear(ProxiedPlayer player) {
        messageManager.clearInbox(player.getUniqueId());
        player.sendMessage(new ComponentBuilder("Inbox cleared!").color(ChatColor.GREEN).create());
    }

    private void showHelp(ProxiedPlayer player) {
        player.sendMessage(new ComponentBuilder("=== Message Commands ===").color(ChatColor.GOLD).create());
        player.sendMessage(new ComponentBuilder("/msg <player> <message>").color(ChatColor.YELLOW)
            .append(" - Send a private message").color(ChatColor.WHITE).create());
        player.sendMessage(new ComponentBuilder("/msg reply <message>").color(ChatColor.YELLOW)
            .append(" - Reply to last message").color(ChatColor.WHITE).create());
        player.sendMessage(new ComponentBuilder("/msg inbox").color(ChatColor.YELLOW)
            .append(" - Open inbox").color(ChatColor.WHITE).create());
        player.sendMessage(new ComponentBuilder("/msg clear").color(ChatColor.YELLOW)
            .append(" - Clear inbox").color(ChatColor.WHITE).create());
    }
}
