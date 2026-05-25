package com.playerservers;

import net.md_5.bungee.api.ChatColor;
import net.md_5.bungee.api.CommandSender;
import net.md_5.bungee.api.chat.ComponentBuilder;
import net.md_5.bungee.api.connection.ProxiedPlayer;
import net.md_5.bungee.api.plugin.Command;

import java.util.UUID;

public class ServerCommand extends Command {

    private final PlayerServerPlugin plugin;

    public ServerCommand(PlayerServerPlugin plugin) {
        super("server", "playerserver.command.server", "pserver");
        this.plugin = plugin;
    }

    @Override
    public void execute(CommandSender sender, String[] args) {
        if (!(sender instanceof ProxiedPlayer)) {
            sender.sendMessage(new ComponentBuilder("This command can only be used by players.").color(ChatColor.RED).create());
            return;
        }

        ProxiedPlayer player = (ProxiedPlayer) sender;
        UUID playerUUID = player.getUniqueId();

        if (args.length == 0) {
            showHelp(player);
            return;
        }

        switch (args[0].toLowerCase()) {
            case "create": handleCreate(player, playerUUID); break;
            case "delete": handleDelete(player, playerUUID); break;
            case "join": handleJoin(player, playerUUID); break;
            case "list": handleList(player); break;
            case "manage": handleManage(player); break;
            default: showHelp(player);
        }
    }

    private void handleCreate(ProxiedPlayer player, UUID playerUUID) {
        if (plugin.getDatabaseManager().hasServer(playerUUID.toString())) {
            player.sendMessage(new ComponentBuilder("You already have a server!").color(ChatColor.RED).create());
            return;
        }
        plugin.getServerManager().createServer(playerUUID);
        player.sendMessage(new ComponentBuilder("Creating your server...").color(ChatColor.GREEN).create());
    }

    private void handleDelete(ProxiedPlayer player, UUID playerUUID) {
        if (!plugin.getDatabaseManager().hasServer(playerUUID.toString())) {
            player.sendMessage(new ComponentBuilder("You don't have a server to delete!").color(ChatColor.RED).create());
            return;
        }
        plugin.getServerManager().deleteServer(playerUUID);
        player.sendMessage(new ComponentBuilder("Deleting your server...").color(ChatColor.GREEN).create());
    }

    private void handleJoin(ProxiedPlayer player, UUID playerUUID) {
        String serverName = plugin.getDatabaseManager().getServerName(playerUUID.toString());
        if (serverName == null) {
            player.sendMessage(new ComponentBuilder("You don't have a server to join!").color(ChatColor.RED).create());
            return;
        }
        plugin.getServerManager().startServer(playerUUID);
        player.connect(plugin.getProxy().getServerInfo(serverName));
    }

    private void handleList(ProxiedPlayer player) {
        player.sendMessage(new ComponentBuilder("=== Player Servers ===").color(ChatColor.GOLD).create());
        boolean found = false;
        for (String name : plugin.getProxy().getServers().keySet()) {
            if (name.contains("-server")) {
                found = true;
                String status = plugin.getDatabaseManager().getServerStatus(
                    name.replace("-server", ""));
                ChatColor color = "RUNNING".equals(status) ? ChatColor.GREEN : ChatColor.RED;
                player.sendMessage(new ComponentBuilder(" - " + name).color(ChatColor.YELLOW)
                    .append(" [" + (status != null ? status : "UNKNOWN") + "]").color(color).create());
            }
        }
        if (!found) {
            player.sendMessage(new ComponentBuilder("No player servers available.").color(ChatColor.RED).create());
        }
    }

    private void handleManage(ProxiedPlayer player) {
        plugin.getGuiManager().openMainMenu(player);
    }

    private void showHelp(ProxiedPlayer player) {
        player.sendMessage(new ComponentBuilder("=== Server Commands ===").color(ChatColor.GOLD).create());
        player.sendMessage(new ComponentBuilder("/server create").color(ChatColor.YELLOW)
            .append(" - Create your server").color(ChatColor.WHITE).create());
        player.sendMessage(new ComponentBuilder("/server delete").color(ChatColor.YELLOW)
            .append(" - Delete your server").color(ChatColor.WHITE).create());
        player.sendMessage(new ComponentBuilder("/server join").color(ChatColor.YELLOW)
            .append(" - Join your server").color(ChatColor.WHITE).create());
        player.sendMessage(new ComponentBuilder("/server list").color(ChatColor.YELLOW)
            .append(" - List servers").color(ChatColor.WHITE).create());
        player.sendMessage(new ComponentBuilder("/server manage").color(ChatColor.YELLOW)
            .append(" - Manage your server").color(ChatColor.WHITE).create());
    }
}
