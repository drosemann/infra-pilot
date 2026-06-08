package com.playerservers.features.social;

import com.playerservers.PlayerServerPlugin;
import net.md_5.bungee.api.ChatColor;
import net.md_5.bungee.api.chat.ClickEvent;
import net.md_5.bungee.api.chat.ComponentBuilder;
import net.md_5.bungee.api.chat.TextComponent;
import net.md_5.bungee.api.connection.ProxiedPlayer;

import java.util.UUID;

public class ProfileGUI {
    private final PlayerServerPlugin plugin;
    private final ProfileManager profileManager;

    public ProfileGUI(PlayerServerPlugin plugin, ProfileManager profileManager) {
        this.plugin = plugin;
        this.profileManager = profileManager;
    }

    public void openProfile(ProxiedPlayer viewer, UUID targetUuid) {
        PlayerProfile profile = profileManager.getProfile(targetUuid);

        viewer.sendMessage(new ComponentBuilder("=== " + profile.getPlayerName() + " ===")
            .color(ChatColor.GOLD).create());

        if (profile.getBio() != null && !profile.getBio().isEmpty()) {
            viewer.sendMessage(new ComponentBuilder("\"" + profile.getBio() + "\"").color(ChatColor.ITALIC).create());
        }

        TextComponent servers = new TextComponent("[Servers: " + profile.getServersCreated() + "] ");
        servers.setColor(ChatColor.GREEN);
        servers.setClickEvent(new ClickEvent(ClickEvent.Action.RUN_COMMAND, "/browse search " + profile.getPlayerName()));

        TextComponent friends = new TextComponent("[Friends: " + profile.getFriendsCount() + "] ");
        friends.setColor(ChatColor.YELLOW);

        TextComponent rep = new TextComponent("[Rep: " + profile.getReputationScore() + "]");
        rep.setColor(ChatColor.GOLD);

        viewer.sendMessage(servers, friends, rep);

        if (profile.getWebsite() != null) {
            TextComponent web = new TextComponent("[Website] ");
            web.setColor(ChatColor.BLUE);
            web.setClickEvent(new ClickEvent(ClickEvent.Action.OPEN_URL, profile.getWebsite()));
            viewer.sendMessage(web);
        }

        if (profile.getFriends() != null && !profile.getFriends().isEmpty()) {
            viewer.sendMessage(new ComponentBuilder("Friends:").color(ChatColor.YELLOW).create());
            int count = 0;
            for (Friend friend : profile.getFriends()) {
                if (count >= 5) {
                    viewer.sendMessage(new ComponentBuilder(" ... and " + (profile.getFriends().size() - 5) + " more")
                        .color(ChatColor.GRAY).create());
                    break;
                }
                String status = friend.isFriendOnline() ? " \u25CF ONLINE" : " \u25CB OFFLINE";
                TextComponent fc = new TextComponent(" - " + friend.getFriendName());
                fc.setColor(ChatColor.YELLOW);
                TextComponent sc = new TextComponent(status);
                sc.setColor(friend.isFriendOnline() ? ChatColor.GREEN : ChatColor.GRAY);
                viewer.sendMessage(fc, sc);
                count++;
            }
        }

        TextComponent editProfile = new TextComponent("[Edit Profile]");
        editProfile.setColor(ChatColor.AQUA);
        editProfile.setClickEvent(new ClickEvent(ClickEvent.Action.SUGGEST_COMMAND, "/profile set "));
        viewer.sendMessage(editProfile);
    }
}
