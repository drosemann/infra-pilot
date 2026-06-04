import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet } from 'react-native';
import { endpoints } from '../../api/endpoints';

export default function CommunityPlatformScreen({ navigation }: any) {
  const [posts, setPosts] = useState<any[]>([]);

  useEffect(() => {
    endpoints.customerExperience.community.posts().then((res) => setPosts(res.posts || [])).catch(console.error);
  }, []);

  const renderItem = ({ item }: any) => (
    <TouchableOpacity
      style={styles.card}
      onPress={() => navigation.navigate('PostDetail', { postId: item.id })}
    >
      <Text style={styles.title}>{item.title}</Text>
      <Text style={styles.author}>by {item.author_name || 'Anonymous'} · {item.post_type}</Text>
      <View style={styles.stats}>
        <Text style={styles.stat}>↑ {item.upvotes}</Text>
        <Text style={styles.stat}>↓ {item.downvotes}</Text>
        <Text style={styles.stat}>💬 {item.comment_count || 0}</Text>
      </View>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <Text style={styles.heading}>Community</Text>
      <FlatList data={posts} keyExtractor={(i) => i.id} renderItem={renderItem} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: '#121212' },
  heading: { fontSize: 24, fontWeight: 'bold', color: '#fff', marginBottom: 16 },
  card: { backgroundColor: '#1e1e1e', padding: 16, borderRadius: 8, marginBottom: 12 },
  title: { fontSize: 16, color: '#fff', fontWeight: '600' },
  author: { fontSize: 12, color: '#888', marginTop: 2 },
  stats: { flexDirection: 'row', marginTop: 8 },
  stat: { fontSize: 14, color: '#aaa', marginRight: 16 },
});
