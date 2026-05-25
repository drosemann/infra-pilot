package com.playerservers;

import net.md_5.bungee.api.ChatColor;
import net.md_5.bungee.api.chat.ComponentBuilder;
import net.md_5.bungee.api.chat.ClickEvent;
import net.md_5.bungee.api.chat.TextComponent;
import net.md_5.bungee.api.connection.ProxiedPlayer;

public class GUIManager {

    private final PlayerServerPlugin plugin;

    public GUIManager(PlayerServerPlugin plugin) {
        this.plugin = plugin;
    }

    public void openMainMenu(ProxiedPlayer player) {
        player.sendMessage(new ComponentBuilder("=== Server Management ===").color(ChatColor.GOLD).create());

        TextComponent start = new TextComponent("[Start] ");
        start.setColor(ChatColor.GREEN);
        start.setClickEvent(new ClickEvent(ClickEvent.Action.RUN_COMMAND, "/server join"));

        TextComponent stop = new TextComponent("[Stop] ");
        stop.setColor(ChatColor.RED);
        stop.setClickEvent(new ClickEvent(ClickEvent.Action.RUN_COMMAND, "/server delete"));

        TextComponent info = new TextComponent("[Info]");
        info.setColor(ChatColor.YELLOW);
        info.setClickEvent(new ClickEvent(ClickEvent.Action.RUN_COMMAND, "/server list"));

        player.sendMessage(start, stop, info);
    }
}
