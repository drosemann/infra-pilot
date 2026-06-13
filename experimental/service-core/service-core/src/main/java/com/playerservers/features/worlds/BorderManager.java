package com.playerservers.features.worlds;

import com.playerservers.PlayerServerPlugin;
import net.md_5.bungee.api.ChatColor;
import net.md_5.bungee.api.CommandSender;
import net.md_5.bungee.api.chat.ComponentBuilder;
import net.md_5.bungee.api.connection.ProxiedPlayer;
import net.md_5.bungee.api.plugin.Command;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

public class BorderManager {

    private final PlayerServerPlugin plugin;
    private final Map<String, BorderData> worldBorders;
    private final AtomicInteger expansionTaskId;

    public BorderManager(PlayerServerPlugin plugin) {
        this.plugin = plugin;
        this.worldBorders = new ConcurrentHashMap<>();
        this.expansionTaskId = new AtomicInteger(-1);
        startExpansionScheduler();
    }

    public void setBorder(String worldName, int startingSize, int maxSize, int expansionRate, int expansionInterval) {
        worldBorders.put(worldName, new BorderData(startingSize, maxSize, expansionRate, expansionInterval));
    }

    public int getCurrentSize(String worldName) {
        BorderData data = worldBorders.get(worldName);
        return data != null ? data.currentSize.get() : 0;
    }

    public int getMaxSize(String worldName) {
        BorderData data = worldBorders.get(worldName);
        return data != null ? data.maxSize : 0;
    }

    private void startExpansionScheduler() {
        plugin.getProxy().getScheduler().schedule(plugin, () -> {
            for (Map.Entry<String, BorderData> entry : worldBorders.entrySet()) {
                BorderData data = entry.getValue();
                if (data.currentSize.get() < data.maxSize) {
                    int newSize = Math.min(data.currentSize.addAndGet(data.expansionRate), data.maxSize);
                    broadcastBorderUpdate(entry.getKey(), newSize);
                }
            }
        }, 1, 1, TimeUnit.MINUTES);
    }

    private void broadcastBorderUpdate(String worldName, int newSize) {
        if (plugin.getProxy().getServerInfo(worldName) != null) {
            for (ProxiedPlayer player : plugin.getProxy().getServerInfo(worldName).getPlayers()) {
                player.sendMessage(new ComponentBuilder("[Border] World border expanded to ")
                    .color(ChatColor.AQUA)
                    .append(String.valueOf(newSize)).color(ChatColor.GREEN)
                    .append(" blocks").color(ChatColor.AQUA).create());
            }
        }
    }

    private static class BorderData {
        final AtomicInteger currentSize;
        final int maxSize;
        final int expansionRate;
        final int expansionInterval;

        BorderData(int startingSize, int maxSize, int expansionRate, int expansionInterval) {
            this.currentSize = new AtomicInteger(startingSize);
            this.maxSize = maxSize;
            this.expansionRate = expansionRate;
            this.expansionInterval = expansionInterval;
        }
    }

    public static class BorderCommands {
        private final PlayerServerPlugin plugin;
        private final BorderManager borderManager;

        public BorderCommands(PlayerServerPlugin plugin, BorderManager borderManager) {
            this.plugin = plugin;
            this.borderManager = borderManager;
            plugin.getProxy().getPluginManager().registerCommand(plugin, new BorderCommand());
            plugin.getProxy().getPluginManager().registerCommand(plugin, new BorderAdminCommand());
        }

        private class BorderCommand extends Command {
            public BorderCommand() { super("border", "playerservers.border"); }

            @Override
            public void execute(CommandSender sender, String[] args) {
                if (!(sender instanceof ProxiedPlayer)) return;
                ProxiedPlayer player = (ProxiedPlayer) sender;
                String world = player.getServer() != null ? player.getServer().getInfo().getName() : "unknown";
                int current = borderManager.getCurrentSize(world);
                int max = borderManager.getMaxSize(world);
                player.sendMessage(new ComponentBuilder("World border: ").color(ChatColor.YELLOW)
                    .append(String.valueOf(current)).color(ChatColor.GREEN)
                    .append(" / ").color(ChatColor.YELLOW)
                    .append(String.valueOf(max)).color(ChatColor.GOLD)
                    .append(" blocks").color(ChatColor.YELLOW).create());
            }
        }

        private class BorderAdminCommand extends Command {
            public BorderAdminCommand() { super("borderadmin", "playerservers.border.admin"); }

            @Override
            public void execute(CommandSender sender, String[] args) {
                if (args.length >= 5 && "set".equalsIgnoreCase(args[0])) {
                    try {
                        String world = args[1];
                        int start = Integer.parseInt(args[2]);
                        int max = Integer.parseInt(args[3]);
                        int rate = Integer.parseInt(args[4]);
                        borderManager.setBorder(world, start, max, rate, 1);
                        sender.sendMessage(new ComponentBuilder("Border set for " + world).color(ChatColor.GREEN).create());
                    } catch (NumberFormatException e) {
                        sender.sendMessage(new ComponentBuilder("Usage: /borderadmin set <world> <start> <max> <rate>")
                            .color(ChatColor.RED).create());
                    }
                } else {
                    sender.sendMessage(new ComponentBuilder("Usage: /borderadmin set <world> <start> <max> <rate>")
                        .color(ChatColor.RED).create());
                }
            }
        }
    }
}
