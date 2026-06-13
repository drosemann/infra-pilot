package com.playerservers.features.social;

import java.sql.Timestamp;
import java.util.List;
import java.util.UUID;

public class Community {
    private int id;
    private String name;
    private String description;
    private UUID ownerUuid;
    private int memberCount;
    private boolean isPublic;
    private Timestamp createdAt;
    private String ownerName;
    private List<CommunityMember> members;
    private MemberRole userRole;

    public enum MemberRole {
        owner, admin, member
    }

    public Community(int id, String name, String description, UUID ownerUuid,
                    int memberCount, boolean isPublic, Timestamp createdAt) {
        this.id = id;
        this.name = name;
        this.description = description;
        this.ownerUuid = ownerUuid;
        this.memberCount = memberCount;
        this.isPublic = isPublic;
        this.createdAt = createdAt;
    }

    public int getId() { return id; }
    public String getName() { return name; }
    public String getDescription() { return description; }
    public UUID getOwnerUuid() { return ownerUuid; }
    public int getMemberCount() { return memberCount; }
    public boolean isPublic() { return isPublic; }
    public Timestamp getCreatedAt() { return createdAt; }
    public String getOwnerName() { return ownerName; }
    public List<CommunityMember> getMembers() { return members; }
    public MemberRole getUserRole() { return userRole; }

    public void setOwnerName(String ownerName) { this.ownerName = ownerName; }
    public void setMembers(List<CommunityMember> members) { this.members = members; }
    public void setUserRole(MemberRole userRole) { this.userRole = userRole; }
}
