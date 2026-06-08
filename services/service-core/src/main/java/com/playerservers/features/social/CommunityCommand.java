package com.playerservers.features.social;

import com.playerservers.PlayerServerPlugin;
import net.md_5.bungee.api.ChatColor;
import net.md_5.bungee.api.CommandSender;
import net.md_5.bungee.api.chat.ComponentBuilder;
import net.md_5.bungee.api.connection.ProxiedPlayer;
import net.md_5.bungee.api.plugin.Command;

import java.util.List;

public class CommunityCommand extends Command {
    private final PlayerServerPlugin plugin;
    private final CommunityManager communityManager;

    public CommunityCommand(PlayerServerPlugin plugin, CommunityManager communityManager) {
        super("community", "playerservers.community", "comm");
        this.plugin = plugin;
        this.communityManager = communityManager;
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
            case "create":
                if (args.length < 2) {
                    player.sendMessage(new ComponentBuilder("Usage: /community create <name> [description]")
                        .color(ChatColor.RED).create());
                    return;
                }
                String desc = args.length >= 3 ? args[2] : "";
                for (int i = 3; i < args.length; i++) desc += " " + args[i];
                handleCreate(player, args[1], desc);
                break;
            case "join":
                if (args.length < 2) {
                    player.sendMessage(new ComponentBuilder("Usage: /community join <id>").color(ChatColor.RED).create());
                    return;
                }
                handleJoin(player, args[1]);
                break;
            case "leave":
                if (args.length < 2) {
                    player.sendMessage(new ComponentBuilder("Usage: /community leave <id>").color(ChatColor.RED).create());
                    return;
                }
                handleLeave(player, args[1]);
                break;
            case "list":
                int page = args.length >= 2 ? Integer.parseInt(args[1]) : 1;
                handleList(player, page);
                break;
            case "info":
                if (args.length < 2) {
                    player.sendMessage(new ComponentBuilder("Usage: /community info <id>").color(ChatColor.RED).create());
                    return;
                }
                handleInfo(player, args[1]);
                break;
            case "invite":
                if (args.length < 3) {
                    player.sendMessage(new ComponentBuilder("Usage: /community invite <id> <player>")
                        .color(ChatColor.RED).create());
                    return;
                }
                handleInvite(player, args[1], args[2]);
                break;
            default:
                showHelp(player);
        }
    }

    private void handleCreate(ProxiedPlayer player, String name, String description) {
        if (communityManager.createCommunity(player.getUniqueId(), name, description, true)) {
            player.sendMessage(new ComponentBuilder("Community '" + name + "' created!").color(ChatColor.GREEN).create());
        } else {
            player.sendMessage(new ComponentBuilder("Could not create community. Name taken or limit reached.")
                .color(ChatColor.RED).create());
        }
    }

    private void handleJoin(ProxiedPlayer player, String idStr) {
        int id;
        try {
            id = Integer.parseInt(idStr);
        } catch (NumberFormatException e) {
            player.sendMessage(new ComponentBuilder("Invalid ID!").color(ChatColor.RED).create());
            return;
        }
        if (communityManager.joinCommunity(id, player.getUniqueId())) {
            player.sendMessage(new ComponentBuilder("Joined community!").color(ChatColor.GREEN).create());
        } else {
            player.sendMessage(new ComponentBuilder("Could not join community (full, already member, or doesn't exist).")
                .color(ChatColor.RED).create());
        }
    }

    private void handleLeave(ProxiedPlayer player, String idStr) {
        int id;
        try {
            id = Integer.parseInt(idStr);
        } catch (NumberFormatException e) {
            player.sendMessage(new ComponentBuilder("Invalid ID!").color(ChatColor.RED).create());
            return;
        }
        if (communityManager.leaveCommunity(id, player.getUniqueId())) {
            player.sendMessage(new ComponentBuilder("Left community.").color(ChatColor.GREEN).create());
        } else {
            player.sendMessage(new ComponentBuilder("Could not leave (owner cannot leave).").color(ChatColor.RED).create());
        }
    }

    private void handleList(ProxiedPlayer player, int page) {
        List<Community> communities = communityManager.listCommunities(page, 10);
        player.sendMessage(new ComponentBuilder("=== Communities (Page " + page + ") ===").color(ChatColor.GOLD).create());
        if (communities.isEmpty()) {
            player.sendMessage(new ComponentBuilder("No communities found.").color(ChatColor.GRAY).create());
            return;
        }
        for (Community community : communities) {
            player.sendMessage(new ComponentBuilder(" #" + community.getId() + " " + community.getName())
                .color(ChatColor.YELLOW)
                .append(" | Members: " + community.getMemberCount()).color(ChatColor.GREEN)
                .append(" | Owner: " + community.getOwnerName()).color(ChatColor.WHITE).create());
        }
    }

    private void handleInfo(ProxiedPlayer player, String idStr) {
        int id;
        try {
            id = Integer.parseInt(idStr);
        } catch (NumberFormatException e) {
            player.sendMessage(new ComponentBuilder("Invalid ID!").color(ChatColor.RED).create());
            return;
        }
        Community community = communityManager.getCommunity(id);
        if (community == null) {
            player.sendMessage(new ComponentBuilder("Community not found.").color(ChatColor.RED).create());
            return;
        }
        player.sendMessage(new ComponentBuilder("=== " + community.getName() + " ===").color(ChatColor.GOLD).create());
        player.sendMessage(new ComponentBuilder("Description: ").color(ChatColor.YELLOW)
            .append(community.getDescription() != null ? community.getDescription() : "None")
            .color(ChatColor.WHITE).create());
        player.sendMessage(new ComponentBuilder("Owner: ").color(ChatColor.YELLOW)
            .append(community.getOwnerName()).color(ChatColor.WHITE).create());
        player.sendMessage(new ComponentBuilder("Members: ").color(ChatColor.YELLOW)
            .append(String.valueOf(community.getMemberCount())).color(ChatColor.GREEN).create());
        player.sendMessage(new ComponentBuilder("Public: ").color(ChatColor.YELLOW)
            .append(String.valueOf(community.isPublic())).color(ChatColor.GREEN).create());

        if (community.getMembers() != null) {
            player.sendMessage(new ComponentBuilder("--- Members ---").color(ChatColor.GRAY).create());
            for (CommunityMember member : community.getMembers()) {
                String roleBadge = member.getRole() == Community.MemberRole.owner ? " [OWNER]"
                    : member.getRole() == Community.MemberRole.admin ? " [ADMIN]" : "";
                player.sendMessage(new ComponentBuilder(" - " + member.getPlayerName())
                    .color(ChatColor.YELLOW)
                    .append(roleBadge).color(ChatColor.GOLD).create());
            }
        }
    }

    private void handleInvite(ProxiedPlayer player, String idStr, String targetName) {
        int id;
        try {
            id = Integer.parseInt(idStr);
        } catch (NumberFormatException e) {
            player.sendMessage(new ComponentBuilder("Invalid ID!").color(ChatColor.RED).create());
            return;
        }
        ProxiedPlayer target = plugin.getProxy().getPlayer(targetName);
        if (target == null) {
            player.sendMessage(new ComponentBuilder("Player not found!").color(ChatColor.RED).create());
            return;
        }
        if (communityManager.inviteToCommunity(id, player.getUniqueId(), target.getUniqueId())) {
            player.sendMessage(new ComponentBuilder("Invited " + target.getName() + " to community!")
                .color(ChatColor.GREEN).create());
            target.sendMessage(new ComponentBuilder(player.getName() + " invited you to their community! Use /community join " + id)
                .color(ChatColor.YELLOW).create());
        } else {
            player.sendMessage(new ComponentBuilder("Could not invite. Not a member/admin.").color(ChatColor.RED).create());
        }
    }

    private void showHelp(ProxiedPlayer player) {
        player.sendMessage(new ComponentBuilder("=== Community Commands ===").color(ChatColor.GOLD).create());
        player.sendMessage(new ComponentBuilder("/community create <name> [desc]").color(ChatColor.YELLOW)
            .append(" - Create community").color(ChatColor.WHITE).create());
        player.sendMessage(new ComponentBuilder("/community join <id>").color(ChatColor.YELLOW)
            .append(" - Join community").color(ChatColor.WHITE).create());
        player.sendMessage(new ComponentBuilder("/community leave <id>").color(ChatColor.YELLOW)
            .append(" - Leave community").color(ChatColor.WHITE).create());
        player.sendMessage(new ComponentBuilder("/community list").color(ChatColor.YELLOW)
            .append(" - List communities").color(ChatColor.WHITE).create());
        player.sendMessage(new ComponentBuilder("/community info <id>").color(ChatColor.YELLOW)
            .append(" - View community details").color(ChatColor.WHITE).create());
        player.sendMessage(new ComponentBuilder("/community invite <id> <player>").color(ChatColor.YELLOW)
            .append(" - Invite to community").color(ChatColor.WHITE).create());
    }
}
