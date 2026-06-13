package com.playerservers.features.economy;

import com.playerservers.PlayerServerPlugin;
import net.md_5.bungee.api.ChatColor;
import net.md_5.bungee.api.chat.ComponentBuilder;
import net.md_5.bungee.api.connection.ProxiedPlayer;
import net.md_5.bungee.api.event.PlayerDisconnectEvent;
import net.md_5.bungee.api.event.PostLoginEvent;
import net.md_5.bungee.api.plugin.Listener;
import net.md_5.bungee.event.EventHandler;

import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.TimeUnit;

public class ActivityRewardListener implements Listener {
    private final PlayerServerPlugin plugin;
    private final EconomyManager economyManager;
    private final Map<UUID, Long> playerPlaytime;
    private final Map<UUID, Long> lastRewardTime;

    public ActivityRewardListener(PlayerServerPlugin plugin, EconomyManager economyManager) {
        this.plugin = plugin;
        this.economyManager = economyManager;
        this.playerPlaytime = new ConcurrentHashMap<>();
        this.lastRewardTime = new ConcurrentHashMap<>();
        
        startPlaytimeTracker();
    }

    private void startPlaytimeTracker() {
        plugin.getProxy().getScheduler().schedule(plugin, () -> {
            long currentTime = System.currentTimeMillis();
            
            // Check each online player's playtime
            for (ProxiedPlayer player : plugin.getProxy().getPlayers()) {
                UUID uuid = player.getUniqueId();
                long loginTime = playerPlaytime.getOrDefault(uuid, currentTime);
                long lastReward = lastRewardTime.getOrDefault(uuid, loginTime);
                
                // Check if an hour has passed since last reward
                if (currentTime - lastReward >= TimeUnit.HOURS.toMillis(1)) {
                    // Award playtime reward
                    economyManager.rewardActivity(uuid, "PLAYTIME_HOUR");
                    lastRewardTime.put(uuid, currentTime);
                    
                    // Notify player
                    player.sendMessage(new ComponentBuilder("You earned money for playing for an hour!")
                        .color(ChatColor.GREEN).create());
                }
            }
        }, 1, 1, TimeUnit.MINUTES); // Check every minute
    }

    @EventHandler
    public void onPlayerJoin(PostLoginEvent event) {
        ProxiedPlayer player = event.getPlayer();
        playerPlaytime.put(player.getUniqueId(), System.currentTimeMillis());
        lastRewardTime.put(player.getUniqueId(), System.currentTimeMillis());
    }

    @EventHandler
    public void onPlayerQuit(PlayerDisconnectEvent event) {
        ProxiedPlayer player = event.getPlayer();
        UUID uuid = player.getUniqueId();
        
        // Calculate final playtime and cleanup
        long loginTime = playerPlaytime.getOrDefault(uuid, System.currentTimeMillis());
        long playtime = System.currentTimeMillis() - loginTime;
        
        // Award any remaining playtime rewards
        long hours = TimeUnit.MILLISECONDS.toHours(playtime);
        long lastReward = lastRewardTime.getOrDefault(uuid, loginTime);
        long hoursSinceLastReward = TimeUnit.MILLISECONDS.toHours(System.currentTimeMillis() - lastReward);
        
        if (hoursSinceLastReward > 0) {
            economyManager.rewardActivity(uuid, "PLAYTIME_HOUR");
        }
        
        // Cleanup
        playerPlaytime.remove(uuid);
        lastRewardTime.remove(uuid);
    }
    
    // Additional activity reward methods can be added here for other events
    // These would be called from the respective event listeners in the main plugin
    
    public void handleBlockBreak(UUID uuid) {
        economyManager.rewardActivity(uuid, "BLOCK_BREAK");
    }
    
    public void handleBlockPlace(UUID uuid) {
        economyManager.rewardActivity(uuid, "BLOCK_PLACE");
    }
    
    public void handlePlayerKill(UUID uuid) {
        economyManager.rewardActivity(uuid, "PLAYER_KILL");
    }
    
    public void handleMobKill(UUID uuid) {
        economyManager.rewardActivity(uuid, "MOB_KILL");
    }
    
    public void handleFishCatch(UUID uuid) {
        economyManager.rewardActivity(uuid, "FISH_CATCH");
    }
    
    public void handleCraftItem(UUID uuid) {
        economyManager.rewardActivity(uuid, "CRAFT_ITEM");
    }
    
    public void handleVote(UUID uuid) {
        economyManager.rewardActivity(uuid, "VOTE");
        
        // Send notification to player if online
        ProxiedPlayer player = plugin.getProxy().getPlayer(uuid);
        if (player != null) {
            player.sendMessage(new ComponentBuilder("Thanks for voting! You received a reward!")
                .color(ChatColor.GREEN).create());
        }
    }
    
    /**
     * Get a player's current session playtime in milliseconds
     */
    public long getPlayerPlaytime(UUID uuid) {
        Long loginTime = playerPlaytime.get(uuid);
        if (loginTime == null) {
            return 0;
        }
        return System.currentTimeMillis() - loginTime;
    }
    
    /**
     * Get time until next playtime reward in milliseconds
     */
    public long getTimeUntilNextReward(UUID uuid) {
        Long lastReward = lastRewardTime.get(uuid);
        if (lastReward == null) {
            return 0;
        }
        long timeSinceLastReward = System.currentTimeMillis() - lastReward;
        return Math.max(0, TimeUnit.HOURS.toMillis(1) - timeSinceLastReward);
    }
}