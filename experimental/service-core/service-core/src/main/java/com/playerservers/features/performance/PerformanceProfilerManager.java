package com.playerservers.features.performance;

import com.playerservers.PlayerServerPlugin;
import com.playerservers.features.server.AntiCheatManager;
import net.md_5.bungee.api.ChatColor;
import net.md_5.bungee.api.CommandSender;
import net.md_5.bungee.api.chat.ComponentBuilder;
import net.md_5.bungee.api.connection.ProxiedPlayer;
import net.md_5.bungee.api.plugin.Command;
import net.md_5.bungee.api.scheduler.ScheduledTask;

import java.util.*;
import java.util.concurrent.ConcurrentLinkedDeque;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicLong;

public class PerformanceProfilerManager {

    private final PlayerServerPlugin plugin;
    private final AtomicBoolean profilingEnabled;
    private final Deque<TickSnapshot> history;
    private final int historyLength;
    private final long slowTickThreshold;
    private ScheduledTask profilingTask;

    private final Map<String, Long> entityCounts;
    private final Map<String, Long> redstoneCounts;
    private final Map<String, Long> pluginTimings;
    private final Map<String, Long> chunkCounts;
    private final List<ProfileSnapshot> snapshots;
    private final List<Suggestion> suggestions;

    private static final String[] SUGGESTION_PATTERNS = {
        "High entity density detected in %s (%d entities). Consider reducing mob farms or using entity stacking.",
        "Redstone activity spike in %s (%d updates/tick). Use repeaters to spread loads or optimize clocks.",
        "Plugin %s is taking %dms/tick. Consider optimizing or replacing this plugin.",
        "Chunk usage in %s is at %d chunks. Reduce render distance or optimize terrain generation.",
        "Tick time of %dms exceeds threshold. Check for lag-inducing redstone or entities.",
        "Memory usage at %d MB. Consider allocating more RAM to the server.",
        "High player count in %s (%d players). Distribute players across servers.",
        "Frequent garbage collection detected. Add JVM flags: -XX:+UseG1GC -XX:MaxGCPauseMillis=50",
        "World %s has %d loaded chunks. Consider pre-generating or trimming unused chunks.",
        "Hopper lag detected in %s. Limit hopper chains to 3 or use cooldown timers.",
        "Minecart entity count high in %s. Replace with velocity-based teleportation.",
        "Spigot/Bukkit tile entity tick rate high. Increase entity-activation-range in spigot.yml.",
        "Villager AI causing lag in %s. Reduce villager count or use performance-friendly AI.",
        "Falling block entities detected. Prevent sand/gravel duplication machines.",
        "Large item frames (>50) in %s. Reduce or replace with maps.",
        "Brewing stand activity high. Consolidate brewing operations.",
        "Beam render distance causing lag. Reduce beacon range in bukkit.yml.",
        "Piston activity spike. Limit piston chain length and clock speed.",
        "Water flow lag detected. Use water logging prevention or limit flowing water.",
        "Nether portal lag. Limit portal-based chunk loading or use portal cooldowns."
    };

    public PerformanceProfilerManager(PlayerServerPlugin plugin) {
        this.plugin = plugin;
        this.profilingEnabled = new AtomicBoolean(false);
        this.historyLength = plugin.getConfigManager().getInt("performance_profiler.history_length", 1200);
        this.slowTickThreshold = plugin.getConfigManager().getLong("performance_profiler.slow_tick_threshold_ms", 50);
        this.history = new ConcurrentLinkedDeque<>();
        this.entityCounts = new HashMap<>();
        this.redstoneCounts = new HashMap<>();
        this.pluginTimings = new HashMap<>();
        this.chunkCounts = new HashMap<>();
        this.snapshots = new ArrayList<>();
        this.suggestions = new ArrayList<>();
        startBackgroundProfiling();
    }

    public boolean isProfilingEnabled() { return profilingEnabled.get(); }

    public void startProfiling() {
        profilingEnabled.set(true);
        plugin.getProxy().broadcast(new ComponentBuilder("[Profiler] Performance profiling started.")
            .color(ChatColor.GREEN).create());
    }

    public void stopProfiling() {
        profilingEnabled.set(false);
        plugin.getProxy().broadcast(new ComponentBuilder("[Profiler] Performance profiling stopped.")
            .color(ChatColor.YELLOW).create());
    }

    private void startBackgroundProfiling() {
        profilingTask = plugin.getProxy().getScheduler().schedule(plugin, () -> {
            if (!profilingEnabled.get()) return;
            captureSnapshot();
        }, 20, 20, TimeUnit.SECONDS);
    }

