package com.playerservers;

import net.md_5.bungee.api.connection.ProxiedPlayer;
import net.md_5.bungee.api.event.PluginMessageEvent;
import net.md_5.bungee.api.plugin.Listener;
import net.md_5.bungee.event.EventHandler;

import java.io.ByteArrayInputStream;
import java.io.DataInputStream;
import java.io.IOException;

public class PluginMessageListener implements Listener {

    private final PlayerServerPlugin plugin;

    public PluginMessageListener(PlayerServerPlugin plugin) {
        this.plugin = plugin;
        plugin.getProxy().registerChannel("PlayerServer:Main");
    }

    @EventHandler
    public void onPluginMessage(PluginMessageEvent event) {
        if (!event.getTag().equals("PlayerServer:Main")) return;

        DataInputStream in = new DataInputStream(new ByteArrayInputStream(event.getData()));
        try {
            String subchannel = in.readUTF();
            if ("BlockBreak".equals(subchannel)) {
                String uuid = in.readUTF();
                plugin.getActivityRewardListener().handleBlockBreak(java.util.UUID.fromString(uuid));
            } else if ("BlockPlace".equals(subchannel)) {
                String uuid = in.readUTF();
                plugin.getActivityRewardListener().handleBlockPlace(java.util.UUID.fromString(uuid));
            } else if ("PlayerKill".equals(subchannel)) {
                String uuid = in.readUTF();
                plugin.getActivityRewardListener().handlePlayerKill(java.util.UUID.fromString(uuid));
            } else if ("MobKill".equals(subchannel)) {
                String uuid = in.readUTF();
                plugin.getActivityRewardListener().handleMobKill(java.util.UUID.fromString(uuid));
            } else if ("FishCatch".equals(subchannel)) {
                String uuid = in.readUTF();
                plugin.getActivityRewardListener().handleFishCatch(java.util.UUID.fromString(uuid));
            } else if ("CraftItem".equals(subchannel)) {
                String uuid = in.readUTF();
                plugin.getActivityRewardListener().handleCraftItem(java.util.UUID.fromString(uuid));
            }
        } catch (IOException e) {
            plugin.getLogger().warning("Failed to read plugin message: " + e.getMessage());
        }
    }
}
