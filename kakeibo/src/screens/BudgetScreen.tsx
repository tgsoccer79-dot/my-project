import React, { useState } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  TextInput, Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { format, subMonths, addMonths } from 'date-fns';
import { ja } from 'date-fns/locale';
import { useKakeibo } from '../hooks/useKakeibo';

interface Props {
  kakeibo: ReturnType<typeof useKakeibo>;
}

export default function BudgetScreen({ kakeibo }: Props) {
  const [currentMonth, setCurrentMonth] = useState(format(new Date(), 'yyyy-MM'));
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState('');

  const { categories, setBudget, getBudgetForCategory, getCategorySpending } = kakeibo;

  const expenseCategories = categories.filter(c => c.type === 'expense');
  const spending = getCategorySpending(currentMonth);
  const displayMonth = format(new Date(currentMonth + '-01'), 'yyyy年M月', { locale: ja });

  const handleSaveBudget = async (categoryId: string) => {
    const amount = Number(editValue);
    if (isNaN(amount) || amount < 0) {
      Alert.alert('エラー', '正しい金額を入力してください');
      return;
    }
    await setBudget({ categoryId, amount, month: currentMonth });
    setEditingId(null);
    setEditValue('');
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.scroll}>
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

      <Text style={styles.hint}>カテゴリをタップして予算を設定</Text>

      {expenseCategories.map(cat => {
        const budget = getBudgetForCategory(cat.id, currentMonth);
        const spent = spending[cat.id] || 0;
        const budgetAmt = budget?.amount ?? 0;
        const progress = budgetAmt > 0 ? Math.min(spent / budgetAmt, 1) : 0;
        const isOver = budgetAmt > 0 && spent > budgetAmt;
        const isEditing = editingId === cat.id;

        return (
          <View key={cat.id} style={styles.card}>
            <View style={styles.cardHeader}>
              <View style={[styles.iconCircle, { backgroundColor: cat.color }]}>
                <Ionicons name={cat.icon as any} size={18} color="#fff" />
              </View>
              <View style={styles.cardInfo}>
                <Text style={styles.catName}>{cat.name}</Text>
                <Text style={styles.spentText}>
                  ¥{spent.toLocaleString()} 使用
                  {budgetAmt > 0 && ` / ¥${budgetAmt.toLocaleString()} 予算`}
                </Text>
              </View>
              <TouchableOpacity
                onPress={() => {
                  setEditingId(isEditing ? null : cat.id);
                  setEditValue(budgetAmt > 0 ? String(budgetAmt) : '');
                }}
              >
                <Ionicons name={isEditing ? 'close' : 'pencil'} size={20} color="#888" />
              </TouchableOpacity>
            </View>

            {budgetAmt > 0 && (
              <View style={styles.progressBg}>
                <View style={[
                  styles.progressFill,
                  { width: `${progress * 100}%` as any, backgroundColor: isOver ? '#FF6B6B' : cat.color },
                ]} />
              </View>
            )}

            {isOver && (
              <Text style={styles.overText}>
                ¥{(spent - budgetAmt).toLocaleString()} 超過！
              </Text>
            )}

            {isEditing && (
              <View style={styles.editRow}>
                <TextInput
                  style={styles.editInput}
                  value={editValue}
                  onChangeText={setEditValue}
                  keyboardType="numeric"
                  placeholder="予算を入力"
                  placeholderTextColor="#ccc"
                  autoFocus
                />
                <TouchableOpacity
                  style={styles.saveBtn}
                  onPress={() => handleSaveBudget(cat.id)}
                >
                  <Text style={styles.saveBtnText}>保存</Text>
                </TouchableOpacity>
              </View>
            )}
          </View>
        );
      })}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  scroll: { paddingBottom: 32 },
  monthRow: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    backgroundColor: '#45B7D1', paddingHorizontal: 20, paddingVertical: 14,
  },
  monthText: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
  hint: { textAlign: 'center', color: '#999', marginVertical: 12, fontSize: 13 },
  card: {
    backgroundColor: '#fff', marginHorizontal: 12, marginBottom: 10, borderRadius: 14,
    padding: 14, shadowColor: '#000', shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06, shadowRadius: 3, elevation: 2,
  },
  cardHeader: { flexDirection: 'row', alignItems: 'center' },
  iconCircle: { width: 38, height: 38, borderRadius: 19, alignItems: 'center', justifyContent: 'center', marginRight: 10 },
  cardInfo: { flex: 1 },
  catName: { fontSize: 15, fontWeight: '600', color: '#333' },
  spentText: { fontSize: 12, color: '#888', marginTop: 2 },
  progressBg: { height: 6, backgroundColor: '#eee', borderRadius: 3, marginTop: 10 },
  progressFill: { height: 6, borderRadius: 3 },
  overText: { color: '#FF6B6B', fontSize: 12, fontWeight: '600', marginTop: 6 },
  editRow: { flexDirection: 'row', alignItems: 'center', marginTop: 10, gap: 8 },
  editInput: {
    flex: 1, borderWidth: 1.5, borderColor: '#45B7D1', borderRadius: 8,
    paddingHorizontal: 10, paddingVertical: 6, fontSize: 15, color: '#333',
  },
  saveBtn: { backgroundColor: '#45B7D1', paddingHorizontal: 14, paddingVertical: 8, borderRadius: 8 },
  saveBtnText: { color: '#fff', fontWeight: '600' },
});
