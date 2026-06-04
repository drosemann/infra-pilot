import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet } from 'react-native';
import { endpoints } from '../../api/endpoints';

export default function OnboardingWizardScreen() {
  const [customerId, setCustomerId] = useState('');
  const [session, setSession] = useState<any>(null);

  const startOnboarding = async () => {
    if (!customerId) return;
    try {
      const res = await endpoints.customerExperience.onboarding.start({
        customer_id: customerId, customer_name: customerId,
      });
      setSession(res);
    } catch (e) {
      console.error(e);
    }
  };

  const completeStep = async (stepId: string) => {
    if (!session) return;
    try {
      const res = await endpoints.customerExperience.onboarding.step({
        session_id: session.id, step_id: stepId, status: 'completed',
      });
      const updated = await endpoints.customerExperience.onboarding.get(customerId);
      setSession(updated);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Onboarding Wizard</Text>
      <TextInput
        style={styles.input}
        placeholder="Customer ID"
        placeholderTextColor="#666"
        value={customerId}
        onChangeText={setCustomerId}
      />
      <TouchableOpacity style={styles.button} onPress={startOnboarding}>
        <Text style={styles.buttonText}>Start Onboarding</Text>
      </TouchableOpacity>
      {session && (
        <View style={styles.sessionCard}>
          <Text style={styles.progress}>Progress: {session.completed_steps}/{session.total_steps}</Text>
          {session.steps?.map((step: any) => (
            <TouchableOpacity
              key={step.id}
              style={[styles.step, step.status === 'completed' && styles.stepDone]}
              onPress={() => completeStep(step.id)}
              disabled={step.status === 'completed'}
            >
              <Text style={styles.stepText}>{step.title || step.id} — {step.status}</Text>
            </TouchableOpacity>
          ))}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: '#121212' },
  title: { fontSize: 24, fontWeight: 'bold', color: '#fff', marginBottom: 16 },
  input: { backgroundColor: '#1e1e1e', color: '#fff', borderRadius: 8, padding: 12, marginBottom: 12 },
  button: { backgroundColor: '#1976d2', padding: 14, borderRadius: 8, alignItems: 'center', marginBottom: 16 },
  buttonText: { color: '#fff', fontWeight: 'bold', fontSize: 16 },
  sessionCard: { backgroundColor: '#1e1e1e', padding: 16, borderRadius: 8 },
  progress: { fontSize: 18, color: '#fff', fontWeight: '600', marginBottom: 12 },
  step: { backgroundColor: '#333', padding: 12, borderRadius: 6, marginBottom: 8 },
  stepDone: { backgroundColor: '#2e7d32' },
  stepText: { color: '#fff', fontSize: 14 },
});
