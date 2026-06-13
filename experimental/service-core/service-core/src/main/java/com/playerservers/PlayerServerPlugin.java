package com.playerservers;

import com.playerservers.features.economy.EconomyManager;
import com.playerservers.features.economy.EconomyCommands;
import com.playerservers.features.economy.ActivityRewardListener;
import com.playerservers.features.economy.ShopTaxManager;
import com.playerservers.features.economy.CurrencyExchangeManager;
import com.playerservers.features.economy.MarketManager;
import com.playerservers.features.statistics.PlayerStatistics;
import com.playerservers.features.statistics.StatisticsCommand;
import com.playerservers.features.statistics.AchievementsManager;
import com.playerservers.features.worlds.ResourceWorldManager;
import com.playerservers.features.worlds.WorldCommands;
import com.playerservers.features.worlds.BorderManager;
import com.playerservers.features.items.CustomItemManager;
import com.playerservers.features.items.CustomCraftingManager;
import com.playerservers.features.gameplay.ResourceMultiplierManager;
import com.playerservers.features.gameplay.DeathPenaltyManager;
import com.playerservers.features.gameplay.PlayerTimeWeatherManager;
import com.playerservers.features.gameplay.PlaytimeRewardsManager;
import com.playerservers.features.community.VoteRewardsManager;
import com.playerservers.features.community.ReferralManager;
import com.playerservers.features.server.MaintenanceManager;
import com.playerservers.features.server.ResourceLimitsManager;
import com.playerservers.features.server.AntiCheatManager;
import com.playerservers.features.server.CommandCooldownManager;
import com.playerservers.features.server.PermissionManager;
import com.playerservers.features.server.VIPPerksManager;
import com.playerservers.features.social.*;
import com.playerservers.features.performance.PerformanceProfilerManager;

import net.md_5.bungee.api.plugin.Plugin;

import java.sql.SQLException;

public class PlayerServerPlugin extends Plugin {

    private DatabaseManager databaseManager;
    private ServerManager serverManager;
    private ConfigManager configManager;
    private GUIManager guiManager;
    private EconomyManager economyManager;
    private ActivityRewardListener activityRewardListener;
    private PlayerStatistics playerStatistics;
    private ResourceWorldManager resourceWorldManager;
    private BorderManager borderManager;
    private ShopTaxManager shopTaxManager;
    private CurrencyExchangeManager currencyExchangeManager;
    private MarketManager marketManager;
    private AchievementsManager achievementsManager;
    private CustomItemManager customItemManager;
    private CustomCraftingManager customCraftingManager;
    private ResourceMultiplierManager resourceMultiplierManager;
    private DeathPenaltyManager deathPenaltyManager;
    private PlayerTimeWeatherManager playerTimeWeatherManager;
    private PlaytimeRewardsManager playtimeRewardsManager;
    private VoteRewardsManager voteRewardsManager;
    private ReferralManager referralManager;
    private MaintenanceManager maintenanceManager;
    private ResourceLimitsManager resourceLimitsManager;
    private AntiCheatManager antiCheatManager;
    private CommandCooldownManager commandCooldownManager;
    private PermissionManager permissionManager;
    private VIPPerksManager vipPerksManager;
    private PerformanceProfilerManager performanceProfilerManager;
    private FriendManager friendManager;
    private InvitationManager invitationManager;
    private ServerDiscoveryManager serverDiscoveryManager;
    private ReviewManager reviewManager;
    private ProfileManager profileManager;
    private MessageManager messageManager;
    private CommunityManager communityManager;
    private ActivityManager activityManager;
    private InactivityShutdownTask inactivityShutdown;