    public void recordTick(long durationNs) {
        if (!profilingEnabled.get()) return;

        long durationMs = durationNs / 1_000_000;
        TickSnapshot snapshot = new TickSnapshot(durationMs, System.currentTimeMillis());
        history.addLast(snapshot);
        if (history.size() > historyLength) {
            history.pollFirst();
        }

        if (durationMs > slowTickThreshold) {
            AntiCheatManager antiCheat = plugin.getAntiCheatManager();
            if (antiCheat != null) {
                for (ProxiedPlayer player : plugin.getProxy().getPlayers()) {
                    antiCheat.reportAlert(player.getUniqueId(), "LAG_SPIKE", (float) durationMs / slowTickThreshold);
                }
            }
        }
    }

    public void recordEntityCount(String world, long count) {
        entityCounts.put(world, count);
        if (count > plugin.getConfigManager().getInt("limits.max_entities_per_server", 200)) {
            suggestions.add(new Suggestion("entity", String.format(SUGGESTION_PATTERNS[0], world, count), "HIGH"));
        }
    }

    public void recordRedstoneActivity(String world, long updates) {
        redstoneCounts.put(world, updates);
        if (updates > 100) {
            suggestions.add(new Suggestion("redstone", String.format(SUGGESTION_PATTERNS[1], world, updates), "HIGH"));
        }
    }

    public void recordPluginTiming(String pluginName, long timeMs) {
        pluginTimings.put(pluginName, timeMs);
        if (timeMs > 10) {
            suggestions.add(new Suggestion("plugin", String.format(SUGGESTION_PATTERNS[2], pluginName, timeMs), "MEDIUM"));
        }
    }

    public void recordChunkCount(String world, long count) {
        chunkCounts.put(world, count);
        if (count > plugin.getConfigManager().getInt("limits.max_chunks_per_server", 400)) {
            suggestions.add(new Suggestion("chunks", String.format(SUGGESTION_PATTERNS[3], world, count), "MEDIUM"));
        }
    }

    private void captureSnapshot() {
        ProfileSnapshot snapshot = new ProfileSnapshot(
            System.currentTimeMillis(),
            new HashMap<>(entityCounts),
            new HashMap<>(redstoneCounts),
            new HashMap<>(pluginTimings),
            new HashMap<>(chunkCounts),
            history.isEmpty() ? 0 : history.getLast().durationMs,
            Runtime.getRuntime().totalMemory() - Runtime.getRuntime().freeMemory()
        );
        snapshots.add(snapshot);
        if (snapshots.size() > historyLength) {
            snapshots.remove(0);
        }
        suggestions.clear();
    }

    public String generateReport() {
        StringBuilder report = new StringBuilder();
        report.append("=== Performance Profiler Report ===\n\n");

        if (history.isEmpty()) {
            report.append("No profiling data collected yet.\n");
            return report.toString();
        }

        long totalTicks = history.size();
        long slowTicks = history.stream().filter(t -> t.durationMs > slowTickThreshold).count();
        double avgTick = history.stream().mapToLong(t -> t.durationMs).average().orElse(0);
        long maxTick = history.stream().mapToLong(t -> t.durationMs).max().orElse(0);
        double slowPercent = totalTicks > 0 ? (slowTicks * 100.0 / totalTicks) : 0;

        report.append(String.format("Tick Statistics:\n"));
        report.append(String.format("  Average Tick: %.2f ms\n", avgTick));
        report.append(String.format("  Max Tick: %d ms\n", maxTick));
        report.append(String.format("  Slow Ticks (>%dms): %d (%.1f%%)\n", slowTickThreshold, slowTicks, slowPercent));
        report.append("\n");

        if (!entityCounts.isEmpty()) {
            report.append("Entity Counts by World:\n");
            entityCounts.forEach((w, c) -> report.append(String.format("  %s: %d entities\n", w, c)));
        }

        if (!pluginTimings.isEmpty()) {
            report.append("\nPlugin Timings:\n");
            pluginTimings.entrySet().stream()
                .sorted(Map.Entry.<String, Long>comparingByValue().reversed())
                .limit(10)
                .forEach(e -> report.append(String.format("  %s: %d ms\n", e.getKey(), e.getValue())));
        }

        return report.toString();
    }

    public List<Map<String, Object>> getFlameGraphData() {
        List<Map<String, Object>> flameData = new ArrayList<>();
        long now = System.currentTimeMillis();
        for (TickSnapshot tick : history) {
            if (now - tick.timestamp > 60000) continue;
            if (tick.durationMs > slowTickThreshold) {
                Map<String, Object> frame = new HashMap<>();
                frame.put("name", "tick_" + tick.timestamp);
                frame.put("value", tick.durationMs);
                flameData.add(frame);
            }
        }
        return flameData;
    }

