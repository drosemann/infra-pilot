package com.playerservers;

import com.playerservers.features.social.ServerDiscoveryManager;
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
            case "public": handlePublic(player, args); break;
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

    private void handlePublic(ProxiedPlayer player, String[] args) {
        if (!plugin.getDatabaseManager().hasServer(player.getUniqueId().toString())) {
            player.sendMessage(new ComponentBuilder("You don't have a server!").color(ChatColor.RED).create());
            return;
        }
        if (args.length < 2) {
            player.sendMessage(new ComponentBuilder("Usage: /server public <true|false> [description] [tags]")
                .color(ChatColor.RED).create());
            return;
        }
        boolean isPublic = Boolean.parseBoolean(args[1]);
        String description = "";
        String tags = "";
        if (args.length >= 3) {
            StringBuilder descBuilder = new StringBuilder();
            for (int i = 2; i < args.length; i++) {
                if (args[i].startsWith("#")) {
                    tags = args[i].substring(1);
                    break;
                }
                if (descBuilder.length() > 0) descBuilder.append(" ");
                descBuilder.append(args[i]);
            }
            description = descBuilder.toString();
        }

        ServerDiscoveryManager discovery = plugin.getServerDiscoveryManager();
        discovery.setServerPublic(player.getUniqueId().toString(), isPublic, description, tags);
        player.sendMessage(new ComponentBuilder("Server is now " + (isPublic ? "public" : "private") + "!")
            .color(ChatColor.GREEN).create());
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
        player.sendMessage(new ComponentBuilder("/server public <true|false> [desc] [#tags]").color(ChatColor.YELLOW)
            .append(" - Toggle server visibility").color(ChatColor.WHITE).create());
    }
}
