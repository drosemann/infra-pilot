package com.playerservers.features.social;

import java.sql.Timestamp;
import java.util.UUID;

public class Message {
    private int id;
    private UUID senderUuid;
    private UUID receiverUuid;
    private String message;
    private boolean isRead;
    private Timestamp createdAt;
    private String senderName;

    public Message(int id, UUID senderUuid, UUID receiverUuid, String message,
                  boolean isRead, Timestamp createdAt) {
        this.id = id;
        this.senderUuid = senderUuid;
        this.receiverUuid = receiverUuid;
        this.message = message;
        this.isRead = isRead;
        this.createdAt = createdAt;
    }

    public int getId() { return id; }
    public UUID getSenderUuid() { return senderUuid; }
    public UUID getReceiverUuid() { return receiverUuid; }
    public String getMessage() { return message; }
    public boolean isRead() { return isRead; }
    public Timestamp getCreatedAt() { return createdAt; }
    public String getSenderName() { return senderName; }

    public void setRead(boolean read) { isRead = read; }
    public void setSenderName(String senderName) { this.senderName = senderName; }
}
