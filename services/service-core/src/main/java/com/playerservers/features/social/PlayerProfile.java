package com.playerservers.features.social;

import java.util.List;
import java.util.Map;
import java.util.UUID;

public class PlayerProfile {
    private UUID playerUuid;
    private String playerName;
    private String bio;
    private String avatarUrl;
    private String website;
    private String discord;
    private int totalPlaytime;
    private int serversCreated;
    private int friendsCount;
    private int reputationScore;
    private List<String> ownedServers;
    private List<Friend> friends;
    private Map<String, Object> statistics;

    public PlayerProfile(UUID playerUuid) {
        this.playerUuid = playerUuid;
    }

    public UUID getPlayerUuid() { return playerUuid; }
    public String getPlayerName() { return playerName; }
    public String getBio() { return bio; }
    public String getAvatarUrl() { return avatarUrl; }
    public String getWebsite() { return website; }
    public String getDiscord() { return discord; }
    public int getTotalPlaytime() { return totalPlaytime; }
    public int getServersCreated() { return serversCreated; }
    public int getFriendsCount() { return friendsCount; }
    public int getReputationScore() { return reputationScore; }
    public List<String> getOwnedServers() { return ownedServers; }
    public List<Friend> getFriends() { return friends; }
    public Map<String, Object> getStatistics() { return statistics; }

    public void setPlayerName(String playerName) { this.playerName = playerName; }
    public void setBio(String bio) { this.bio = bio; }
    public void setAvatarUrl(String avatarUrl) { this.avatarUrl = avatarUrl; }
    public void setWebsite(String website) { this.website = website; }
    public void setDiscord(String discord) { this.discord = discord; }
    public void setTotalPlaytime(int totalPlaytime) { this.totalPlaytime = totalPlaytime; }
    public void setServersCreated(int serversCreated) { this.serversCreated = serversCreated; }
    public void setFriendsCount(int friendsCount) { this.friendsCount = friendsCount; }
    public void setReputationScore(int reputationScore) { this.reputationScore = reputationScore; }
    public void setOwnedServers(List<String> ownedServers) { this.ownedServers = ownedServers; }
    public void setFriends(List<Friend> friends) { this.friends = friends; }
    public void setStatistics(Map<String, Object> statistics) { this.statistics = statistics; }
}
