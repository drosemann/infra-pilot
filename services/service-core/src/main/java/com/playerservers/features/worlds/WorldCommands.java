package com.playerservers.features.worlds;

import com.playerservers.PlayerServerPlugin;
import net.md_5.bungee.api.ChatColor;
import net.md_5.bungee.api.CommandSender;
import net.md_5.bungee.api.chat.ComponentBuilder;
import net.md_5.bungee.api.connection.ProxiedPlayer;
import net.md_5.bungee.api.plugin.Command;

public class WorldCommands {

    private final PlayerServerPlugin plugin;
    private final ResourceWorldManager resourceWorldManager;

    public WorldCommands(PlayerServerPlugin plugin, ResourceWorldManager resourceWorldManager, BorderManager borderManager) {
        this.plugin = plugin;
        this.resourceWorldManager = resourceWorldManager;
        plugin.getProxy().getPluginManager().registerCommand(plugin, new ResWorldCommand());
        new BorderManager.BorderCommands(plugin, borderManager);
    }

    private class ResWorldCommand extends Command {
        public ResWorldCommand() { super("resworld", "playerservers.resworld"); }

        @Override
        public void execute(CommandSender sender, String[] args) {
            if (args.length == 0) {
                if (sender instanceof ProxiedPlayer) {
                    ProxiedPlayer player = (ProxiedPlayer) sender;
                    if (plugin.getProxy().getServerInfo("resource_world") != null) {
                        player.connect(plugin.getProxy().getServerInfo("resource_world"));
                    } else {
                        player.sendMessage(new ComponentBuilder("Resource world not available").color(ChatColor.RED).create());
                    }
                }
                return;
            }

            if ("regenerate".equalsIgnoreCase(args[0]) && sender.hasPermission("playerservers.resworld.regenerate")) {
                resourceWorldManager.regenerateWorld();
                sender.sendMessage(new ComponentBuilder("Resource world regeneration started").color(ChatColor.GREEN).create());
            } else if ("info".equalsIgnoreCase(args[0])) {
                sender.sendMessage(new ComponentBuilder("Resource world: ").color(ChatColor.YELLOW)
                    .append(resourceWorldManager.getWorldName()).color(ChatColor.GREEN).create());
                sender.sendMessage(new ComponentBuilder("Regenerating: ").color(ChatColor.YELLOW)
                    .append(String.valueOf(resourceWorldManager.isRegenerating())).color(
                        resourceWorldManager.isRegenerating() ? ChatColor.RED : ChatColor.GREEN).create());
            }
        }
    }
}
