package com.playerservers.features.social;

import java.sql.Timestamp;
import java.util.UUID;

public class ServerReview {
    private int id;
    private String serverId;
    private UUID reviewerUuid;
    private int rating;
    private String comment;
    private Timestamp createdAt;
    private Timestamp updatedAt;
    private String reviewerName;

    public ServerReview(int id, String serverId, UUID reviewerUuid, int rating,
                       String comment, Timestamp createdAt, Timestamp updatedAt) {
        this.id = id;
        this.serverId = serverId;
        this.reviewerUuid = reviewerUuid;
        this.rating = rating;
        this.comment = comment;
        this.createdAt = createdAt;
        this.updatedAt = updatedAt;
    }

    public int getId() { return id; }
    public String getServerId() { return serverId; }
    public UUID getReviewerUuid() { return reviewerUuid; }
    public int getRating() { return rating; }
    public String getComment() { return comment; }
    public Timestamp getCreatedAt() { return createdAt; }
    public Timestamp getUpdatedAt() { return updatedAt; }
    public String getReviewerName() { return reviewerName; }

    public void setReviewerName(String reviewerName) { this.reviewerName = reviewerName; }
}
