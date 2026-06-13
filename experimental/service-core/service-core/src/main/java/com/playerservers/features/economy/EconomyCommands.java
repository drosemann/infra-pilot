package com.playerservers.features.economy;

import com.playerservers.PlayerServerPlugin;
import net.md_5.bungee.api.ChatColor;
import net.md_5.bungee.api.CommandSender;
import net.md_5.bungee.api.chat.ComponentBuilder;
import net.md_5.bungee.api.connection.ProxiedPlayer;
import net.md_5.bungee.api.plugin.Command;

import java.text.NumberFormat;
import java.util.Locale;
import java.util.Map;
import java.util.UUID;

public class EconomyCommands {
    private final PlayerServerPlugin plugin;
    private final EconomyManager economyManager;

    public EconomyCommands(PlayerServerPlugin plugin, EconomyManager economyManager) {
        this.plugin = plugin;
        this.economyManager = economyManager;
        registerCommands();
    }

    private void registerCommands() {
        plugin.getProxy().getPluginManager().registerCommand(plugin, new BalanceCommand());
        plugin.getProxy().getPluginManager().registerCommand(plugin, new PayCommand());
        plugin.getProxy().getPluginManager().registerCommand(plugin, new EcoAdminCommand());
        plugin.getProxy().getPluginManager().registerCommand(plugin, new TopBalanceCommand());
    }

    private class BalanceCommand extends Command {
        public BalanceCommand() {
            super("balance", "playerservers.economy.balance", "bal", "money");
        }

        @Override
        public void execute(CommandSender sender, String[] args) {
            if (!(sender instanceof ProxiedPlayer)) {
                sender.sendMessage(new ComponentBuilder("This command can only be used by players!").color(ChatColor.RED).create());
                return;
            }

            ProxiedPlayer player = (ProxiedPlayer) sender;
            double balance = economyManager.getBalance(player.getUniqueId());
            String formattedBalance = formatCurrency(balance);
            sender.sendMessage(new ComponentBuilder("Your balance: ").color(ChatColor.YELLOW)
                .append(formattedBalance).color(ChatColor.GREEN).create());
        }
    }

    private class PayCommand extends Command {
        public PayCommand() {
            super("pay", "playerservers.economy.pay", "transfer");
        }

        @Override
        public void execute(CommandSender sender, String[] args) {
            if (!(sender instanceof ProxiedPlayer)) {
                sender.sendMessage(new ComponentBuilder("This command can only be used by players!").color(ChatColor.RED).create());
                return;
            }

            ProxiedPlayer player = (ProxiedPlayer) sender;
            if (args.length != 2) {
                sender.sendMessage(new ComponentBuilder("Usage: /pay <player> <amount>").color(ChatColor.RED).create());
                return;
            }

            ProxiedPlayer target = plugin.getProxy().getPlayer(args[0]);
            if (target == null) {
                sender.sendMessage(new ComponentBuilder("Player not found!").color(ChatColor.RED).create());
                return;
            }

            try {
                double amount = Double.parseDouble(args[1]);
                if (amount <= 0) {
                    sender.sendMessage(new ComponentBuilder("Amount must be positive!").color(ChatColor.RED).create());
                    return;
                }

                if (economyManager.withdraw(player.getUniqueId(), amount, "Payment to " + target.getName())) {
                    economyManager.deposit(target.getUniqueId(), amount, "Payment from " + player.getName());
                    
                    String formattedAmount = formatCurrency(amount);
                    sender.sendMessage(new ComponentBuilder("You sent ").color(ChatColor.GREEN)
                        .append(formattedAmount).color(ChatColor.YELLOW)
                        .append(" to " + target.getName()).color(ChatColor.GREEN).create());
                    
                    target.sendMessage(new ComponentBuilder("You received ").color(ChatColor.GREEN)
                        .append(formattedAmount).color(ChatColor.YELLOW)
                        .append(" from " + player.getName()).color(ChatColor.GREEN).create());
                } else {
                    sender.sendMessage(new ComponentBuilder("Insufficient funds!").color(ChatColor.RED).create());
                }
            } catch (NumberFormatException e) {
                sender.sendMessage(new ComponentBuilder("Invalid amount!").color(ChatColor.RED).create());
            }
        }
    }

