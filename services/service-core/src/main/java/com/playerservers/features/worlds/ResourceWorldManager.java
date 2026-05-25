package com.playerservers.features.worlds;

import com.playerservers.PlayerServerPlugin;
import net.md_5.bungee.api.ChatColor;
import net.md_5.bungee.api.chat.ComponentBuilder;
import net.md_5.bungee.api.config.ServerInfo;
import net.md_5.bungee.api.connection.ProxiedPlayer;
import net.md_5.bungee.config.Configuration;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.List;
import java.util.concurrent.TimeUnit;
import java.util.logging.Level;

public class ResourceWorldManager {
    private final PlayerServerPlugin plugin;
    private final String worldName;
    private final long regenerationInterval;
    private final String serverTemplate;
    private final List<Integer> warningTimes;
    private final boolean autoTeleport;
    private final String spawnWorld;
    private final boolean backupOldWorld;
    private boolean isRegenerating = false;

    public ResourceWorldManager(PlayerServerPlugin plugin) {
        this.plugin = plugin;
        Configuration config = plugin.getConfig();
        this.worldName = config.getString("resource_world.name", "resource_world");
        this.regenerationInterval = config.getLong("resource_world.regeneration_interval", 7 * 24 * 60);
        this.serverTemplate = config.getString("resource_world.template", "resource_template");
        this.warningTimes = config.getIntList("resource_world.warning_times");
        this.autoTeleport = config.getBoolean("resource_world.auto_teleport", true);
        this.spawnWorld = config.getString("resource_world.spawn_world", "hub");
        this.backupOldWorld = config.getBoolean("resource_world.backup_old_world", false);
        
        if (config.getBoolean("resource_world.enabled", true)) {
            startRegenerationTask();
            scheduleWarnings();
        }
    }

    private void scheduleWarnings() {
        long nextRegeneration = regenerationInterval;
        
        for (int warningTime : warningTimes) {
            long warningDelay = nextRegeneration - warningTime;
            if (warningDelay > 0) {
                plugin.getProxy().getScheduler().schedule(plugin, () -> {
                    broadcastWarning(warningTime);
                }, warningDelay, regenerationInterval, TimeUnit.MINUTES);
            }
        }
    }

    private void broadcastWarning(int minutesLeft) {
        String timeString = formatTime(minutesLeft);
        String message = ChatColor.GOLD + "[Resource World] " + ChatColor.YELLOW + 
                        "The resource world will regenerate in " + timeString + "!";
        
        ServerInfo resourceServer = plugin.getProxy().getServerInfo(worldName);
        if (resourceServer != null) {
            for (ProxiedPlayer player : resourceServer.getPlayers()) {
                player.sendMessage(new ComponentBuilder(message).create());
            }
        }
    }

    private String formatTime(int minutes) {
        if (minutes < 60) {
            return minutes + " minutes";
        } else if (minutes == 60) {
            return "1 hour";
        } else if (minutes < 1440) {
            return (minutes / 60) + " hours";
        } else {
            return (minutes / 1440) + " days";
        }
    }

    private void notifyPlayers() {
        ServerInfo resourceServer = plugin.getProxy().getServerInfo(worldName);
        if (resourceServer != null) {
            String message = ChatColor.GOLD + "[Resource World] " + ChatColor.RED + 
                           "Resource world regeneration is starting now!";
            
            for (ProxiedPlayer player : resourceServer.getPlayers()) {
                player.sendMessage(new ComponentBuilder(message).create());
            }
        }
    }

    private void evacuateWorld() {
        ServerInfo resourceServer = plugin.getProxy().getServerInfo(worldName);
        ServerInfo spawnServer = plugin.getProxy().getServerInfo(spawnWorld);
        
        if (resourceServer != null && spawnServer != null) {
            for (ProxiedPlayer player : resourceServer.getPlayers()) {
                if (autoTeleport) {
                    player.connect(spawnServer);
                    player.sendMessage(new ComponentBuilder()
                        .color(ChatColor.YELLOW)
                        .append("You have been teleported to spawn due to resource world regeneration.")
                        .create());
                } else {
                    player.disconnect(new ComponentBuilder()
                        .color(ChatColor.RED)
                        .append("Resource world is regenerating. Please rejoin in a few minutes.")
                        .create());
                }
            }
        }
        
        // Wait a moment to ensure all players are evacuated
        try {
            Thread.sleep(5000);
        } catch (InterruptedException e) {
            plugin.getLogger().log(Level.WARNING, "Evacuation wait interrupted", e);
        }
    }

    private void stopWorld() {
        plugin.getServerManager().stopServer(worldName);
        
        // Wait for server to fully stop
        try {
            Thread.sleep(10000);
        } catch (InterruptedException e) {
            plugin.getLogger().log(Level.WARNING, "Stop world wait interrupted", e);
        }
    }

    private void deleteWorld() {
        File worldDir = new File(plugin.getDataFolder(), "servers/" + worldName);
        
        if (backupOldWorld) {
            File backupDir = new File(plugin.getDataFolder(), "backups/resource_worlds/" + 
                                    System.currentTimeMillis());
            try {
                Files.move(worldDir.toPath(), backupDir.toPath(), StandardCopyOption.REPLACE_EXISTING);
            } catch (IOException e) {
                plugin.getLogger().log(Level.SEVERE, "Failed to backup old resource world", e);
            }
        } else {
            deleteDirectory(worldDir);
        }
    }

    private void deleteDirectory(File directory) {
        if (directory.exists()) {
            File[] files = directory.listFiles();
            if (files != null) {
                for (File file : files) {
                    if (file.isDirectory()) {
                        deleteDirectory(file);
                    } else {
                        file.delete();
                    }
                }
            }
            directory.delete();
        }
    }

    private void copyTemplate() {
        File templateDir = new File(plugin.getDataFolder(), "templates/" + serverTemplate);
        File worldDir = new File(plugin.getDataFolder(), "servers/" + worldName);
        
        try {
            copyDirectory(templateDir.toPath(), worldDir.toPath());
        } catch (IOException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to copy world template", e);
        }
    }

    private void copyDirectory(Path source, Path target) throws IOException {
        if (!Files.exists(target)) {
            Files.createDirectories(target);
        }
        
        Files.walk(source).forEach(sourcePath -> {
            try {
                Path targetPath = target.resolve(source.relativize(sourcePath));
                if (Files.isDirectory(sourcePath)) {
                    if (!Files.exists(targetPath)) {
                        Files.createDirectories(targetPath);
                    }
                } else {
                    Files.copy(sourcePath, targetPath, StandardCopyOption.REPLACE_EXISTING);
                }
            } catch (IOException e) {
                plugin.getLogger().log(Level.SEVERE, "Failed to copy file: " + sourcePath, e);
            }
        });
    }

    private void startWorld() {
        plugin.getServerManager().startServer(worldName);
    }

    // Add this to your existing regenerateWorld method
    public void regenerateWorld() {
        if (isRegenerating) {
            plugin.getLogger().warning("Resource world regeneration already in progress!");
            return;
        }
        
        isRegenerating = true;
        plugin.getLogger().info("Starting resource world regeneration...");
        
        try {
            notifyPlayers();
            evacuateWorld();
            stopWorld();
            deleteWorld();
            copyTemplate();
            startWorld();
            
            plugin.getLogger().info("Resource world regeneration complete!");
        } catch (Exception e) {
            plugin.getLogger().log(Level.SEVERE, "Error during world regeneration", e);
        } finally {
            isRegenerating = false;
        }
    }

    public boolean isRegenerating() {
        return isRegenerating;
    }

    public String getWorldName() {
        return worldName;
    }
}