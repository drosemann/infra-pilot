package com.playerservers.features.server;

import com.playerservers.PlayerServerPlugin;
import net.md_5.bungee.api.ChatColor;
import net.md_5.bungee.api.chat.ComponentBuilder;
import net.md_5.bungee.api.connection.ProxiedPlayer;
import net.md_5.bungee.api.event.ChatEvent;
import net.md_5.bungee.api.plugin.Listener;
import net.md_5.bungee.event.EventHandler;

import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

public class AntiCheatManager implements Listener {

    private final PlayerServerPlugin plugin;
    private final Map<UUID, AlertRecord> alerts;
    private final int maxAlertsBeforeFlag;

    public AntiCheatManager(PlayerServerPlugin plugin) {
        this.plugin = plugin;
        this.alerts = new ConcurrentHashMap<>();
        this.maxAlertsBeforeFlag = plugin.getConfigManager().getInt("anticheat.max_alerts_before_flag", 5);
        plugin.getProxy().getPluginManager().registerListener(plugin, this);
    }

    public void reportAlert(UUID player, String hackType, double vl) {
        AlertRecord record = alerts.computeIfAbsent(player, k -> new AlertRecord());
        record.addAlert(hackType, vl);

        if (record.totalAlerts.get() >= maxAlertsBeforeFlag) {
            flagPlayer(player, record);
            alerts.remove(player);
        }
    }

    private void flagPlayer(UUID uuid, AlertRecord record) {
        ProxiedPlayer player = plugin.getProxy().getPlayer(uuid);
        if (player != null) {
            plugin.getProxy().broadcast(new ComponentBuilder("[AntiCheat] ")
                .color(ChatColor.RED)
                .append(player.getName()).color(ChatColor.YELLOW)
                .append(" has been flagged for suspicious activity!").color(ChatColor.RED).create());
        }
    }

    @EventHandler
    public void onChat(ChatEvent event) {
        if (event.isCommand()) return;
        if (!(event.getSender() instanceof ProxiedPlayer)) return;

        String msg = event.getMessage().toLowerCase();
        // Simple anti-spam check
        if (msg.length() > 100) {
            ProxiedPlayer player = (ProxiedPlayer) event.getSender();
            reportAlert(player.getUniqueId(), "SPAM", 1.0);
        }
    }

    private static class AlertRecord {
        final AtomicInteger totalAlerts;
        final Map<String, Double> alertsByType;
        long lastAlertTime;

        AlertRecord() {
            this.totalAlerts = new AtomicInteger(0);
            this.alertsByType = new ConcurrentHashMap<>();
            this.lastAlertTime = System.currentTimeMillis();
        }

        void addAlert(String type, double vl) {
            totalAlerts.incrementAndGet();
            alertsByType.merge(type, vl, Double::sum);
            lastAlertTime = System.currentTimeMillis();
        }
    }
}
