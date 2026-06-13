import { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  RefreshControl,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { theme } from '../src/theme';
import { BillingInfo, Transaction } from '../src/types';
import { endpoints } from '../src/api/endpoints';
import { LoadingState } from '../src/components/LoadingState';
import { formatCurrency, formatDate } from '../src/utils/formatting';

export default function BillingScreen() {
  const [billing, setBilling] = useState<BillingInfo | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      const [balance, txns] = await Promise.all([
        endpoints.billing.balance(),
        endpoints.billing.transactions(),
      ]);
      setBilling(balance);
      setTransactions(txns);
    } catch (e: any) {
      Alert.alert('Error', e?.message || 'Failed to load billing info');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function onRefresh() {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  }

  if (isLoading && !refreshing) {
    return <LoadingState message="Loading billing..." />;
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.colors.primary} />}
    >
      {billing && (
        <View style={styles.balanceCard}>
          <Text style={styles.balanceLabel}>Current Balance</Text>
          <Text style={styles.balanceAmount}>
            {formatCurrency(billing.balance)}
          </Text>
          <View style={styles.balanceStats}>
            <View style={styles.balanceStat}>
              <Text style={styles.statLabel}>Total Spent</Text>
              <Text style={styles.statValue}>{formatCurrency(billing.totalSpent)}</Text>
            </View>
            <View style={styles.balanceStat}>
              <Text style={styles.statLabel}>Total Top-ups</Text>
              <Text style={styles.statValue}>{formatCurrency(billing.totalToppedUp)}</Text>
            </View>
          </View>
        </View>
      )}

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Recent Transactions</Text>
        {transactions.length === 0 ? (
          <Text style={styles.emptyText}>No transactions yet</Text>
        ) : (
          transactions.map((txn) => (
            <View key={txn.id} style={styles.txnRow}>
              <View style={styles.txnLeft}>
                <View
                  style={[
                    styles.txnIcon,
                    {
                      backgroundColor:
                        txn.type === 'topup'
                          ? theme.colors.success + '20'
                          : txn.type === 'charge'
                          ? theme.colors.danger + '20'
                          : theme.colors.warning + '20',
                    },
                  ]}
                >
                  <Ionicons
                    name={
                      txn.type === 'topup'
                        ? 'arrow-down'
                        : txn.type === 'charge'
                        ? 'arrow-up'
                        : 'refresh'
                    }
                    size={16}
                    color={
                      txn.type === 'topup'
                        ? theme.colors.success
                        : txn.type === 'charge'
                        ? theme.colors.danger
                        : theme.colors.warning
                    }
                  />
                </View>
                <View>
                  <Text style={styles.txnDesc}>{txn.description}</Text>
                  <Text style={styles.txnDate}>{formatDate(txn.timestamp)}</Text>
                </View>
              </View>
              <Text
                style={[
                  styles.txnAmount,
                  {
                    color:
                      txn.type === 'topup'
                        ? theme.colors.success
                        : theme.colors.danger,
                  },
                ]}
              >
                {txn.type === 'topup' ? '+' : '-'}{formatCurrency(txn.amount)}
              </Text>
            </View>
          ))
        )}
      </View>
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
  balanceCard: {
    backgroundColor: theme.colors.surface,
    borderRadius: theme.borderRadius.lg,
    borderWidth: 1,
    borderColor: theme.colors.border,
    padding: theme.spacing.lg,
    marginBottom: theme.spacing.lg,
  },
  balanceLabel: {
    fontSize: theme.fontSize.sm,
    color: theme.colors.textSecondary,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  balanceAmount: {
    fontSize: 42,
    fontWeight: '800',
    color: theme.colors.text,
    marginVertical: theme.spacing.sm,
  },
  balanceStats: {
    flexDirection: 'row',
    gap: theme.spacing.md,
    paddingTop: theme.spacing.md,
    borderTopWidth: 1,
    borderTopColor: theme.colors.border,
  },
  balanceStat: {
    flex: 1,
  },
  statLabel: {
    fontSize: theme.fontSize.xs,
    color: theme.colors.textSecondary,
  },
  statValue: {
    fontSize: theme.fontSize.md,
    fontWeight: '700',
    color: theme.colors.text,
    marginTop: 2,
  },
  section: {
    marginBottom: theme.spacing.lg,
  },
  sectionTitle: {
    fontSize: theme.fontSize.lg,
    fontWeight: '700',
    color: theme.colors.text,
    marginBottom: theme.spacing.sm,
  },
  emptyText: {
    fontSize: theme.fontSize.sm,
    color: theme.colors.textSecondary,
    textAlign: 'center',
    paddingVertical: theme.spacing.xl,
  },
  txnRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: theme.colors.surface,
    borderRadius: theme.borderRadius.md,
    padding: theme.spacing.md,
    marginBottom: theme.spacing.xs,
    borderWidth: 1,
    borderColor: theme.colors.border,
  },
  txnLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.sm,
    flex: 1,
  },
  txnIcon: {
    width: 36,
    height: 36,
    borderRadius: 18,
    justifyContent: 'center',
    alignItems: 'center',
  },
  txnDesc: {
    fontSize: theme.fontSize.sm,
    color: theme.colors.text,
    fontWeight: '500',
  },
  txnDate: {
    fontSize: theme.fontSize.xs,
    color: theme.colors.textSecondary,
    marginTop: 2,
  },
  txnAmount: {
    fontSize: theme.fontSize.md,
    fontWeight: '700',
  },
});
