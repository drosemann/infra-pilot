package com.playerservers.features.server;

import com.playerservers.PlayerServerPlugin;
import net.md_5.bungee.api.ChatColor;
import net.md_5.bungee.api.CommandSender;
import net.md_5.bungee.api.chat.ComponentBuilder;
import net.md_5.bungee.api.chat.TextComponent;
import net.md_5.bungee.api.connection.ProxiedPlayer;
import net.md_5.bungee.api.event.LoginEvent;
import net.md_5.bungee.api.plugin.Command;
import net.md_5.bungee.api.plugin.Listener;
import net.md_5.bungee.event.EventHandler;

import java.util.concurrent.atomic.AtomicBoolean;

public class MaintenanceManager implements Listener {

    private final PlayerServerPlugin plugin;
    private final AtomicBoolean maintenanceMode;
    private String kickMessage;

    public MaintenanceManager(PlayerServerPlugin plugin) {
        this.plugin = plugin;
        this.maintenanceMode = new AtomicBoolean(false);
        this.kickMessage = plugin.getConfigManager().getString("maintenance.kick_message",
            "Server is under maintenance. Please check back later!");
        plugin.getProxy().getPluginManager().registerListener(plugin, this);
    }

    public boolean isMaintenanceMode() { return maintenanceMode.get(); }

    public void setMaintenanceMode(boolean enabled) {
        maintenanceMode.set(enabled);
        String status = enabled ? "enabled" : "disabled";
        plugin.getProxy().broadcast(new ComponentBuilder("Maintenance mode " + status + "!")
            .color(enabled ? ChatColor.RED : ChatColor.GREEN).create());

        if (enabled) {
            for (ProxiedPlayer player : plugin.getProxy().getPlayers()) {
                if (!player.hasPermission("playerservers.maintenance.bypass")) {
                    player.disconnect(new TextComponent(kickMessage));
                }
            }
        }
    }

    public void scheduleMaintenance(long delaySeconds) {
        plugin.getProxy().getScheduler().schedule(plugin, () -> {
            plugin.getProxy().broadcast(new ComponentBuilder("Maintenance starting in 1 minute!")
                .color(ChatColor.RED).create());
        }, delaySeconds - 60, java.util.concurrent.TimeUnit.SECONDS);

        plugin.getProxy().getScheduler().schedule(plugin, () -> {
            setMaintenanceMode(true);
        }, delaySeconds, java.util.concurrent.TimeUnit.SECONDS);
    }

    @EventHandler
    public void onLogin(LoginEvent event) {
        if (maintenanceMode.get()) {
            ProxiedPlayer player = event.getConnection() instanceof ProxiedPlayer ?
                (ProxiedPlayer) event.getConnection() : null;
            if (player != null && !player.hasPermission("playerservers.maintenance.bypass")) {
                event.setCancelled(true);
                event.setCancelReason(new TextComponent(kickMessage));
            }
        }
    }

    public static class MaintenanceCommands {
        private final PlayerServerPlugin plugin;
        private final MaintenanceManager manager;

        public MaintenanceCommands(PlayerServerPlugin plugin, MaintenanceManager manager) {
            this.plugin = plugin;
            this.manager = manager;
            plugin.getProxy().getPluginManager().registerCommand(plugin, new MaintenanceCommand());
        }

        private class MaintenanceCommand extends Command {
            public MaintenanceCommand() { super("maintenance", "playerservers.maintenance", "maint"); }

            @Override
            public void execute(CommandSender sender, String[] args) {
                if (args.length >= 1) {
                    if ("on".equalsIgnoreCase(args[0])) {
                        manager.setMaintenanceMode(true);
                        sender.sendMessage(new ComponentBuilder("Maintenance mode enabled").color(ChatColor.GREEN).create());
                    } else if ("off".equalsIgnoreCase(args[0])) {
                        manager.setMaintenanceMode(false);
                        sender.sendMessage(new ComponentBuilder("Maintenance mode disabled").color(ChatColor.GREEN).create());
                    } else if ("status".equalsIgnoreCase(args[0])) {
                        sender.sendMessage(new ComponentBuilder("Maintenance mode: ")
                            .color(ChatColor.YELLOW)
                            .append(manager.isMaintenanceMode() ? "ENABLED" : "DISABLED")
                            .color(manager.isMaintenanceMode() ? ChatColor.RED : ChatColor.GREEN).create());
                    } else if ("schedule".equalsIgnoreCase(args[0]) && args.length >= 2) {
                        try {
                            long seconds = Long.parseLong(args[1]);
                            manager.scheduleMaintenance(seconds);
                            sender.sendMessage(new ComponentBuilder("Maintenance scheduled in " + seconds + "s")
                                .color(ChatColor.GREEN).create());
                        } catch (NumberFormatException e) {
                            sender.sendMessage(new ComponentBuilder("Invalid time").color(ChatColor.RED).create());
                        }
                    }
                } else {
                    sender.sendMessage(new ComponentBuilder("Usage: /maintenance <on|off|status|schedule <seconds>>")
                        .color(ChatColor.RED).create());
                }
            }
        }
    }
}
