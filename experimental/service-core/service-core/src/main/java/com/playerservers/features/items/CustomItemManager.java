package com.playerservers.features.items;

import com.playerservers.PlayerServerPlugin;
import net.md_5.bungee.api.ChatColor;
import net.md_5.bungee.api.CommandSender;
import net.md_5.bungee.api.chat.ComponentBuilder;
import net.md_5.bungee.api.connection.ProxiedPlayer;
import net.md_5.bungee.api.plugin.Command;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.logging.Level;

public class CustomItemManager {

    private final PlayerServerPlugin plugin;
    private final Map<String, CustomItemDef> itemRegistry;
    private final Map<UUID, Map<String, Integer>> playerDurability;

    public CustomItemManager(PlayerServerPlugin plugin) {
        this.plugin = plugin;
        this.itemRegistry = new ConcurrentHashMap<>();
        this.playerDurability = new ConcurrentHashMap<>();
        initDatabase();
    }

    private void initDatabase() {
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            conn.createStatement().execute("CREATE TABLE IF NOT EXISTS custom_items (" +
                "item_id VARCHAR(64) PRIMARY KEY," +
                "display_name VARCHAR(128)," +
                "material VARCHAR(64)," +
                "lore TEXT," +
                "max_durability INT DEFAULT -1," +
                "enchantments TEXT" +
                ")");
            conn.createStatement().execute("CREATE TABLE IF NOT EXISTS item_durability (" +
                "uuid VARCHAR(36), item_id VARCHAR(64), durability INT, " +
                "PRIMARY KEY (uuid, item_id))");
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to init custom items DB", e);
        }
    }

    public void registerItem(String id, String displayName, String material, int maxDurability) {
        itemRegistry.put(id, new CustomItemDef(id, displayName, material, maxDurability));
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "INSERT OR REPLACE INTO custom_items (item_id, display_name, material, max_durability) VALUES (?,?,?,?)");
            stmt.setString(1, id);
            stmt.setString(2, displayName);
            stmt.setString(3, material);
            stmt.setInt(4, maxDurability);
            stmt.executeUpdate();
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to register item", e);
        }
    }

    public int getDurability(UUID player, String itemId) {
        return playerDurability.computeIfAbsent(player, k -> new ConcurrentHashMap<>())
            .getOrDefault(itemId, getMaxDurability(itemId));
    }

    public void damageItem(UUID player, String itemId, int amount) {
        Map<String, Integer> dura = playerDurability.computeIfAbsent(player, k -> new ConcurrentHashMap<>());
        int current = dura.getOrDefault(itemId, getMaxDurability(itemId));
        int damaged = Math.max(0, current - amount);
        dura.put(itemId, damaged);
        saveDurability(player, itemId, damaged);
    }

    public boolean repairItem(UUID player, String itemId, int amount) {
        int current = getDurability(player, itemId);
        int max = getMaxDurability(itemId);
        int repaired = Math.min(max, current + amount);
        playerDurability.getOrDefault(player, new ConcurrentHashMap<>()).put(itemId, repaired);
        saveDurability(player, itemId, repaired);
        return repaired == max;
    }

    public boolean isBroken(UUID player, String itemId) {
        return getDurability(player, itemId) <= 0;
    }

    public int getMaxDurability(String itemId) {
        CustomItemDef def = itemRegistry.get(itemId);
        return def != null ? def.maxDurability : -1;
    }

    private void saveDurability(UUID player, String itemId, int durability) {
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "INSERT OR REPLACE INTO item_durability (uuid, item_id, durability) VALUES (?,?,?)");
            stmt.setString(1, player.toString());
            stmt.setString(2, itemId);
            stmt.setInt(3, durability);
            stmt.executeUpdate();
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to save durability", e);
        }
    }

    public static class CustomItemDef {
        public final String id;
        public final String displayName;
        public final String material;
        public final int maxDurability;

        public CustomItemDef(String id, String displayName, String material, int maxDurability) {
            this.id = id; this.displayName = displayName; this.material = material; this.maxDurability = maxDurability;
        }
    }

    public static class CustomItemCommands {
        private final PlayerServerPlugin plugin;
        private final CustomItemManager manager;

        public CustomItemCommands(PlayerServerPlugin plugin, CustomItemManager manager) {
            this.plugin = plugin;
            this.manager = manager;
            plugin.getProxy().getPluginManager().registerCommand(plugin, new CustomItemAdminCommand());
        }

        private class CustomItemAdminCommand extends Command {
            public CustomItemAdminCommand() { super("customitem", "playerservers.customitem.admin", "citem"); }

            @Override
            public void execute(CommandSender sender, String[] args) {
                if (args.length >= 5 && "register".equalsIgnoreCase(args[0])) {
                    try {
                        int dura = Integer.parseInt(args[4]);
                        manager.registerItem(args[1], args[2], args[3], dura);
                        sender.sendMessage(new ComponentBuilder("Registered custom item: " + args[1])
                            .color(ChatColor.GREEN).create());
                    } catch (NumberFormatException e) {
                        sender.sendMessage(new ComponentBuilder("Usage: /customitem register <id> <name> <material> <durability>")
                            .color(ChatColor.RED).create());
                    }
                } else {
                    sender.sendMessage(new ComponentBuilder("Usage: /customitem register <id> <name> <material> <durability>")
                        .color(ChatColor.RED).create());
                }
            }
        }
    }
}