    public List<Suggestion> getSuggestions() {
        List<Suggestion> result = new ArrayList<>(suggestions);
        if (!history.isEmpty()) {
            long totalTicks = history.size();
            long slowTicks = history.stream().filter(t -> t.durationMs > slowTickThreshold).count();
            double slowPercent = totalTicks > 0 ? (slowTicks * 100.0 / totalTicks) : 0;
            if (slowPercent > 20) {
                long maxTick = history.stream().mapToLong(t -> t.durationMs).max().orElse(0);
                result.add(new Suggestion("tick", String.format(SUGGESTION_PATTERNS[4], maxTick), "HIGH"));
            }
            long mem = Runtime.getRuntime().totalMemory() - Runtime.getRuntime().freeMemory();
            result.add(new Suggestion("memory", String.format(SUGGESTION_PATTERNS[5], mem / 1024 / 1024), "INFO"));
        }
        return result;
    }

    public static class PerformanceCommand {
        private final PlayerServerPlugin plugin;
        private final PerformanceProfilerManager manager;

        public PerformanceCommand(PlayerServerPlugin plugin, PerformanceProfilerManager manager) {
            this.plugin = plugin;
            this.manager = manager;
            plugin.getProxy().getPluginManager().registerCommand(plugin, new PerfCommand());
        }

        private class PerfCommand extends Command {
            public PerfCommand() { super("perf", "playerservers.perf"); }

            @Override
            public void execute(CommandSender sender, String[] args) {
                if (args.length < 1) {
                    sender.sendMessage(new ComponentBuilder("Usage: /perf <start|stop|report|suggest>")
                        .color(ChatColor.RED).create());
                    return;
                }

                switch (args[0].toLowerCase()) {
                    case "start":
                        manager.startProfiling();
                        sender.sendMessage(new ComponentBuilder("[Profiler] Profiling started.")
                            .color(ChatColor.GREEN).create());
                        break;

                    case "stop":
                        manager.stopProfiling();
                        sender.sendMessage(new ComponentBuilder("[Profiler] Profiling stopped.")
                            .color(ChatColor.YELLOW).create());
                        break;

                    case "report":
                        String report = manager.generateReport();
                        sender.sendMessage(new ComponentBuilder(report).color(ChatColor.WHITE).create());
                        break;

                    case "suggest":
                        List<Suggestion> suggestions = manager.getSuggestions();
                        if (suggestions.isEmpty()) {
                            sender.sendMessage(new ComponentBuilder("[Profiler] No suggestions at this time.")
                                .color(ChatColor.GREEN).create());
                        } else {
                            sender.sendMessage(new ComponentBuilder("=== Performance Suggestions ===")
                                .color(ChatColor.GOLD).create());
                            for (int i = 0; i < Math.min(suggestions.size(), 10); i++) {
                                Suggestion s = suggestions.get(i);
                                ChatColor color = "HIGH".equals(s.severity) ? ChatColor.RED :
                                    "MEDIUM".equals(s.severity) ? ChatColor.YELLOW : ChatColor.GREEN;
                                sender.sendMessage(new ComponentBuilder(String.format("%d. [%s] %s", i + 1, s.severity, s.message))
                                    .color(color).create());
                            }
                        }
                        break;

                    default:
                        sender.sendMessage(new ComponentBuilder("Unknown subcommand. Use: start, stop, report, suggest")
                            .color(ChatColor.RED).create());
                }
            }
        }
    }

    private static class TickSnapshot {
        final long durationMs;
        final long timestamp;

        TickSnapshot(long durationMs, long timestamp) {
            this.durationMs = durationMs;
            this.timestamp = timestamp;
        }
    }

    private static class ProfileSnapshot {
        final long timestamp;
        final Map<String, Long> entities;
        final Map<String, Long> redstone;
        final Map<String, Long> pluginTimings;
        final Map<String, Long> chunks;
        final long lastTickMs;
        final long memoryBytes;

        ProfileSnapshot(long timestamp, Map<String, Long> entities, Map<String, Long> redstone,
                        Map<String, Long> pluginTimings, Map<String, Long> chunks,
                        long lastTickMs, long memoryBytes) {
            this.timestamp = timestamp;
            this.entities = entities;
            this.redstone = redstone;
            this.pluginTimings = pluginTimings;
            this.chunks = chunks;
            this.lastTickMs = lastTickMs;
            this.memoryBytes = memoryBytes;
        }
    }

    public static class Suggestion {
        public final String category;
        public final String message;
        public final String severity;

        public Suggestion(String category, String message, String severity) {
            this.category = category;
            this.message = message;
            this.severity = severity;
        }
    }
}
