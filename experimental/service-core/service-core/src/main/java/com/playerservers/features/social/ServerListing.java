package com.playerservers.features.social;

import java.sql.Timestamp;
import java.util.List;

public class ServerListing {
    private int id;
    private String playerUuid;
    private String serverName;
    private String description;
    private List<String> tags;
    private int playerCount;
    private int maxPlayers;
    private int upvotes;
    private int downvotes;
    private boolean isPublic;
    private double averageRating;
    private int reviewCount;
    private Timestamp lastUpdated;
    private String ownerName;

    public ServerListing(int id, String playerUuid, String serverName, String description,
                        List<String> tags, int playerCount, int maxPlayers,
                        int upvotes, int downvotes, boolean isPublic,
                        Timestamp lastUpdated) {
        this.id = id;
        this.playerUuid = playerUuid;
        this.serverName = serverName;
        this.description = description;
        this.tags = tags;
        this.playerCount = playerCount;
        this.maxPlayers = maxPlayers;
        this.upvotes = upvotes;
        this.downvotes = downvotes;
        this.isPublic = isPublic;
        this.lastUpdated = lastUpdated;
    }

    public int getId() { return id; }
    public String getPlayerUuid() { return playerUuid; }
    public String getServerName() { return serverName; }
    public String getDescription() { return description; }
    public List<String> getTags() { return tags; }
    public int getPlayerCount() { return playerCount; }
    public int getMaxPlayers() { return maxPlayers; }
    public int getUpvotes() { return upvotes; }
    public int getDownvotes() { return downvotes; }
    public boolean isPublic() { return isPublic; }
    public double getAverageRating() { return averageRating; }
    public int getReviewCount() { return reviewCount; }
    public Timestamp getLastUpdated() { return lastUpdated; }
    public String getOwnerName() { return ownerName; }
    public int getRatingScore() { return upvotes - downvotes; }

    public void setAverageRating(double averageRating) { this.averageRating = averageRating; }
    public void setReviewCount(int reviewCount) { this.reviewCount = reviewCount; }
    public void setOwnerName(String ownerName) { this.ownerName = ownerName; }
}
