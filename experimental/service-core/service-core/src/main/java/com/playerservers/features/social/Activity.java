package com.playerservers.features.social;

import java.sql.Timestamp;
import java.util.Map;
import java.util.UUID;

public class Activity {
    private int id;
    private UUID playerUuid;
    private ActivityType activityType;
    private int targetId;
    private Map<String, Object> metadata;
    private Timestamp createdAt;
    private String playerName;

    public enum ActivityType {
        server_created,
        server_started,
        server_stopped,
        friend_joined,
        friend_left,
        review_posted,
        achievement_earned,
        community_joined,
        invitation_sent,
        invitation_accepted,
        server_rated,
        profile_updated
    }

    public Activity(int id, UUID playerUuid, ActivityType activityType,
                   int targetId, Map<String, Object> metadata, Timestamp createdAt) {
        this.id = id;
        this.playerUuid = playerUuid;
        this.activityType = activityType;
        this.targetId = targetId;
        this.metadata = metadata;
        this.createdAt = createdAt;
    }

    public int getId() { return id; }
    public UUID getPlayerUuid() { return playerUuid; }
    public ActivityType getActivityType() { return activityType; }
    public int getTargetId() { return targetId; }
    public Map<String, Object> getMetadata() { return metadata; }
    public Timestamp getCreatedAt() { return createdAt; }
    public String getPlayerName() { return playerName; }

    public void setPlayerName(String playerName) { this.playerName = playerName; }

    public String getFormattedMessage() {
        switch (activityType) {
            case server_created:
                return "created a new server";
            case server_started:
                return "started their server";
            case server_stopped:
                return "stopped their server";
            case friend_joined:
                return "came online";
            case friend_left:
                return "went offline";
            case review_posted:
                return "posted a review";
            case achievement_earned:
                return "earned an achievement";
            case community_joined:
                return "joined a community";
            case invitation_sent:
                return "sent a server invitation";
            case invitation_accepted:
                return "accepted a server invitation";
            case server_rated:
                return "rated a server";
            case profile_updated:
                return "updated their profile";
            default:
                return "did something";
        }
    }
}
