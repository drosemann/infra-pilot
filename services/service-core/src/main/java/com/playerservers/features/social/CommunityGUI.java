package com.playerservers.features.social;

import com.playerservers.PlayerServerPlugin;
import net.md_5.bungee.api.ChatColor;
import net.md_5.bungee.api.chat.ClickEvent;
import net.md_5.bungee.api.chat.ComponentBuilder;
import net.md_5.bungee.api.chat.TextComponent;
import net.md_5.bungee.api.connection.ProxiedPlayer;

import java.util.List;

public class CommunityGUI {
    private final PlayerServerPlugin plugin;
    private final CommunityManager communityManager;

    public CommunityGUI(PlayerServerPlugin plugin, CommunityManager communityManager) {
        this.plugin = plugin;
        this.communityManager = communityManager;
    }

    public void openCommunityList(ProxiedPlayer player, int page) {
        List<Community> communities = communityManager.listCommunities(page, 10);

        player.sendMessage(new ComponentBuilder("=== Communities ===").color(ChatColor.GOLD).create());

        TextComponent create = new TextComponent("[Create Community]");
        create.setColor(ChatColor.GREEN);
        create.setClickEvent(new ClickEvent(ClickEvent.Action.SUGGEST_COMMAND, "/community create "));
        player.sendMessage(create);

        if (communities.isEmpty()) {
            player.sendMessage(new ComponentBuilder("No communities yet.").color(ChatColor.GRAY).create());
            return;
        }

        for (Community community : communities) {
            TextComponent name = new TextComponent("[" + community.getName() + "] ");
            name.setColor(ChatColor.YELLOW);
            name.setClickEvent(new ClickEvent(ClickEvent.Action.RUN_COMMAND, "/community info " + community.getId()));

            TextComponent info = new TextComponent(community.getMemberCount() + " members");
            info.setColor(ChatColor.GREEN);

            player.sendMessage(name, info);
        }
    }

    public void openCommunityInfo(ProxiedPlayer player, int communityId) {
        Community community = communityManager.getCommunity(communityId);
        if (community == null) {
            player.sendMessage(new ComponentBuilder("Community not found.").color(ChatColor.RED).create());
            return;
        }

        player.sendMessage(new ComponentBuilder("=== " + community.getName() + " ===").color(ChatColor.GOLD).create());
        player.sendMessage(new ComponentBuilder(community.getDescription() != null ? community.getDescription() : "")
            .color(ChatColor.WHITE).create());

        TextComponent join = new TextComponent("[Join] ");
        join.setColor(ChatColor.GREEN);
        join.setClickEvent(new ClickEvent(ClickEvent.Action.RUN_COMMAND, "/community join " + communityId));

        TextComponent leave = new TextComponent("[Leave]");
        leave.setColor(ChatColor.RED);
        leave.setClickEvent(new ClickEvent(ClickEvent.Action.RUN_COMMAND, "/community leave " + communityId));

        player.sendMessage(join, leave);

        if (community.getMembers() != null) {
            player.sendMessage(new ComponentBuilder("Members (" + community.getMemberCount() + "):")
                .color(ChatColor.YELLOW).create());
            for (CommunityMember member : community.getMembers()) {
                String badge = member.getRole() == Community.MemberRole.owner ? " [OWNER]"
                    : member.getRole() == Community.MemberRole.admin ? " [ADMIN]" : "";
                TextComponent mc = new TextComponent(" - " + member.getPlayerName());
                mc.setColor(ChatColor.YELLOW);
                TextComponent bc = new TextComponent(badge);
                bc.setColor(ChatColor.GOLD);
                player.sendMessage(mc, bc);
            }
        }
    }
}
