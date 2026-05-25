package com.playerservers;

import net.md_5.bungee.api.chat.TextComponent;
import net.md_5.bungee.api.config.ServerInfo;
import net.md_5.bungee.api.connection.ProxiedPlayer;
import net.md_5.bungee.api.event.ServerConnectedEvent;
import net.md_5.bungee.api.event.ServerDisconnectEvent;
import net.md_5.bungee.api.plugin.Listener;
import net.md_5.bungee.event.EventHandler;

import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.TimeUnit;

public class InactivityShutdownTask implements Listener, Runnable {

    private final PlayerServerPlugin plugin;
    private final Map<String, Long> lastActivity;
    private final long timeoutMillis;

    public InactivityShutdownTask(PlayerServerPlugin plugin) {
        this.plugin = plugin;
        this.lastActivity = new ConcurrentHashMap<>();
        this.timeoutMillis = TimeUnit.MINUTES.toMillis(
            plugin.getConfigManager().getLong("server_limits.inactivity_shutdown_minutes", 30));
        plugin.getProxy().getScheduler().schedule(plugin, this, 1, 1, TimeUnit.MINUTES);
    }

    @Override
    public void run() {
        long now = System.currentTimeMillis();
        for (Map.Entry<String, Long> entry : lastActivity.entrySet()) {
            String serverName = entry.getKey();
            long inactiveFor = now - entry.getValue();

            ServerInfo serverInfo = plugin.getProxy().getServerInfo(serverName);
            if (serverInfo == null) continue;

            boolean hasPlayers = !serverInfo.getPlayers().isEmpty();

            if (hasPlayers) {
                lastActivity.put(serverName, now);
                continue;
            }

            if (!hasPlayers && inactiveFor >= timeoutMillis) {
                plugin.getLogger().info("Shutting down inactive server: " + serverName +
                    " (inactive for " + TimeUnit.MILLISECONDS.toMinutes(inactiveFor) + " min)");
                UUID ownerUUID = findOwner(serverName);
                if (ownerUUID != null) {
                    plugin.getServerManager().stopServer(ownerUUID);
                }
                lastActivity.remove(serverName);
            } else if (!hasPlayers && inactiveFor >= timeoutMillis - TimeUnit.MINUTES.toMillis(5)) {
                for (ProxiedPlayer player : plugin.getProxy().getPlayers()) {
                    if (player.getServer() != null && serverName.equals(player.getServer().getInfo().getName())) {
                        player.sendMessage(new TextComponent("§e[Warning] Your server will shut down due to inactivity in 5 minutes."));
                    }
                }
            }
        }
    }

    @EventHandler
    public void onServerConnected(ServerConnectedEvent event) {
        String serverName = event.getServer().getInfo().getName();
        lastActivity.put(serverName, System.currentTimeMillis());
    }

    @EventHandler
    public void onServerDisconnect(ServerDisconnectEvent event) {
        String serverName = event.getTarget().getName();
        lastActivity.put(serverName, System.currentTimeMillis());
    }

    public void markActivity(String serverName) {
        lastActivity.put(serverName, System.currentTimeMillis());
    }

    private UUID findOwner(String serverName) {
        for (ProxiedPlayer player : plugin.getProxy().getPlayers()) {
            if (player.getServer() != null && serverName.equals(player.getServer().getInfo().getName())) {
                return player.getUniqueId();
            }
        }
        return null;
    }
}
