import { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  Switch,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { theme } from '../../src/theme';
import { useAuth } from '../../src/hooks/useAuth';
import {
  isBiometricAvailable,
  authenticateWithBiometrics,
  storeTokenForBiometric,
  clearBiometricToken,
} from '../../src/utils/biometric';
import { registerForPushNotifications } from '../../src/utils/notifications';

export default function SettingsScreen() {
  const { state, logout } = useAuth();
  const router = useRouter();
  const [biometricEnabled, setBiometricEnabled] = useState(false);
  const [notificationsEnabled, setNotificationsEnabled] = useState(false);

  async function toggleBiometric(value: boolean) {
    if (value) {
      const available = await isBiometricAvailable();
      if (!available) {
        Alert.alert('Unavailable', 'Biometric authentication is not available on this device');
        return;
      }
      const authenticated = await authenticateWithBiometrics();
      if (authenticated && state.token) {
        await storeTokenForBiometric(state.token);
        setBiometricEnabled(true);
      }
    } else {
      await clearBiometricToken();
      setBiometricEnabled(false);
    }
  }

  async function toggleNotifications(value: boolean) {
    if (value) {
      const token = await registerForPushNotifications();
      if (token) {
        setNotificationsEnabled(true);
        Alert.alert('Success', 'Push notifications enabled');
      } else {
        Alert.alert('Permission Denied', 'Enable notifications in system settings');
      }
    } else {
      setNotificationsEnabled(false);
    }
  }

  async function handleLogout() {
    Alert.alert('Sign Out', 'Are you sure you want to sign out?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Sign Out',
        style: 'destructive',
        onPress: async () => {
          await logout();
          router.replace('/');
        },
      },
    ]);
  }

  const settingsSections = [
    {
      title: 'Security',
      items: [
        {
          icon: 'finger-print-outline',
          label: 'Biometric Login',
          type: 'switch',
          value: biometricEnabled,
          onToggle: toggleBiometric,
        },
      ],
    },
    {
      title: 'Notifications',
      items: [
        {
          icon: 'notifications-outline',
          label: 'Push Notifications',
          type: 'switch',
          value: notificationsEnabled,
          onToggle: toggleNotifications,
        },
      ],
    },
    {
      title: 'Account',
      items: [
        {
          icon: 'person-outline',
          label: 'Display Name',
          type: 'info',
          value: state.user?.display_name || 'N/A',
        },
        {
          icon: 'mail-outline',
          label: 'Email',
          type: 'info',
          value: state.user?.email || 'N/A',
        },
        {
          icon: 'shield-checkmark-outline',
          label: 'Role',
          type: 'info',
          value: state.user?.role || 'N/A',
        },
      ],
    },
  ];

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {settingsSections.map((section, si) => (
        <View key={si} style={styles.section}>
          <Text style={styles.sectionTitle}>{section.title}</Text>
          <View style={styles.sectionCard}>
            {section.items.map((item, ii) => (
              <View key={ii} style={[styles.settingRow, ii < section.items.length - 1 && styles.settingBorder]}>
                <View style={styles.settingLeft}>
                  <Ionicons name={item.icon as any} size={20} color={theme.colors.primary} />
                  <Text style={styles.settingLabel}>{item.label}</Text>
                </View>
                {item.type === 'switch' ? (
                  <Switch
                    value={item.value as boolean}
                    onValueChange={item.onToggle as (v: boolean) => void}
                    trackColor={{ false: theme.colors.border, true: theme.colors.primary + '60' }}
                    thumbColor={item.value ? theme.colors.primary : theme.colors.textSecondary}
                  />
                ) : (
                  <Text style={styles.settingValue}>{item.value as string}</Text>
                )}
              </View>
            ))}
          </View>
        </View>
      ))}

      <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
        <Ionicons name="log-out-outline" size={20} color={theme.colors.danger} />
        <Text style={styles.logoutText}>Sign Out</Text>
      </TouchableOpacity>

      <Text style={styles.version}>Infra Pilot v1.0.0</Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  content: {
    padding: theme.spacing.md,
    paddingBottom: 32,
  },
  section: {
    marginBottom: theme.spacing.lg,
  },
  sectionTitle: {
    fontSize: theme.fontSize.sm,
    fontWeight: '700',
    color: theme.colors.textSecondary,
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: theme.spacing.sm,
    marginLeft: theme.spacing.xs,
  },
  sectionCard: {
    backgroundColor: theme.colors.surface,
    borderRadius: theme.borderRadius.md,
    borderWidth: 1,
    borderColor: theme.colors.border,
    overflow: 'hidden',
  },
  settingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: theme.spacing.md,
    paddingHorizontal: theme.spacing.md,
  },
  settingBorder: {
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.border,
  },
  settingLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.sm,
  },
  settingLabel: {
    fontSize: theme.fontSize.md,
    color: theme.colors.text,
  },
  settingValue: {
    fontSize: theme.fontSize.sm,
    color: theme.colors.textSecondary,
  },
  logoutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: theme.colors.surface,
    borderRadius: theme.borderRadius.md,
    borderWidth: 1,
    borderColor: theme.colors.danger + '40',
    paddingVertical: theme.spacing.md,
    gap: theme.spacing.sm,
    marginBottom: theme.spacing.lg,
  },
  logoutText: {
    fontSize: theme.fontSize.md,
    fontWeight: '600',
    color: theme.colors.danger,
  },
  version: {
    textAlign: 'center',
    fontSize: theme.fontSize.xs,
    color: theme.colors.textSecondary,
  },
});
