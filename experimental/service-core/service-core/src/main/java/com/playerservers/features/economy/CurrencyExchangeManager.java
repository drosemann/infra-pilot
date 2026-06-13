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

public class CurrencyExchangeManager {

    private final PlayerServerPlugin plugin;
    private final EconomyManager economyManager;
    private final AtomicReference<Double> exchangeRate;
    private final AtomicReference<Double> exchangeFee;

    public CurrencyExchangeManager(PlayerServerPlugin plugin, EconomyManager economyManager) {
        this.plugin = plugin;
        this.economyManager = economyManager;
        this.exchangeRate = new AtomicReference<>(plugin.getConfigManager().getDouble("economy.exchange_rate", 1.0));
        this.exchangeFee = new AtomicReference<>(plugin.getConfigManager().getDouble("economy.exchange_fee", 0.02));
    }

    public boolean exchange(UUID player, double amount) {
        double fee = amount * exchangeFee.get();
        double totalCost = amount + fee;
        if (!economyManager.hasBalance(player, totalCost)) return false;
        if (economyManager.withdraw(player, totalCost, "Currency exchange")) {
            economyManager.deposit(player, amount * exchangeRate.get(), "Currency exchange credit");
            return true;
        }
        return false;
    }

    public double getExchangeRate() { return exchangeRate.get(); }
    public void setExchangeRate(double rate) { exchangeRate.set(rate); }
    public double getExchangeFee() { return exchangeFee.get(); }

    public static class CurrencyCommands {
        private final PlayerServerPlugin plugin;
        private final CurrencyExchangeManager exchange;

        public CurrencyCommands(PlayerServerPlugin plugin, CurrencyExchangeManager exchange) {
            this.plugin = plugin;
            this.exchange = exchange;
            plugin.getProxy().getPluginManager().registerCommand(plugin, new ExchangeCommand());
            plugin.getProxy().getPluginManager().registerCommand(plugin, new ExchangeAdminCommand());
        }

        private class ExchangeCommand extends Command {
            public ExchangeCommand() { super("exchange", "playerservers.economy.exchange"); }

            @Override
            public void execute(CommandSender sender, String[] args) {
                if (!(sender instanceof ProxiedPlayer)) {
                    sender.sendMessage(new ComponentBuilder("Players only").color(ChatColor.RED).create());
                    return;
                }
                ProxiedPlayer player = (ProxiedPlayer) sender;
                if (args.length != 1) {
                    player.sendMessage(new ComponentBuilder("Usage: /exchange <amount>")
                        .color(ChatColor.RED).create());
                    player.sendMessage(new ComponentBuilder("Rate: " + exchange.getExchangeRate() +
                        " | Fee: " + (exchange.getExchangeFee() * 100) + "%")
                        .color(ChatColor.YELLOW).create());
                    return;
                }
                try {
                    double amount = Double.parseDouble(args[0]);
                    double totalCost = amount * (1 + exchange.getExchangeFee());
                    if (exchange.exchange(player.getUniqueId(), amount)) {
                        player.sendMessage(new ComponentBuilder("Exchanged ").color(ChatColor.GREEN)
                            .append(String.format("$%.2f", totalCost)).color(ChatColor.YELLOW)
                            .append(" for ").color(ChatColor.GREEN)
                            .append(String.format("%.2f credits", amount * exchange.getExchangeRate()))
                            .color(ChatColor.GOLD).create());
                    } else {
                        player.sendMessage(new ComponentBuilder("Insufficient funds! Need ")
                            .color(ChatColor.RED)
                            .append(String.format("$%.2f", totalCost)).color(ChatColor.YELLOW).create());
                    }
                } catch (NumberFormatException e) {
                    player.sendMessage(new ComponentBuilder("Invalid amount").color(ChatColor.RED).create());
                }
            }
        }

        private class ExchangeAdminCommand extends Command {
            public ExchangeAdminCommand() { super("exchangeadmin", "playerservers.economy.exchange.admin"); }

            @Override
            public void execute(CommandSender sender, String[] args) {
                if (args.length == 2) {
                    if ("rate".equalsIgnoreCase(args[0])) {
                        try {
                            exchange.setExchangeRate(Double.parseDouble(args[1]));
                            sender.sendMessage(new ComponentBuilder("Exchange rate set to " + args[1])
                                .color(ChatColor.GREEN).create());
                        } catch (NumberFormatException e) {
                            sender.sendMessage(new ComponentBuilder("Invalid number").color(ChatColor.RED).create());
                        }
                    } else if ("fee".equalsIgnoreCase(args[0])) {
                        try {
                            double fee = Double.parseDouble(args[1]);
                            exchange.exchangeFee.set(fee);
                            sender.sendMessage(new ComponentBuilder("Exchange fee set to " + (fee * 100) + "%")
                                .color(ChatColor.GREEN).create());
                        } catch (NumberFormatException e) {
                            sender.sendMessage(new ComponentBuilder("Invalid number").color(ChatColor.RED).create());
                        }
                    }
                } else {
                    sender.sendMessage(new ComponentBuilder("Usage: /exchangeadmin <rate|fee> <value>")
                        .color(ChatColor.RED).create());
                }
            }
        }
    }
}
