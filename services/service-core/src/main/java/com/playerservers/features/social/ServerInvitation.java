package com.playerservers.features.social;

import java.sql.Timestamp;
import java.util.UUID;

public class ServerInvitation {
    private int id;
    private String serverId;
    private UUID inviterUuid;
    private UUID inviteeUuid;
    private PermissionLevel permissionLevel;
    private Status status;
    private Timestamp expiresAt;
    private Timestamp createdAt;
    private String inviterName;
    private String serverName;

    public enum PermissionLevel {
        player, operator, admin
    }

    public enum Status {
        pending, accepted, declined, expired
    }

    public ServerInvitation(int id, String serverId, UUID inviterUuid, UUID inviteeUuid,
                           PermissionLevel permissionLevel, Status status,
                           Timestamp expiresAt, Timestamp createdAt) {
        this.id = id;
        this.serverId = serverId;
        this.inviterUuid = inviterUuid;
        this.inviteeUuid = inviteeUuid;
        this.permissionLevel = permissionLevel;
        this.status = status;
        this.expiresAt = expiresAt;
        this.createdAt = createdAt;
    }

    public int getId() { return id; }
    public String getServerId() { return serverId; }
    public UUID getInviterUuid() { return inviterUuid; }
    public UUID getInviteeUuid() { return inviteeUuid; }
    public PermissionLevel getPermissionLevel() { return permissionLevel; }
    public Status getStatus() { return status; }
    public Timestamp getExpiresAt() { return expiresAt; }
    public Timestamp getCreatedAt() { return createdAt; }
    public String getInviterName() { return inviterName; }
    public String getServerName() { return serverName; }

    public void setStatus(Status status) { this.status = status; }
    public void setInviterName(String inviterName) { this.inviterName = inviterName; }
    public void setServerName(String serverName) { this.serverName = serverName; }
    public boolean isExpired() {
        return expiresAt != null && expiresAt.getTime() < System.currentTimeMillis();
    }
}
