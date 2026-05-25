package com.playerservers.features.server;

import com.playerservers.PlayerServerPlugin;
import net.md_5.bungee.api.ChatColor;
import net.md_5.bungee.api.CommandSender;
import net.md_5.bungee.api.chat.ComponentBuilder;
import net.md_5.bungee.api.config.ServerInfo;
import net.md_5.bungee.api.connection.ProxiedPlayer;
import net.md_5.bungee.api.event.ServerConnectEvent;
import net.md_5.bungee.api.plugin.Command;
import net.md_5.bungee.api.plugin.Listener;
import net.md_5.bungee.event.EventHandler;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;

public class ResourceLimitsManager implements Listener {

    private final PlayerServerPlugin plugin;
    private final AtomicInteger maxEntitiesPerServer;
    private final AtomicInteger maxPlayersPerServer;
    private final AtomicInteger maxChunksPerServer;
    private final Map<String, AtomicInteger> serverCounts;

    public ResourceLimitsManager(PlayerServerPlugin plugin) {
        this.plugin = plugin;
        this.maxEntitiesPerServer = new AtomicInteger(plugin.getConfigManager().getInt("limits.max_entities_per_server", 200));
        this.maxPlayersPerServer = new AtomicInteger(plugin.getConfigManager().getInt("limits.max_players_per_server", 20));
        this.maxChunksPerServer = new AtomicInteger(plugin.getConfigManager().getInt("limits.max_chunks_per_server", 400));
        this.serverCounts = new ConcurrentHashMap<>();
    }

    @EventHandler
    public void onServerConnect(ServerConnectEvent event) {
        String target = event.getTarget().getName();
        int currentPlayers = event.getTarget().getPlayers().size();
        if (currentPlayers >= maxPlayersPerServer.get()) {
            if (!event.getPlayer().hasPermission("playerservers.limits.bypass")) {
                event.setCancelled(true);
                event.getPlayer().sendMessage(new ComponentBuilder("Server is full (max " +
                    maxPlayersPerServer.get() + " players)").color(ChatColor.RED).create());
            }
        }
    }

    public void setMaxEntities(int count) { maxEntitiesPerServer.set(count); }
    public void setMaxPlayers(int count) { maxPlayersPerServer.set(count); }
    public void setMaxChunks(int count) { maxChunksPerServer.set(count); }
    public int getMaxEntities() { return maxEntitiesPerServer.get(); }
    public int getMaxPlayers() { return maxPlayersPerServer.get(); }
    public int getMaxChunks() { return maxChunksPerServer.get(); }

    public boolean canAddEntity(String serverName) {
        AtomicInteger count = serverCounts.computeIfAbsent(serverName, k -> new AtomicInteger(0));
        return count.incrementAndGet() <= maxEntitiesPerServer.get();
    }

    public void removeEntity(String serverName) {
        AtomicInteger count = serverCounts.get(serverName);
        if (count != null) count.decrementAndGet();
    }

    public static class LimitCommands {
        private final PlayerServerPlugin plugin;
        private final ResourceLimitsManager manager;

        public LimitCommands(PlayerServerPlugin plugin, ResourceLimitsManager manager) {
            this.plugin = plugin;
            this.manager = manager;
            plugin.getProxy().getPluginManager().registerCommand(plugin, new LimitCommand());
        }

        private class LimitCommand extends Command {
            public LimitCommand() { super("limits", "playerservers.limits"); }

            @Override
            public void execute(CommandSender sender, String[] args) {
                if (args.length >= 2) {
                    try {
                        int value = Integer.parseInt(args[1]);
                        switch (args[0].toLowerCase()) {
                            case "entities": manager.setMaxEntities(value);
                                sender.sendMessage(new ComponentBuilder("Max entities set to " + value).color(ChatColor.GREEN).create());
                                return;
                            case "players": manager.setMaxPlayers(value);
                                sender.sendMessage(new ComponentBuilder("Max players set to " + value).color(ChatColor.GREEN).create());
                                return;
                            case "chunks": manager.setMaxChunks(value);
                                sender.sendMessage(new ComponentBuilder("Max chunks set to " + value).color(ChatColor.GREEN).create());
                                return;
                        }
                    } catch (NumberFormatException e) {}
                }
                sender.sendMessage(new ComponentBuilder("Usage: /limits <entities|players|chunks> <value>")
                    .color(ChatColor.RED).create());
                sender.sendMessage(new ComponentBuilder("Current: entities=" + manager.getMaxEntities() +
                    " players=" + manager.getMaxPlayers() + " chunks=" + manager.getMaxChunks())
                    .color(ChatColor.YELLOW).create());
            }
        }
    }
}
