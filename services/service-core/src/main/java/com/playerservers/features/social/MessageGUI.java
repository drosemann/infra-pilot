package com.playerservers.features.social;

import com.playerservers.PlayerServerPlugin;
import net.md_5.bungee.api.ChatColor;
import net.md_5.bungee.api.chat.ClickEvent;
import net.md_5.bungee.api.chat.ComponentBuilder;
import net.md_5.bungee.api.chat.TextComponent;
import net.md_5.bungee.api.connection.ProxiedPlayer;

import java.util.List;

public class MessageGUI {
    private final PlayerServerPlugin plugin;
    private final MessageManager messageManager;

    public MessageGUI(PlayerServerPlugin plugin, MessageManager messageManager) {
        this.plugin = plugin;
        this.messageManager = messageManager;
    }

    public void openInbox(ProxiedPlayer player) {
        List<Message> messages = messageManager.getInbox(player.getUniqueId());
        int unread = messageManager.getUnreadCount(player.getUniqueId());

        player.sendMessage(new ComponentBuilder("=== Inbox (" + unread + " unread) ===")
            .color(ChatColor.GOLD).create());

        TextComponent clear = new TextComponent("[Clear All]");
        clear.setColor(ChatColor.RED);
        clear.setClickEvent(new ClickEvent(ClickEvent.Action.RUN_COMMAND, "/msg clear"));
        player.sendMessage(clear);

        if (messages.isEmpty()) {
            player.sendMessage(new ComponentBuilder("No messages.").color(ChatColor.GRAY).create());
            return;
        }

        for (Message msg : messages) {
            ComponentBuilder line = new ComponentBuilder(msg.getSenderName())
                .color(ChatColor.YELLOW)
                .event(new ClickEvent(ClickEvent.Action.SUGGEST_COMMAND, "/msg " + msg.getSenderName() + " "));

            if (!msg.isRead()) {
                line.append(" [NEW]").color(ChatColor.GREEN);
            }

            line.append(": ").color(ChatColor.WHITE);
            line.append(msg.getMessage()).color(ChatColor.GRAY);

            player.sendMessage(line.create());
            messageManager.markAsRead(player.getUniqueId(), msg.getId());
        }
    }
}
