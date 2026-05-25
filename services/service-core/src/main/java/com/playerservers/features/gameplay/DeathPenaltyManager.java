package com.playerservers.features.gameplay;

import com.playerservers.PlayerServerPlugin;
import com.playerservers.features.economy.EconomyManager;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.logging.Level;

public class DeathPenaltyManager {

    private final PlayerServerPlugin plugin;
    private final EconomyManager economyManager;
    private final Map<String, DeathPenaltyConfig> worldPenalties;

    public DeathPenaltyManager(PlayerServerPlugin plugin, EconomyManager economyManager) {
        this.plugin = plugin;
        this.economyManager = economyManager;
        this.worldPenalties = new ConcurrentHashMap<>();
        loadConfig();
    }

    private void loadConfig() {
        String worlds = plugin.getConfigManager().getString("death_penalty.worlds", "all");
        double currencyLoss = plugin.getConfigManager().getDouble("death_penalty.currency_loss_percent", 0.0);
        boolean keepInventory = plugin.getConfigManager().getBoolean("death_penalty.keep_inventory", true);
        boolean keepXP = plugin.getConfigManager().getBoolean("death_penalty.keep_xp", true);
        worldPenalties.put("default", new DeathPenaltyConfig(currencyLoss, keepInventory, keepXP));
    }

    public void applyDeathPenalty(UUID player, String worldName) {
        DeathPenaltyConfig config = worldPenalties.getOrDefault(worldName, worldPenalties.get("default"));
        if (config == null) return;

        if (config.currencyLossPercent > 0) {
            double balance = economyManager.getBalance(player);
            double loss = balance * config.currencyLossPercent;
            if (loss > 0) {
                economyManager.withdraw(player, loss, "Death penalty in " + worldName);
            }
        }
    }

    public static class DeathPenaltyConfig {
        public final double currencyLossPercent;
        public final boolean keepInventory;
        public final boolean keepXP;

        public DeathPenaltyConfig(double currencyLossPercent, boolean keepInventory, boolean keepXP) {
            this.currencyLossPercent = currencyLossPercent;
            this.keepInventory = keepInventory;
            this.keepXP = keepXP;
        }
    }
}
