import React, { useState } from "react";
import { View, Text, TextInput, TouchableOpacity, FlatList, StyleSheet, KeyboardAvoidingView, Platform } from "react-native";
import { Ionicons } from "@expo/vector-icons";

interface Message {
  id: string;
  text: string;
  sender: "user" | "assistant";
}

export default function ConversationalOpsScreen() {
  const [messages, setMessages] = useState<Message[]>([
    { id: "1", text: "Hello! I'm your Ops Assistant. How can I help?", sender: "assistant" },
  ]);
  const [input, setInput] = useState("");

  const sendMessage = () => {
    if (!input.trim()) return;
    const userMsg: Message = { id: Date.now().toString(), text: input, sender: "user" };
    const reply: Message = {
      id: (Date.now() + 1).toString(),
      text: `Processing: "${input}" - intent detected, action queued.`,
      sender: "assistant",
    };
    setMessages(prev => [...prev, userMsg, reply]);
    setInput("");
  };

  return (
    <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === "ios" ? "padding" : undefined}>
      <Text style={styles.title}>Ops Assistant</Text>
      <FlatList
        data={messages}
        keyExtractor={item => item.id}
        renderItem={({ item }) => (
          <View style={[styles.bubble, item.sender === "user" ? styles.userBubble : styles.assistantBubble]}>
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
  assistantBubble: { backgroundColor: "#1e293b", alignSelf: "flex-start" },
  bubbleText: { color: "#f8fafc", fontSize: 14 },
  userText: { color: "#fff" },
  inputRow: { flexDirection: "row", gap: 8, marginTop: 8 },
  input: { flex: 1, backgroundColor: "#1e293b", borderRadius: 12, padding: 12, color: "#f8fafc", fontSize: 14 },
  sendBtn: { backgroundColor: "#3b82f6", borderRadius: 12, padding: 12, justifyContent: "center" },
});
