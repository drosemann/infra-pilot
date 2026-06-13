package com.playerservers.features.server;

import com.playerservers.PlayerServerPlugin;
import net.md_5.bungee.api.ChatColor;
import net.md_5.bungee.api.CommandSender;
import net.md_5.bungee.api.chat.ComponentBuilder;
import net.md_5.bungee.api.connection.ProxiedPlayer;
import net.md_5.bungee.api.event.ChatEvent;
import net.md_5.bungee.api.plugin.Command;
import net.md_5.bungee.api.plugin.Listener;
import net.md_5.bungee.event.EventHandler;

import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.TimeUnit;

public class CommandCooldownManager implements Listener {

    private final PlayerServerPlugin plugin;
    private final Map<String, Map<String, Long>> cooldowns; // command -> (group -> cooldown ms)
    private final Map<String, Map<UUID, Long>> playerCooldowns;

    public CommandCooldownManager(PlayerServerPlugin plugin) {
        this.plugin = plugin;
        this.cooldowns = new ConcurrentHashMap<>();
        this.playerCooldowns = new ConcurrentHashMap<>();
        loadDefaults();
    }

    private void loadDefaults() {
        setCooldown("fly", "default", 5000);
        setCooldown("feed", "default", 30000);
        setCooldown("heal", "default", 60000);
        setCooldown("tpa", "default", 10000);
        setCooldown("spawn", "default", 15000);
    }

    public void setCooldown(String command, String group, long cooldownMs) {
        cooldowns.computeIfAbsent(command, k -> new ConcurrentHashMap<>()).put(group, cooldownMs);
    }

    public boolean checkCooldown(ProxiedPlayer player, String command) {
        if (player.hasPermission("playerservers.cooldown.bypass")) return true;

        Map<String, Long> commandCooldowns = cooldowns.get(command);
        if (commandCooldowns == null) return true;

        long cooldown = commandCooldowns.getOrDefault("default", 0L);
        for (Map.Entry<String, Long> entry : commandCooldowns.entrySet()) {
            if (player.hasPermission("playerservers.cooldown." + entry.getKey())) {
                cooldown = entry.getValue();
                break;
            }
        }

        if (cooldown <= 0) return true;

        Map<UUID, Long> cmdCooldowns = playerCooldowns.computeIfAbsent(command, k -> new ConcurrentHashMap<>());
        Long lastUse = cmdCooldowns.get(player.getUniqueId());
        long now = System.currentTimeMillis();

        if (lastUse != null && (now - lastUse) < cooldown) {
            long remaining = cooldown - (now - lastUse);
            player.sendMessage(new ComponentBuilder("Please wait " + (remaining / 1000 + 1) + "s before using /" + command + " again")
                .color(ChatColor.RED).create());
            return false;
        }

        cmdCooldowns.put(player.getUniqueId(), now);
        return true;
    }

    public static class CooldownCommands {
        private final PlayerServerPlugin plugin;
        private final CommandCooldownManager manager;

        public CooldownCommands(PlayerServerPlugin plugin, CommandCooldownManager manager) {
            this.plugin = plugin;
            this.manager = manager;
            plugin.getProxy().getPluginManager().registerCommand(plugin, new CooldownCommand());
        }

        private class CooldownCommand extends Command {
            public CooldownCommand() { super("cooldowns", "playerservers.cooldowns.admin"); }

            @Override
            public void execute(CommandSender sender, String[] args) {
                if (args.length >= 3) {
                    try {
                        long ms = Long.parseLong(args[2]);
                        manager.setCooldown(args[0], args[1], ms);
                        sender.sendMessage(new ComponentBuilder("Cooldown set: /" + args[0] + " for " + args[1] + " = " + ms + "ms")
                            .color(ChatColor.GREEN).create());
                    } catch (NumberFormatException e) {
                        sender.sendMessage(new ComponentBuilder("Usage: /cooldowns <command> <group> <milliseconds>")
                            .color(ChatColor.RED).create());
                    }
                } else {
                    sender.sendMessage(new ComponentBuilder("Usage: /cooldowns <command> <group> <milliseconds>")
                        .color(ChatColor.RED).create());
                }
            }
        }
    }
}
