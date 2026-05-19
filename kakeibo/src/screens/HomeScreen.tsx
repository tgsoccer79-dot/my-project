import React, { useState } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  FlatList, Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { format, subMonths, addMonths } from 'date-fns';
import { ja } from 'date-fns/locale';
import { useKakeibo } from '../hooks/useKakeibo';
import { Transaction } from '../types';

interface Props {
  navigation: any;
  kakeibo: ReturnType<typeof useKakeibo>;
}

export default function HomeScreen({ navigation, kakeibo }: Props) {
  const [currentMonth, setCurrentMonth] = useState(format(new Date(), 'yyyy-MM'));
  const { transactions, categories, deleteTransaction, getMonthlyStats } = kakeibo;

  const stats = getMonthlyStats(currentMonth);
  const monthTxs = transactions
    .filter(t => t.date.startsWith(currentMonth))
    .sort((a, b) => b.date.localeCompare(a.date));

  const getCategoryName = (id: string) => categories.find(c => c.id === id)?.name ?? '-';
  const getCategoryColor = (id: string) => categories.find(c => c.id === id)?.color ?? '#888';
  const getCategoryIcon = (id: string) => (categories.find(c => c.id === id)?.icon ?? 'ellipse') as any;

  const formatAmount = (amount: number) =>
    `¥${amount.toLocaleString()}`;

  const handleDelete = (tx: Transaction) => {
    Alert.alert('削除確認', `この取引を削除しますか？\n${getCategoryName(tx.categoryId)} ${formatAmount(tx.amount)}`, [
      { text: 'キャンセル', style: 'cancel' },
      { text: '削除', style: 'destructive', onPress: () => deleteTransaction(tx.id) },
    ]);
  };

  const displayMonth = format(new Date(currentMonth + '-01'), 'yyyy年M月', { locale: ja });

  return (
    <View style={styles.container}>
      {/* Month selector */}
      <View style={styles.monthRow}>
        <TouchableOpacity onPress={() => setCurrentMonth(format(subMonths(new Date(currentMonth + '-01'), 1), 'yyyy-MM'))}>
          <Ionicons name="chevron-back" size={24} color="#fff" />
        </TouchableOpacity>
        <Text style={styles.monthText}>{displayMonth}</Text>
        <TouchableOpacity onPress={() => setCurrentMonth(format(addMonths(new Date(currentMonth + '-01'), 1), 'yyyy-MM'))}>
          <Ionicons name="chevron-forward" size={24} color="#fff" />
        </TouchableOpacity>
      </View>

      {/* Balance cards */}
      <View style={styles.statsRow}>
        <View style={[styles.statCard, { backgroundColor: '#51CF66' }]}>
          <Text style={styles.statLabel}>収入</Text>
          <Text style={styles.statAmount}>{formatAmount(stats.totalIncome)}</Text>
        </View>
        <View style={[styles.statCard, { backgroundColor: '#FF6B6B' }]}>
          <Text style={styles.statLabel}>支出</Text>
          <Text style={styles.statAmount}>{formatAmount(stats.totalExpense)}</Text>
        </View>
        <View style={[styles.statCard, { backgroundColor: stats.balance >= 0 ? '#45B7D1' : '#FF8C00' }]}>
          <Text style={styles.statLabel}>残高</Text>
          <Text style={styles.statAmount}>{formatAmount(stats.balance)}</Text>
        </View>
      </View>

      {/* Transaction list */}
      <FlatList
        data={monthTxs}
        keyExtractor={item => item.id}
        contentContainerStyle={styles.list}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Ionicons name="receipt-outline" size={48} color="#ccc" />
            <Text style={styles.emptyText}>この月の取引はありません</Text>
          </View>
        }
        renderItem={({ item }) => (
          <TouchableOpacity
            style={styles.txItem}
            onLongPress={() => handleDelete(item)}
          >
            <View style={[styles.txIcon, { backgroundColor: getCategoryColor(item.categoryId) }]}>
              <Ionicons name={getCategoryIcon(item.categoryId)} size={20} color="#fff" />
            </View>
            <View style={styles.txInfo}>
              <Text style={styles.txCategory}>{getCategoryName(item.categoryId)}</Text>
              {item.memo ? <Text style={styles.txMemo}>{item.memo}</Text> : null}
              <Text style={styles.txDate}>{item.date}</Text>
            </View>
            <Text style={[
              styles.txAmount,
              { color: item.type === 'income' ? '#51CF66' : '#FF6B6B' }
            ]}>
              {item.type === 'income' ? '+' : '-'}{formatAmount(item.amount)}
            </Text>
          </TouchableOpacity>
        )}
      />

      {/* FAB */}
      <TouchableOpacity
        style={styles.fab}
        onPress={() => navigation.navigate('AddTransaction', { kakeibo })}
      >
        <Ionicons name="add" size={32} color="#fff" />
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  monthRow: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    backgroundColor: '#45B7D1', paddingHorizontal: 20, paddingVertical: 14,
  },
  monthText: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
  statsRow: { flexDirection: 'row', padding: 12, gap: 8 },
  statCard: {
    flex: 1, borderRadius: 12, padding: 12, alignItems: 'center',
  },
  statLabel: { color: '#fff', fontSize: 12, marginBottom: 4 },
  statAmount: { color: '#fff', fontSize: 14, fontWeight: 'bold' },
  list: { paddingHorizontal: 12, paddingBottom: 80 },
  txItem: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: '#fff',
    borderRadius: 12, padding: 12, marginBottom: 8,
    shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.05, shadowRadius: 2, elevation: 2,
  },
  txIcon: { width: 40, height: 40, borderRadius: 20, alignItems: 'center', justifyContent: 'center', marginRight: 12 },
  txInfo: { flex: 1 },
  txCategory: { fontSize: 15, fontWeight: '600', color: '#333' },
  txMemo: { fontSize: 12, color: '#888', marginTop: 2 },
  txDate: { fontSize: 11, color: '#bbb', marginTop: 2 },
  txAmount: { fontSize: 16, fontWeight: 'bold' },
  empty: { alignItems: 'center', paddingTop: 60 },
  emptyText: { color: '#bbb', marginTop: 12, fontSize: 15 },
  fab: {
    position: 'absolute', bottom: 24, right: 24,
    width: 60, height: 60, borderRadius: 30,
    backgroundColor: '#45B7D1', alignItems: 'center', justifyContent: 'center',
    shadowColor: '#000', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.3, shadowRadius: 6, elevation: 8,
  },
});
