package com.playerservers.features.social;

import java.sql.Timestamp;
import java.util.UUID;

public class CommunityMember {
    private int id;
    private int communityId;
    private UUID playerUuid;
    private Community.MemberRole role;
    private Timestamp joinedAt;
    private String playerName;

    public CommunityMember(int id, int communityId, UUID playerUuid,
                          Community.MemberRole role, Timestamp joinedAt) {
        this.id = id;
        this.communityId = communityId;
        this.playerUuid = playerUuid;
        this.role = role;
        this.joinedAt = joinedAt;
    }

    public int getId() { return id; }
    public int getCommunityId() { return communityId; }
    public UUID getPlayerUuid() { return playerUuid; }
    public Community.MemberRole getRole() { return role; }
    public Timestamp getJoinedAt() { return joinedAt; }
    public String getPlayerName() { return playerName; }

    public void setRole(Community.MemberRole role) { this.role = role; }
    public void setPlayerName(String playerName) { this.playerName = playerName; }
}
