package com.playerservers.features.gameplay;

import com.playerservers.PlayerServerPlugin;
import net.md_5.bungee.api.ChatColor;
import net.md_5.bungee.api.CommandSender;
import net.md_5.bungee.api.chat.ComponentBuilder;
import net.md_5.bungee.api.connection.ProxiedPlayer;
import net.md_5.bungee.api.plugin.Command;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.logging.Level;

public class PlayerTimeWeatherManager {

    private final PlayerServerPlugin plugin;
    private final Map<UUID, Long> playerTime;
    private final Map<UUID, String> playerWeather;

    public PlayerTimeWeatherManager(PlayerServerPlugin plugin) {
        this.plugin = plugin;
        this.playerTime = new ConcurrentHashMap<>();
        this.playerWeather = new ConcurrentHashMap<>();
        initDatabase();
    }

    private void initDatabase() {
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            conn.createStatement().execute("CREATE TABLE IF NOT EXISTS player_time_weather (" +
                "uuid VARCHAR(36) PRIMARY KEY," +
                "time BIGINT DEFAULT -1," +
                "weather VARCHAR(16) DEFAULT 'reset'" +
                ")");
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to init time/weather DB", e);
        }
    }

    public void setTime(UUID player, long time) {
        playerTime.put(player, time);
        save(player, time, playerWeather.getOrDefault(player, "reset"));
    }

    public void setWeather(UUID player, String weather) {
        playerWeather.put(player, weather);
        save(player, playerTime.getOrDefault(player, -1L), weather);
    }

    public void reset(UUID player) {
        playerTime.remove(player);
        playerWeather.remove(player);
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement("DELETE FROM player_time_weather WHERE uuid = ?");
            stmt.setString(1, player.toString());
            stmt.executeUpdate();
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to reset time/weather", e);
        }
    }

    public long getTime(UUID player) { return playerTime.getOrDefault(player, -1L); }
    public String getWeather(UUID player) { return playerWeather.getOrDefault(player, "reset"); }

    private void save(UUID player, long time, String weather) {
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "INSERT OR REPLACE INTO player_time_weather (uuid, time, weather) VALUES (?,?,?)");
            stmt.setString(1, player.toString());
            stmt.setLong(2, time);
            stmt.setString(3, weather);
            stmt.executeUpdate();
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to save time/weather", e);
        }
    }

    public static class PlayerTimeCommands {
        private final PlayerServerPlugin plugin;
        private final PlayerTimeWeatherManager manager;

        public PlayerTimeCommands(PlayerServerPlugin plugin, PlayerTimeWeatherManager manager) {
            this.plugin = plugin;
            this.manager = manager;
            plugin.getProxy().getPluginManager().registerCommand(plugin, new PTimeCommand());
            plugin.getProxy().getPluginManager().registerCommand(plugin, new PWeatherCommand());
        }

        private class PTimeCommand extends Command {
            public PTimeCommand() { super("ptime", "playerservers.ptime"); }

            @Override
            public void execute(CommandSender sender, String[] args) {
                if (!(sender instanceof ProxiedPlayer)) return;
                ProxiedPlayer player = (ProxiedPlayer) sender;
                if (args.length == 0) {
                    player.sendMessage(new ComponentBuilder("Usage: /ptime <day|night|reset|time>")
                        .color(ChatColor.RED).create());
                    return;
                }
                if ("reset".equalsIgnoreCase(args[0])) {
                    manager.reset(player.getUniqueId());
                    player.sendMessage(new ComponentBuilder("Time reset to world default").color(ChatColor.GREEN).create());
                } else if ("day".equalsIgnoreCase(args[0])) {
                    manager.setTime(player.getUniqueId(), 1000);
                    player.sendMessage(new ComponentBuilder("Time set to day").color(ChatColor.GREEN).create());
                } else if ("night".equalsIgnoreCase(args[0])) {
                    manager.setTime(player.getUniqueId(), 13000);
                    player.sendMessage(new ComponentBuilder("Time set to night").color(ChatColor.GREEN).create());
                } else {
                    try {
                        manager.setTime(player.getUniqueId(), Long.parseLong(args[0]));
                        player.sendMessage(new ComponentBuilder("Time set to tick " + args[0]).color(ChatColor.GREEN).create());
                    } catch (NumberFormatException e) {
                        player.sendMessage(new ComponentBuilder("Invalid time").color(ChatColor.RED).create());
                    }
                }
            }
        }

        private class PWeatherCommand extends Command {
            public PWeatherCommand() { super("pweather", "playerservers.pweather"); }

            @Override
            public void execute(CommandSender sender, String[] args) {
                if (!(sender instanceof ProxiedPlayer)) return;
                ProxiedPlayer player = (ProxiedPlayer) sender;
                if (args.length == 0) {
                    player.sendMessage(new ComponentBuilder("Usage: /pweather <sun|rain|storm|reset>")
                        .color(ChatColor.RED).create());
                    return;
                }
                String weather = args[0].toLowerCase();
                if ("reset".equals(weather)) {
                    manager.reset(player.getUniqueId());
                    player.sendMessage(new ComponentBuilder("Weather reset to world default").color(ChatColor.GREEN).create());
                } else if ("sun".equals(weather) || "rain".equals(weather) || "storm".equals(weather)) {
                    manager.setWeather(player.getUniqueId(), weather);
                    player.sendMessage(new ComponentBuilder("Weather set to " + weather).color(ChatColor.GREEN).create());
                } else {
                    player.sendMessage(new ComponentBuilder("Usage: /pweather <sun|rain|storm|reset>")
                        .color(ChatColor.RED).create());
                }
            }
        }
    }
}
