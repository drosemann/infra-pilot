package com.playerservers.features.economy;

import com.playerservers.PlayerServerPlugin;
import net.md_5.bungee.api.ChatColor;
import net.md_5.bungee.api.CommandSender;
import net.md_5.bungee.api.chat.ComponentBuilder;
import net.md_5.bungee.api.connection.ProxiedPlayer;
import net.md_5.bungee.api.plugin.Command;

import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicReference;

public class ShopTaxManager {

    private final PlayerServerPlugin plugin;
    private final EconomyManager economyManager;
    private final AtomicReference<Double> taxRate;
    private final Map<UUID, Double> taxRevenue;
    private double totalTaxCollected;

    public ShopTaxManager(PlayerServerPlugin plugin, EconomyManager economyManager) {
        this.plugin = plugin;
        this.economyManager = economyManager;
        this.taxRate = new AtomicReference<>(plugin.getConfigManager().getDouble("economy.shop_tax_rate", 0.05));
        this.taxRevenue = new ConcurrentHashMap<>();
    }

    public double applySaleTax(UUID seller, double saleAmount) {
        double tax = saleAmount * taxRate.get();
        double afterTax = saleAmount - tax;
        economyManager.deposit(seller, afterTax, "Shop sale (after " + (taxRate.get() * 100) + "% tax)");
        taxRevenue.merge(seller, tax, Double::sum);
        totalTaxCollected += tax;
        return afterTax;
    }

    public double getTaxRate() { return taxRate.get(); }
    public void setTaxRate(double rate) { taxRate.set(rate); }
    public double getTotalTaxCollected() { return totalTaxCollected; }
    public double getPlayerTaxContribution(UUID uuid) { return taxRevenue.getOrDefault(uuid, 0.0); }

    public static class ShopTaxCommands {
        private final PlayerServerPlugin plugin;
        private final ShopTaxManager shopTaxManager;

        public ShopTaxCommands(PlayerServerPlugin plugin, ShopTaxManager shopTaxManager) {
            this.plugin = plugin;
            this.shopTaxManager = shopTaxManager;
            plugin.getProxy().getPluginManager().registerCommand(plugin, new ShopTaxCommand());
            plugin.getProxy().getPluginManager().registerCommand(plugin, new ShopTaxAdminCommand());
        }

        private class ShopTaxCommand extends Command {
            public ShopTaxCommand() { super("shoptax", "playerservers.economy.shoptax"); }

            @Override
            public void execute(CommandSender sender, String[] args) {
                sender.sendMessage(new ComponentBuilder("Current shop tax rate: ")
                    .color(ChatColor.YELLOW)
                    .append(String.format("%.1f%%", shopTaxManager.getTaxRate() * 100))
                    .color(ChatColor.GREEN).create());
                sender.sendMessage(new ComponentBuilder("Total tax collected: ")
                    .color(ChatColor.YELLOW)
                    .append(String.format("$%.2f", shopTaxManager.getTotalTaxCollected()))
                    .color(ChatColor.GOLD).create());
            }
        }

        private class ShopTaxAdminCommand extends Command {
            public ShopTaxAdminCommand() { super("shoptaxadmin", "playerservers.economy.shoptax.admin"); }

            @Override
            public void execute(CommandSender sender, String[] args) {
                if (args.length == 1) {
                    try {
                        double rate = Double.parseDouble(args[0]);
                        if (rate < 0 || rate > 1) {
                            sender.sendMessage(new ComponentBuilder("Rate must be between 0 and 1").color(ChatColor.RED).create());
                            return;
                        }
                        shopTaxManager.setTaxRate(rate);
                        sender.sendMessage(new ComponentBuilder("Shop tax rate set to " + (rate * 100) + "%").color(ChatColor.GREEN).create());
                    } catch (NumberFormatException e) {
                        sender.sendMessage(new ComponentBuilder("Usage: /shoptaxadmin <rate>").color(ChatColor.RED).create());
                    }
                }
            }
        }
    }
}
