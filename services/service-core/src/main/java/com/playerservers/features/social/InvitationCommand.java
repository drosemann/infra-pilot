package com.playerservers.features.social;

import com.playerservers.PlayerServerPlugin;
import net.md_5.bungee.api.ChatColor;
import net.md_5.bungee.api.CommandSender;
import net.md_5.bungee.api.chat.ComponentBuilder;
import net.md_5.bungee.api.connection.ProxiedPlayer;
import net.md_5.bungee.api.plugin.Command;

import java.util.List;
import java.util.UUID;

public class InvitationCommand extends Command {
    private final PlayerServerPlugin plugin;
    private final InvitationManager invitationManager;

    public InvitationCommand(PlayerServerPlugin plugin, InvitationManager invitationManager) {
        super("invite", "playerservers.invite");
        this.plugin = plugin;
        this.invitationManager = invitationManager;
    }

    @Override
    public void execute(CommandSender sender, String[] args) {
        if (!(sender instanceof ProxiedPlayer)) {
            sender.sendMessage(new ComponentBuilder("Players only!").color(ChatColor.RED).create());
            return;
        }
        ProxiedPlayer player = (ProxiedPlayer) sender;

        if (args.length == 0) {
            showHelp(player);
            return;
        }

        switch (args[0].toLowerCase()) {
            case "send":
                if (args.length < 2) {
                    player.sendMessage(new ComponentBuilder("Usage: /invite send <player> [permission]").color(ChatColor.RED).create());
                    return;
                }
                String perm = args.length >= 3 ? args[2] : "player";
                handleSend(player, args[1], perm);
                break;
            case "accept":
                if (args.length < 2) {
                    player.sendMessage(new ComponentBuilder("Usage: /invite accept <id>").color(ChatColor.RED).create());
                    return;
                }
                handleAccept(player, args[1]);
                break;
            case "decline":
                if (args.length < 2) {
                    player.sendMessage(new ComponentBuilder("Usage: /invite decline <id>").color(ChatColor.RED).create());
                    return;
                }
                handleDecline(player, args[1]);
                break;
            case "list":
                handleList(player);
                break;
            default:
                showHelp(player);
        }
    }

    private void handleSend(ProxiedPlayer player, String targetName, String permission) {
        if (!plugin.getDatabaseManager().hasServer(player.getUniqueId().toString())) {
            player.sendMessage(new ComponentBuilder("You don't have a server!").color(ChatColor.RED).create());
            return;
        }
        ProxiedPlayer target = plugin.getProxy().getPlayer(targetName);
        if (target == null) {
            player.sendMessage(new ComponentBuilder("Player not found!").color(ChatColor.RED).create());
            return;
        }
        ServerInvitation.PermissionLevel permLevel;
        try {
            permLevel = ServerInvitation.PermissionLevel.valueOf(permission.toLowerCase());
        } catch (IllegalArgumentException e) {
            player.sendMessage(new ComponentBuilder("Invalid permission level. Use: player, operator, admin")
                .color(ChatColor.RED).create());
            return;
        }
        if (invitationManager.sendInvitation(player.getUniqueId(), target.getUniqueId(), player.getUniqueId().toString(), permLevel)) {
            player.sendMessage(new ComponentBuilder("Invitation sent to " + target.getName())
                .color(ChatColor.GREEN).create());
            target.sendMessage(new ComponentBuilder(player.getName() + " invited you to their server! Use /invite list")
                .color(ChatColor.YELLOW).create());
        } else {
            player.sendMessage(new ComponentBuilder("Could not send invitation. Already pending.")
                .color(ChatColor.RED).create());
        }
    }

    private void handleAccept(ProxiedPlayer player, String idStr) {
        int id;
        try {
            id = Integer.parseInt(idStr);
        } catch (NumberFormatException e) {
            player.sendMessage(new ComponentBuilder("Invalid ID!").color(ChatColor.RED).create());
            return;
        }
        if (invitationManager.acceptInvitation(id)) {
            player.sendMessage(new ComponentBuilder("Invitation accepted!").color(ChatColor.GREEN).create());
        } else {
            player.sendMessage(new ComponentBuilder("Could not accept invitation.").color(ChatColor.RED).create());
        }
    }

    private void handleDecline(ProxiedPlayer player, String idStr) {
        int id;
        try {
            id = Integer.parseInt(idStr);
        } catch (NumberFormatException e) {
            player.sendMessage(new ComponentBuilder("Invalid ID!").color(ChatColor.RED).create());
            return;
        }
        if (invitationManager.declineInvitation(id)) {
            player.sendMessage(new ComponentBuilder("Invitation declined.").color(ChatColor.GREEN).create());
        } else {
            player.sendMessage(new ComponentBuilder("Could not decline invitation.").color(ChatColor.RED).create());
        }
    }

    private void handleList(ProxiedPlayer player) {
        List<ServerInvitation> invitations = invitationManager.getPendingInvitations(player.getUniqueId());
        player.sendMessage(new ComponentBuilder("=== Pending Invitations (" + invitations.size() + ") ===")
            .color(ChatColor.GOLD).create());
        if (invitations.isEmpty()) {
            player.sendMessage(new ComponentBuilder("No pending invitations.").color(ChatColor.GRAY).create());
            return;
        }
        for (ServerInvitation inv : invitations) {
            player.sendMessage(new ComponentBuilder(" #" + inv.getId() + " - Server: " + inv.getServerName())
                .color(ChatColor.YELLOW)
                .append(" | From: " + inv.getInviterName()).color(ChatColor.WHITE)
                .append(" | Perm: " + inv.getPermissionLevel()).color(ChatColor.GRAY).create());
        }
    }

    private void showHelp(ProxiedPlayer player) {
        player.sendMessage(new ComponentBuilder("=== Invite Commands ===").color(ChatColor.GOLD).create());
        player.sendMessage(new ComponentBuilder("/invite send <player> [permission]").color(ChatColor.YELLOW)
            .append(" - Invite player to your server").color(ChatColor.WHITE).create());
        player.sendMessage(new ComponentBuilder("/invite accept <id>").color(ChatColor.YELLOW)
            .append(" - Accept invitation").color(ChatColor.WHITE).create());
        player.sendMessage(new ComponentBuilder("/invite decline <id>").color(ChatColor.YELLOW)
            .append(" - Decline invitation").color(ChatColor.WHITE).create());
        player.sendMessage(new ComponentBuilder("/invite list").color(ChatColor.YELLOW)
            .append(" - Show pending invitations").color(ChatColor.WHITE).create());
    }
}