    private class EcoAdminCommand extends Command {
        public EcoAdminCommand() {
            super("ecoadmin", "playerservers.economy.admin");
        }

        @Override
        public void execute(CommandSender sender, String[] args) {
            if (!sender.hasPermission("playerservers.economy.admin")) {
                sender.sendMessage(new ComponentBuilder("You don't have permission to use this command!").color(ChatColor.RED).create());
                return;
            }

            if (args.length != 3) {
                sender.sendMessage(new ComponentBuilder("Usage: /ecoadmin <give|take|set> <player> <amount>").color(ChatColor.RED).create());
                return;
            }

            ProxiedPlayer target = plugin.getProxy().getPlayer(args[1]);
            if (target == null) {
                sender.sendMessage(new ComponentBuilder("Player not found!").color(ChatColor.RED).create());
                return;
            }

            try {
                double amount = Double.parseDouble(args[2]);
                String action = args[0].toLowerCase();
                String formattedAmount = formatCurrency(amount);

                switch (action) {
                    case "give":
                        economyManager.deposit(target.getUniqueId(), amount, "Admin give command");
                        sender.sendMessage(new ComponentBuilder("Added ").color(ChatColor.GREEN)
                            .append(formattedAmount).color(ChatColor.YELLOW)
                            .append(" to " + target.getName() + "'s balance").color(ChatColor.GREEN).create());
                        break;

                    case "take":
                        if (economyManager.withdraw(target.getUniqueId(), amount, "Admin take command")) {
                            sender.sendMessage(new ComponentBuilder("Removed ").color(ChatColor.GREEN)
                                .append(formattedAmount).color(ChatColor.YELLOW)
                                .append(" from " + target.getName() + "'s balance").color(ChatColor.GREEN).create());
                        } else {
                            sender.sendMessage(new ComponentBuilder("Player doesn't have enough funds!").color(ChatColor.RED).create());
                        }
                        break;

                    case "set":
                        double currentBalance = economyManager.getBalance(target.getUniqueId());
                        if (amount > currentBalance) {
                            economyManager.deposit(target.getUniqueId(), amount - currentBalance, "Admin set command");
                        } else {
                            economyManager.withdraw(target.getUniqueId(), currentBalance - amount, "Admin set command");
                        }
                        sender.sendMessage(new ComponentBuilder("Set " + target.getName() + "'s balance to ").color(ChatColor.GREEN)
                            .append(formattedAmount).color(ChatColor.YELLOW).create());
                        break;

                    default:
                        sender.sendMessage(new ComponentBuilder("Invalid action! Use give, take, or set").color(ChatColor.RED).create());
                }
            } catch (NumberFormatException e) {
                sender.sendMessage(new ComponentBuilder("Invalid amount!").color(ChatColor.RED).create());
            }
        }
    }

    private class TopBalanceCommand extends Command {
        public TopBalanceCommand() {
            super("balancetop", "playerservers.economy.top", "baltop", "moneytop");
        }

        @Override
        public void execute(CommandSender sender, String[] args) {
            Map<UUID, Double> topBalances = economyManager.getTopBalances(10);
            sender.sendMessage(new ComponentBuilder("=== Top 10 Richest Players ===").color(ChatColor.GOLD).create());

            int rank = 1;
            for (Map.Entry<UUID, Double> entry : topBalances.entrySet()) {
                String playerName = plugin.getProxy().getPlayer(entry.getKey()) != null ? 
                    plugin.getProxy().getPlayer(entry.getKey()).getName() : 
                    entry.getKey().toString();
                
                String formattedBalance = formatCurrency(entry.getValue());
                sender.sendMessage(new ComponentBuilder("#" + rank + " ").color(ChatColor.YELLOW)
                    .append(playerName).color(ChatColor.GREEN)
                    .append(": ").color(ChatColor.WHITE)
                    .append(formattedBalance).color(ChatColor.GOLD).create());
                rank++;
            }
        }
    }

    private String formatCurrency(double amount) {
        NumberFormat format = NumberFormat.getCurrencyInstance(Locale.US);
        return format.format(amount);
    }
}