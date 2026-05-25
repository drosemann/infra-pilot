package com.playerservers;

import net.md_5.bungee.api.ProxyServer;
import net.md_5.bungee.api.config.ServerInfo;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.InetSocketAddress;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.TimeUnit;
import java.util.logging.Level;

public class ServerManager {

    private final PlayerServerPlugin plugin;
    private final Map<String, Process> runningProcesses;

    public ServerManager(PlayerServerPlugin plugin) {
        this.plugin = plugin;
        this.runningProcesses = new ConcurrentHashMap<>();
    }

    public void createServer(UUID playerUUID) {
        String serverName = playerUUID.toString().substring(0, 8) + "-server";
        File serverDirectory = new File(plugin.getDataFolder(), "servers/" + serverName);

        if (serverDirectory.exists()) {
            plugin.getLogger().warning("Server directory already exists: " + serverName);
            return;
        }

        serverDirectory.mkdirs();
        ServerPropertiesGenerator.generate(serverDirectory, serverName);
        createStartScript(serverDirectory, serverName);
        registerServer(serverName, serverDirectory.getAbsolutePath());
        plugin.getDatabaseManager().createServerEntry(playerUUID.toString(), serverName);
    }

    public void createStartScript(File serverDirectory, String serverName) {
        int memoryMB = plugin.getConfigManager().getInt("server.memory_mb", 1024);
        boolean isWindows = System.getProperty("os.name").toLowerCase().contains("win");

        if (isWindows) {
            File batFile = new File(serverDirectory, "start.bat");
            try (FileWriter w = new FileWriter(batFile)) {
                w.write("@echo off\n");
                w.write("title " + serverName + "\n");
                w.write("java -Xms" + (memoryMB / 2) + "M -Xmx" + memoryMB + "M -jar server.jar --nogui\n");
                w.write("pause\n");
            } catch (IOException e) {
                plugin.getLogger().log(Level.SEVERE, "Failed to create start.bat", e);
            }
        } else {
            File shFile = new File(serverDirectory, "start.sh");
            try (FileWriter w = new FileWriter(shFile)) {
                w.write("#!/bin/bash\n");
                w.write("screen -S " + serverName + " java -Xms" + (memoryMB / 2) + "M -Xmx" + memoryMB + "M -jar server.jar --nogui\n");
            } catch (IOException e) {
                plugin.getLogger().log(Level.SEVERE, "Failed to create start.sh", e);
            }
            shFile.setExecutable(true);
        }
    }

    private void registerServer(String serverName, String serverAddress) {
        int port = findAvailablePort(25566, 26000);
        ServerInfo serverInfo = ProxyServer.getInstance().constructServerInfo(
            serverName,
            InetSocketAddress.createUnresolved("localhost", port),
            "Player Server",
            false
        );
        ProxyServer.getInstance().getServers().put(serverName, serverInfo);
    }

    public void startServer(UUID playerUUID) {
        String serverName = plugin.getDatabaseManager().getServerName(playerUUID.toString());
        if (serverName == null) {
            plugin.getLogger().warning("Server name not found for player: " + playerUUID);
            return;
        }

        if (runningProcesses.containsKey(serverName)) {
            plugin.getLogger().info("Server already running: " + serverName);
            return;
        }

        File serverDirectory = new File(plugin.getDataFolder(), "servers/" + serverName);
        if (!serverDirectory.exists()) {
            plugin.getLogger().warning("Server directory not found: " + serverName);
            return;
        }

        try {
            String osName = System.getProperty("os.name").toLowerCase();
            boolean isWindows = osName.contains("win");
            ProcessBuilder pb = new ProcessBuilder(isWindows ? "cmd.exe" : "sh",
                isWindows ? "/c" : "-c",
                isWindows ? "start.bat" : "./start.sh");
            pb.directory(serverDirectory);
            pb.redirectErrorStream(true);
            Process process = pb.start();
            runningProcesses.put(serverName, process);

            plugin.getProxy().getScheduler().runAsync(plugin, () -> {
                try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
                    String line;
                    while ((line = reader.readLine()) != null) {
                        if (plugin.getConfigManager().getBoolean("server.debug_logging", false)) {
                            plugin.getLogger().info("[" + serverName + "] " + line);
                        }
                    }
                } catch (IOException e) {
                    if (runningProcesses.containsKey(serverName)) {
                        plugin.getLogger().log(Level.WARNING, "Process output ended for " + serverName, e);
                    }
                }
            });

            plugin.getProxy().getScheduler().runAsync(plugin, () -> {
                try {
                    int exitCode = process.waitFor();
                    plugin.getLogger().info("Server " + serverName + " exited with code " + exitCode);
                    runningProcesses.remove(serverName);
                } catch (InterruptedException e) {
                    plugin.getLogger().log(Level.WARNING, "Process monitor interrupted for " + serverName, e);
                }
            });

            plugin.getDatabaseManager().updateServerStatus(playerUUID.toString(), "STARTING");

            try { TimeUnit.SECONDS.sleep(5); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
            plugin.getDatabaseManager().updateServerStatus(playerUUID.toString(), "RUNNING");

        } catch (IOException e) {
            plugin.getLogger().severe("Error starting server: " + e.getMessage());
            plugin.getDatabaseManager().updateServerStatus(playerUUID.toString(), "STOPPED");
        }
    }

    public void stopServer(UUID playerUUID) {
        String serverName = plugin.getDatabaseManager().getServerName(playerUUID.toString());
        if (serverName == null) return;

        Process process = runningProcesses.get(serverName);
        if (process != null) {
            process.destroy();
            try {
                if (!process.waitFor(30, TimeUnit.SECONDS)) {
                    process.destroyForcibly();
                }
            } catch (InterruptedException e) {
                process.destroyForcibly();
                Thread.currentThread().interrupt();
            }
            runningProcesses.remove(serverName);
        }

        plugin.getLogger().info("Stopping server: " + serverName);
        plugin.getDatabaseManager().updateServerStatus(playerUUID.toString(), "STOPPED");
    }

    public void deleteServer(UUID playerUUID) {
        String serverName = plugin.getDatabaseManager().getServerName(playerUUID.toString());
        if (serverName == null) return;

        File serverDirectory = new File(plugin.getDataFolder(), "servers/" + serverName);
        stopServer(playerUUID);
        ProxyServer.getInstance().getServers().remove(serverName);

        if (deleteDirectory(serverDirectory)) {
            plugin.getLogger().info("Server directory deleted: " + serverName);
        } else {
            plugin.getLogger().warning("Failed to delete server directory: " + serverName);
        }
        plugin.getDatabaseManager().deleteServerEntry(playerUUID.toString());
    }

    public boolean deleteDirectory(File directory) {
        if (directory.exists()) {
            File[] files = directory.listFiles();
            if (null != files) {
                for (File file : files) {
                    if (file.isDirectory()) {
                        deleteDirectory(file);
                    } else {
                        file.delete();
                    }
                }
            }
        }
        return directory.delete();
    }

    private int findAvailablePort(int start, int max) {
        for (int port = start; port <= max; port++) {
            boolean used = false;
            for (ServerInfo info : ProxyServer.getInstance().getServers().values()) {
                if (info.getAddress().getPort() == port) {
                    used = true;
                    break;
                }
            }
            if (!used) return port;
        }
        return start;
    }
}
