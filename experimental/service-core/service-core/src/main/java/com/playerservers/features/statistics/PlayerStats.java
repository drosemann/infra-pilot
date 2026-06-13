package com.playerservers.features.statistics;

import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.atomic.AtomicReference;

public class PlayerStats {
    private final AtomicLong totalPlaytime;
    private final AtomicInteger peakPlayers;
    private final AtomicLong peakMemoryUsage;
    private final AtomicReference<Double> peakCpuUsage;
    private final AtomicInteger totalRestarts;
    private final AtomicReference<Double> uptimePercentage;
    
    // Current metrics
    private final AtomicReference<Double> currentCpuUsage;
    private final AtomicLong currentMemoryUsage;
    private final AtomicInteger currentPlayers;
    private final AtomicReference<Double> currentTPS;
    private final AtomicReference<String> currentStatus;
    
    // Uptime tracking
    private long startTime;
    private long totalDowntime;
    private boolean isOnline;

    public PlayerStats() {
        this(0L, 0, 0L, 0.0, 0, 100.0);
    }

    public PlayerStats(long totalPlaytime, int peakPlayers, long peakMemoryUsage,
                      double peakCpuUsage, int totalRestarts, double uptimePercentage) {
        this.totalPlaytime = new AtomicLong(totalPlaytime);
        this.peakPlayers = new AtomicInteger(peakPlayers);
        this.peakMemoryUsage = new AtomicLong(peakMemoryUsage);
        this.peakCpuUsage = new AtomicReference<>(peakCpuUsage);
        this.totalRestarts = new AtomicInteger(totalRestarts);
        this.uptimePercentage = new AtomicReference<>(uptimePercentage);
        
        this.currentCpuUsage = new AtomicReference<>(0.0);
        this.currentMemoryUsage = new AtomicLong(0);
        this.currentPlayers = new AtomicInteger(0);
        this.currentTPS = new AtomicReference<>(20.0);
        this.currentStatus = new AtomicReference<>("offline");
        
        this.startTime = System.currentTimeMillis();
        this.totalDowntime = 0;
        this.isOnline = false;
    }

    public void updateCurrentMetrics(double cpuUsage, long memoryUsage, int playerCount, double tps) {
        this.currentCpuUsage.set(cpuUsage);
        this.currentMemoryUsage.set(memoryUsage);
        this.currentPlayers.set(playerCount);
        this.currentTPS.set(tps);
    }

    public void updatePeaks() {
        // Update peak values if current values are higher
        peakPlayers.updateAndGet(current -> Math.max(current, currentPlayers.get()));
        peakMemoryUsage.updateAndGet(current -> Math.max(current, currentMemoryUsage.get()));
        peakCpuUsage.updateAndGet(current -> Math.max(current, currentCpuUsage.get()));
    }

    public void markServerOnline() {
        if (!isOnline) {
            isOnline = true;
            currentStatus.set("online");
            startTime = System.currentTimeMillis();
        }
    }

    public void markServerOffline() {
        if (isOnline) {
            isOnline = false;
            currentStatus.set("offline");
            totalDowntime += System.currentTimeMillis() - startTime;
            updateUptimePercentage();
        }
    }

    private void updateUptimePercentage() {
        long totalTime = System.currentTimeMillis() - startTime + totalDowntime;
        if (totalTime > 0) {
            double uptime = 100.0 * (totalTime - totalDowntime) / totalTime;
            uptimePercentage.set(uptime);
        }
    }

    public void incrementRestarts() {
        totalRestarts.incrementAndGet();
    }

    // Getters
    public long getTotalPlaytime() {
        return totalPlaytime.get();
    }

    public int getPeakPlayers() {
        return peakPlayers.get();
    }

    public long getPeakMemoryUsage() {
        return peakMemoryUsage.get();
    }

    public double getPeakCpuUsage() {
        return peakCpuUsage.get();
    }

    public int getTotalRestarts() {
        return totalRestarts.get();
    }

    public double getUptimePercentage() {
        updateUptimePercentage();
        return uptimePercentage.get();
    }

    public double getCurrentCpuUsage() {
        return currentCpuUsage.get();
    }

    public long getCurrentMemoryUsage() {
        return currentMemoryUsage.get();
    }

    public int getCurrentPlayers() {
        return currentPlayers.get();
    }

    public double getCurrentTPS() {
        return currentTPS.get();
    }

    public String getCurrentStatus() {
        return currentStatus.get();
    }

    public boolean isServerOnline() {
        return isOnline;
    }

    // Additional utility methods
    public void addPlaytime(long milliseconds) {
        totalPlaytime.addAndGet(milliseconds);
    }

    public void setTotalPlaytime(long milliseconds) {
        totalPlaytime.set(milliseconds);
    }

    public void setPeakPlayers(int count) {
        peakPlayers.set(count);
    }

    public void setPeakMemoryUsage(long bytes) {
        peakMemoryUsage.set(bytes);
    }

    public void setPeakCpuUsage(double percentage) {
        peakCpuUsage.set(percentage);
    }

    public void setUptimePercentage(double percentage) {
        uptimePercentage.set(percentage);
    }

    public void resetStats() {
        currentCpuUsage.set(0.0);
        currentMemoryUsage.set(0);
        currentPlayers.set(0);
        currentTPS.set(20.0);
        currentStatus.set("offline");
        isOnline = false;
        startTime = System.currentTimeMillis();
        totalDowntime = 0;
    }
}