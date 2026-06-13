package com.playerservers.features.social;

import java.sql.Timestamp;
import java.util.UUID;

public class Friend {
    private int id;
    private UUID playerUuid;
    private UUID friendUuid;
    private Status status;
    private Timestamp createdAt;
    private Timestamp updatedAt;
    private String friendName;
    private boolean friendOnline;

    public enum Status {
        pending, accepted, blocked
    }

    public Friend(int id, UUID playerUuid, UUID friendUuid, Status status, Timestamp createdAt, Timestamp updatedAt) {
        this.id = id;
        this.playerUuid = playerUuid;
        this.friendUuid = friendUuid;
        this.status = status;
        this.createdAt = createdAt;
        this.updatedAt = updatedAt;
    }

    public int getId() { return id; }
    public UUID getPlayerUuid() { return playerUuid; }
    public UUID getFriendUuid() { return friendUuid; }
    public Status getStatus() { return status; }
    public Timestamp getCreatedAt() { return createdAt; }
    public Timestamp getUpdatedAt() { return updatedAt; }
    public String getFriendName() { return friendName; }
    public boolean isFriendOnline() { return friendOnline; }

    public void setStatus(Status status) { this.status = status; }
    public void setFriendName(String friendName) { this.friendName = friendName; }
    public void setFriendOnline(boolean friendOnline) { this.friendOnline = friendOnline; }
}