    @Override
    public void onEnable() {
        configManager = new ConfigManager(this);
        configManager.loadConfig();

        databaseManager = new DatabaseManager(this);
        try {
            databaseManager.connect();
            databaseManager.setupDatabase();
        } catch (SQLException e) {
            getLogger().severe("Failed to connect to database: " + e.getMessage());
            return;
        }

        serverManager = new ServerManager(this);
        guiManager = new GUIManager(this);

        economyManager = new EconomyManager(this);
        activityRewardListener = new ActivityRewardListener(this, economyManager);
        playerStatistics = new PlayerStatistics(this);
        resourceWorldManager = new ResourceWorldManager(this);
        borderManager = new BorderManager(this);
        shopTaxManager = new ShopTaxManager(this, economyManager);
        currencyExchangeManager = new CurrencyExchangeManager(this, economyManager);
        marketManager = new MarketManager(this, economyManager);
        achievementsManager = new AchievementsManager(this);
        customItemManager = new CustomItemManager(this);
        customCraftingManager = new CustomCraftingManager(this, customItemManager);
        resourceMultiplierManager = new ResourceMultiplierManager(this);
        deathPenaltyManager = new DeathPenaltyManager(this, economyManager);
        playerTimeWeatherManager = new PlayerTimeWeatherManager(this);
        playtimeRewardsManager = new PlaytimeRewardsManager(this);
        voteRewardsManager = new VoteRewardsManager(this, economyManager);
        referralManager = new ReferralManager(this, economyManager);
        maintenanceManager = new MaintenanceManager(this);
        resourceLimitsManager = new ResourceLimitsManager(this);
        antiCheatManager = new AntiCheatManager(this);
        commandCooldownManager = new CommandCooldownManager(this);
        permissionManager = new PermissionManager(this);
        vipPerksManager = new VIPPerksManager(this);
        performanceProfilerManager = new PerformanceProfilerManager(this);
        friendManager = new FriendManager(this);
        invitationManager = new InvitationManager(this);
        serverDiscoveryManager = new ServerDiscoveryManager(this);
        reviewManager = new ReviewManager(this, economyManager);
        messageManager = new MessageManager(this, friendManager);
        communityManager = new CommunityManager(this);
        activityManager = new ActivityManager(this, friendManager);
        profileManager = new ProfileManager(this, friendManager, playerStatistics);
        inactivityShutdown = new InactivityShutdownTask(this);

        getProxy().getPluginManager().registerCommand(this, new ServerCommand(this));
        new EconomyCommands(this, economyManager);
        new StatisticsCommand(this, playerStatistics);
        new WorldCommands(this, resourceWorldManager, borderManager);
        new com.playerservers.features.economy.ShopTaxManager.ShopTaxCommands(this, shopTaxManager);
        new com.playerservers.features.economy.CurrencyExchangeManager.CurrencyCommands(this, currencyExchangeManager);
        new com.playerservers.features.economy.MarketManager.MarketCommands(this, marketManager);
        new com.playerservers.features.statistics.AchievementsManager.AchievementCommands(this, achievementsManager);
        new com.playerservers.features.items.CustomItemManager.CustomItemCommands(this, customItemManager);
        new com.playerservers.features.items.CustomCraftingManager.CraftingCommands(this, customCraftingManager);
        new com.playerservers.features.gameplay.ResourceMultiplierManager.MultiplierCommands(this, resourceMultiplierManager);
        new com.playerservers.features.gameplay.PlayerTimeWeatherManager.PlayerTimeCommands(this, playerTimeWeatherManager);
        new com.playerservers.features.gameplay.PlaytimeRewardsManager.PlaytimeCommands(this, playtimeRewardsManager);
        new com.playerservers.features.community.VoteRewardsManager.VoteCommands(this, voteRewardsManager);
        new com.playerservers.features.community.ReferralManager.ReferralCommands(this, referralManager);
        new com.playerservers.features.server.MaintenanceManager.MaintenanceCommands(this, maintenanceManager);
        new com.playerservers.features.server.ResourceLimitsManager.LimitCommands(this, resourceLimitsManager);
        new com.playerservers.features.server.CommandCooldownManager.CooldownCommands(this, commandCooldownManager);
        new com.playerservers.features.server.PermissionManager.PermissionCommands(this, permissionManager);
        new com.playerservers.features.server.VIPPerksManager.VIPCommands(this, vipPerksManager);
        getProxy().getPluginManager().registerCommand(this, new VIPPerksManager.VIPCommands.VIPAdminCommands(vipPerksManager));
        new PerformanceProfilerManager.PerformanceCommand(this, performanceProfilerManager);

        getProxy().getPluginManager().registerCommand(this, new FriendCommand(this, friendManager));
        getProxy().getPluginManager().registerCommand(this, new InvitationCommand(this, invitationManager));
        getProxy().getPluginManager().registerCommand(this, new DiscoveryCommand(this, serverDiscoveryManager));
        getProxy().getPluginManager().registerCommand(this, new ReviewCommand(this, reviewManager));
        getProxy().getPluginManager().registerCommand(this, new ProfileCommand(this, profileManager));
        getProxy().getPluginManager().registerCommand(this, new MessageCommand(this, messageManager));
        getProxy().getPluginManager().registerCommand(this, new CommunityCommand(this, communityManager));
        getProxy().getPluginManager().registerCommand(this, new ActivityCommand(this, activityManager));

        getProxy().getPluginManager().registerListener(this, activityRewardListener);
        getProxy().getPluginManager().registerListener(this, new PluginMessageListener(this));
        getProxy().getPluginManager().registerListener(this, inactivityShutdown);

        getLogger().info("PlayerServerPlugin has been enabled!");
    }

