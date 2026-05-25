package com.playerservers;

import net.md_5.bungee.config.Configuration;
import net.md_5.bungee.config.ConfigurationProvider;
import net.md_5.bungee.config.YamlConfiguration;

import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;

public class ConfigManager {

    private final PlayerServerPlugin plugin;
    private Configuration config;

    public ConfigManager(PlayerServerPlugin plugin) {
        this.plugin = plugin;
    }

    public void loadConfig() {
        File configFile = new File(plugin.getDataFolder(), "config.yml");
        if (!configFile.exists()) {
            plugin.getDataFolder().mkdirs();
            try (InputStream in = plugin.getResourceAsStream("config.yml")) {
                if (in != null) {
                    Files.copy(in, configFile.toPath());
                }
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
        try {
            config = ConfigurationProvider.getProvider(YamlConfiguration.class).load(configFile);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    public Configuration getConfig() { return config; }
    public String getString(String path) { return config.getString(path); }
    public int getInt(String path) { return config.getInt(path); }
    public long getLong(String path) { return config.getLong(path); }
    public double getDouble(String path) { return config.getDouble(path); }
    public boolean getBoolean(String path) { return config.getBoolean(path); }
    public boolean getBoolean(String path, boolean def) { return config.getBoolean(path, def); }
    public int getInt(String path, int def) { return config.getInt(path, def); }
    public long getLong(String path, long def) { return config.getLong(path, def); }
    public double getDouble(String path, double def) { return config.getDouble(path, def); }
    public String getString(String path, String def) { return config.getString(path, def); }
}
