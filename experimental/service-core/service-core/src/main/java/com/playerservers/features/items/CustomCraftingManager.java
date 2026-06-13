package com.playerservers.features.items;

import com.playerservers.PlayerServerPlugin;
import net.md_5.bungee.api.ChatColor;
import net.md_5.bungee.api.CommandSender;
import net.md_5.bungee.api.chat.ComponentBuilder;
import net.md_5.bungee.api.plugin.Command;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.logging.Level;

public class CustomCraftingManager {

    private final PlayerServerPlugin plugin;
    private final CustomItemManager customItemManager;
    private final Map<String, RecipeDef> recipes;

    public CustomCraftingManager(PlayerServerPlugin plugin, CustomItemManager customItemManager) {
        this.plugin = plugin;
        this.customItemManager = customItemManager;
        this.recipes = new ConcurrentHashMap<>();
        initDatabase();
    }

    private void initDatabase() {
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            conn.createStatement().execute("CREATE TABLE IF NOT EXISTS custom_recipes (" +
                "recipe_id VARCHAR(64) PRIMARY KEY," +
                "result_id VARCHAR(64)," +
                "result_count INT DEFAULT 1," +
                "ingredients TEXT," +
                "permission VARCHAR(128)," +
                "description TEXT" +
                ")");
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to init recipes DB", e);
        }
    }

    public void addRecipe(String id, String resultId, int count, String ingredients, String permission) {
        recipes.put(id, new RecipeDef(id, resultId, count, ingredients, permission));
        try (Connection conn = plugin.getDatabaseManager().getConnection()) {
            PreparedStatement stmt = conn.prepareStatement(
                "INSERT OR REPLACE INTO custom_recipes (recipe_id, result_id, result_count, ingredients, permission) VALUES (?,?,?,?,?)");
            stmt.setString(1, id);
            stmt.setString(2, resultId);
            stmt.setInt(3, count);
            stmt.setString(4, ingredients);
            stmt.setString(5, permission);
            stmt.executeUpdate();
        } catch (SQLException e) {
            plugin.getLogger().log(Level.SEVERE, "Failed to save recipe", e);
        }
    }

    public List<RecipeDef> getAvailableRecipes(UUID player) {
        List<RecipeDef> available = new ArrayList<>();
        for (RecipeDef recipe : recipes.values()) {
            if (recipe.permission == null || recipe.permission.isEmpty() ||
                plugin.getProxy().getPlayer(player) == null ||
                plugin.getProxy().getPlayer(player).hasPermission(recipe.permission)) {
                available.add(recipe);
            }
        }
        return available;
    }

    public static class RecipeDef {
        public final String id;
        public final String resultId;
        public final int count;
        public final String ingredients;
        public final String permission;

        public RecipeDef(String id, String resultId, int count, String ingredients, String permission) {
            this.id = id; this.resultId = resultId; this.count = count;
            this.ingredients = ingredients; this.permission = permission;
        }
    }

    public static class CraftingCommands {
        private final PlayerServerPlugin plugin;
        private final CustomCraftingManager manager;

        public CraftingCommands(PlayerServerPlugin plugin, CustomCraftingManager manager) {
            this.plugin = plugin;
            this.manager = manager;
            plugin.getProxy().getPluginManager().registerCommand(plugin, new CraftingCommand());
            plugin.getProxy().getPluginManager().registerCommand(plugin, new RecipeAdminCommand());
        }

        private class CraftingCommand extends Command {
            public CraftingCommand() { super("craft", "playerservers.craft"); }

            @Override
            public void execute(CommandSender sender, String[] args) {
                sender.sendMessage(new ComponentBuilder("=== Available Recipes ===").color(ChatColor.GOLD).create());
                for (RecipeDef recipe : manager.recipes.values()) {
                    sender.sendMessage(new ComponentBuilder(recipe.id).color(ChatColor.YELLOW)
                        .append(" -> " + recipe.resultId + " x" + recipe.count).color(ChatColor.GREEN)
                        .append(" [" + recipe.ingredients + "]").color(ChatColor.GRAY).create());
                }
            }
        }

        private class RecipeAdminCommand extends Command {
            public RecipeAdminCommand() { super("recipeadmin", "playerservers.craft.admin"); }

            @Override
            public void execute(CommandSender sender, String[] args) {
                if (args.length >= 5 && "add".equalsIgnoreCase(args[0])) {
                    int count;
                    try {
                        count = Integer.parseInt(args[3]);
                    } catch (NumberFormatException e) {
                        sender.sendMessage(new ComponentBuilder("Usage: /recipeadmin add <id> <result> <count> <ingredients> [perm]")
                            .color(ChatColor.RED).create());
                        return;
                    }
                    String perm = args.length >= 6 ? args[5] : "";
                    manager.addRecipe(args[1], args[2], count, args[4], perm);
                    sender.sendMessage(new ComponentBuilder("Recipe added!").color(ChatColor.GREEN).create());
                } else {
                    sender.sendMessage(new ComponentBuilder("Usage: /recipeadmin add <id> <result> <count> <ingredients> [perm]")
                        .color(ChatColor.RED).create());
                }
            }
        }
    }
}