    @Override
    public void onDisable() {
        if (economyManager != null) economyManager.saveAllBalances();
        if (playerStatistics != null) playerStatistics.cleanup();
        if (databaseManager != null) databaseManager.disconnect();
        getLogger().info("PlayerServerPlugin has been disabled!");
    }

    public DatabaseManager getDatabaseManager() { return databaseManager; }
    public ServerManager getServerManager() { return serverManager; }
    public ConfigManager getConfigManager() { return configManager; }
    public GUIManager getGuiManager() { return guiManager; }
    public EconomyManager getEconomyManager() { return economyManager; }
    public ActivityRewardListener getActivityRewardListener() { return activityRewardListener; }
    public PlayerStatistics getPlayerStatistics() { return playerStatistics; }
    public ResourceWorldManager getResourceWorldManager() { return resourceWorldManager; }
    public BorderManager getBorderManager() { return borderManager; }
    public ShopTaxManager getShopTaxManager() { return shopTaxManager; }
    public CurrencyExchangeManager getCurrencyExchangeManager() { return currencyExchangeManager; }
    public MarketManager getMarketManager() { return marketManager; }
    public AchievementsManager getAchievementsManager() { return achievementsManager; }
    public CustomItemManager getCustomItemManager() { return customItemManager; }
    public CustomCraftingManager getCustomCraftingManager() { return customCraftingManager; }
    public ResourceMultiplierManager getResourceMultiplierManager() { return resourceMultiplierManager; }
    public DeathPenaltyManager getDeathPenaltyManager() { return deathPenaltyManager; }
    public PlayerTimeWeatherManager getPlayerTimeWeatherManager() { return playerTimeWeatherManager; }
    public PlaytimeRewardsManager getPlaytimeRewardsManager() { return playtimeRewardsManager; }
    public VoteRewardsManager getVoteRewardsManager() { return voteRewardsManager; }
    public ReferralManager getReferralManager() { return referralManager; }
    public MaintenanceManager getMaintenanceManager() { return maintenanceManager; }
    public ResourceLimitsManager getResourceLimitsManager() { return resourceLimitsManager; }
    public AntiCheatManager getAntiCheatManager() { return antiCheatManager; }
    public CommandCooldownManager getCommandCooldownManager() { return commandCooldownManager; }
    public PermissionManager getPermissionManager() { return permissionManager; }
    public VIPPerksManager getVipPerksManager() { return vipPerksManager; }
    public PerformanceProfilerManager getPerformanceProfilerManager() { return performanceProfilerManager; }
    public FriendManager getFriendManager() { return friendManager; }
    public InvitationManager getInvitationManager() { return invitationManager; }
    public ServerDiscoveryManager getServerDiscoveryManager() { return serverDiscoveryManager; }
    public ReviewManager getReviewManager() { return reviewManager; }
    public ProfileManager getProfileManager() { return profileManager; }
    public MessageManager getMessageManager() { return messageManager; }
    public CommunityManager getCommunityManager() { return communityManager; }
    public ActivityManager getActivityManager() { return activityManager; }
}
