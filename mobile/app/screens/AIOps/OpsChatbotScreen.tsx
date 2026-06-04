import React, { useState } from "react";
import { View, Text, TextInput, TouchableOpacity, FlatList, StyleSheet, KeyboardAvoidingView, Platform } from "react-native";
import { Ionicons } from "@expo/vector-icons";

interface ChatMessage {
  id: string;
  text: string;
  sender: "user" | "bot";
  type?: "success" | "error" | "info";
}

export default function OpsChatbotScreen() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    { id: "1", text: "Hi! I'm your Ops Chatbot. Try: restart, logs, backup, status, scale, deploy", sender: "bot", type: "info" },
  ]);
  const [input, setInput] = useState("");

  const sendMessage = () => {
    if (!input.trim()) return;
    const userMsg: ChatMessage = { id: Date.now().toString(), text: input, sender: "user" };
    const cmd = input.toLowerCase();
    let replyText = `Executing: "${input}"`;
    let replyType: "success" | "error" | "info" = "success";
    if (cmd.includes("restart")) replyText = "Restarting service... done.";
    else if (cmd.includes("logs")) replyText = "Fetching logs... 47 entries found.";
    else if (cmd.includes("backup")) replyText = "Backup initiated: postgres-db-2026-05-30.";
    else if (cmd.includes("status")) replyText = "All systems operational. 3 services healthy.";
    else if (cmd.includes("scale")) replyText = "Scaling api-service to 5 replicas.";
    else if (cmd.includes("deploy")) replyText = "Deploying v3.2 to staging... complete.";
    else replyType = "info";
    const botMsg: ChatMessage = { id: (Date.now() + 1).toString(), text: replyText, sender: "bot", type: replyType };
    setMessages(prev => [...prev, userMsg, botMsg]);
    setInput("");
  };

  return (
    <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === "ios" ? "padding" : undefined}>
      <Text style={styles.title}>Ops Chatbot</Text>
      <FlatList
        data={messages}
        keyExtractor={item => item.id}
        renderItem={({ item }) => (
          <View style={[styles.bubble, item.sender === "user" ? styles.userBubble : styles.botBubble]}>
            <Text style={[styles.bubbleText, item.sender === "user" && styles.userText]}>{item.text}</Text>
          </View>
        )}
        style={styles.chatList}
      />
      <View style={styles.inputRow}>
        <TextInput
          style={styles.input}
          value={input}
          onChangeText={setInput}
          placeholder="Type a command..."
          placeholderTextColor="#64748b"
        />
        <TouchableOpacity onPress={sendMessage} style={styles.sendBtn}>
          <Ionicons name="send" size={20} color="#fff" />
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0f172a", padding: 16 },
  title: { fontSize: 28, fontWeight: "bold", color: "#f8fafc", marginBottom: 16 },
  chatList: { flex: 1 },
  bubble: { padding: 12, borderRadius: 12, marginBottom: 8, maxWidth: "80%" },
  userBubble: { backgroundColor: "#3b82f6", alignSelf: "flex-end" },
  botBubble: { backgroundColor: "#1e293b", alignSelf: "flex-start" },
  bubbleText: { color: "#f8fafc", fontSize: 14 },
  userText: { color: "#fff" },
  inputRow: { flexDirection: "row", gap: 8, marginTop: 8 },
  input: { flex: 1, backgroundColor: "#1e293b", borderRadius: 12, padding: 12, color: "#f8fafc", fontSize: 14 },
  sendBtn: { backgroundColor: "#3b82f6", borderRadius: 12, padding: 12, justifyContent: "center" },
});
