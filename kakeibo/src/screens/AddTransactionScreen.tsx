import React, { useState } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, TextInput,
  ScrollView, Alert, KeyboardAvoidingView, Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { format } from 'date-fns';
import { TransactionType } from '../types';
import { useKakeibo } from '../hooks/useKakeibo';

interface Props {
  navigation: any;
  route: any;
}

export default function AddTransactionScreen({ navigation, route }: Props) {
  const { kakeibo } = route.params;
  const { categories, addTransaction } = kakeibo;

  const [type, setType] = useState<TransactionType>('expense');
  const [amount, setAmount] = useState('');
  const [selectedCategoryId, setSelectedCategoryId] = useState('');
  const [memo, setMemo] = useState('');
  const [date, setDate] = useState(format(new Date(), 'yyyy-MM-dd'));

  const filteredCategories: import('../types').Category[] = categories.filter((c: import('../types').Category) => c.type === type);

  const handleSave = async () => {
    if (!amount || isNaN(Number(amount)) || Number(amount) <= 0) {
      Alert.alert('エラー', '金額を正しく入力してください');
      return;
    }
    if (!selectedCategoryId) {
      Alert.alert('エラー', 'カテゴリを選択してください');
      return;
    }
    await addTransaction({
      type,
      amount: Number(amount),
      categoryId: selectedCategoryId,
      memo,
      date,
    });
    navigation.goBack();
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView contentContainerStyle={styles.scroll}>
        {/* Type toggle */}
        <View style={styles.typeRow}>
          <TouchableOpacity
            style={[styles.typeBtn, type === 'expense' && styles.typeBtnActive]}
            onPress={() => { setType('expense'); setSelectedCategoryId(''); }}
          >
            <Text style={[styles.typeText, type === 'expense' && styles.typeTextActive]}>支出</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.typeBtn, type === 'income' && styles.typeBtnActiveIncome]}
            onPress={() => { setType('income'); setSelectedCategoryId(''); }}
          >
            <Text style={[styles.typeText, type === 'income' && styles.typeTextActive]}>収入</Text>
          </TouchableOpacity>
        </View>

        {/* Amount */}
        <View style={styles.section}>
          <Text style={styles.label}>金額</Text>
          <TextInput
            style={styles.amountInput}
            value={amount}
            onChangeText={setAmount}
            keyboardType="numeric"
            placeholder="0"
            placeholderTextColor="#ccc"
          />
        </View>

        {/* Date */}
        <View style={styles.section}>
          <Text style={styles.label}>日付</Text>
          <TextInput
            style={styles.input}
            value={date}
            onChangeText={setDate}
            placeholder="yyyy-MM-dd"
            placeholderTextColor="#ccc"
          />
        </View>

        {/* Category */}
        <View style={styles.section}>
          <Text style={styles.label}>カテゴリ</Text>
          <View style={styles.categoryGrid}>
            {filteredCategories.map(cat => (
              <TouchableOpacity
                key={cat.id}
                style={[
                  styles.categoryChip,
                  selectedCategoryId === cat.id && { backgroundColor: cat.color, borderColor: cat.color },
                ]}
                onPress={() => setSelectedCategoryId(cat.id)}
              >
                <Ionicons
                  name={cat.icon as any}
                  size={18}
                  color={selectedCategoryId === cat.id ? '#fff' : cat.color}
                />
                <Text style={[
                  styles.categoryChipText,
                  selectedCategoryId === cat.id && { color: '#fff' },
                ]}>
                  {cat.name}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Memo */}
        <View style={styles.section}>
          <Text style={styles.label}>メモ（任意）</Text>
          <TextInput
            style={styles.input}
            value={memo}
            onChangeText={setMemo}
            placeholder="メモを入力..."
            placeholderTextColor="#ccc"
          />
        </View>

        {/* Save button */}
        <TouchableOpacity style={styles.saveBtn} onPress={handleSave}>
          <Text style={styles.saveBtnText}>保存</Text>
        </TouchableOpacity>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  scroll: { padding: 16 },
  typeRow: { flexDirection: 'row', marginBottom: 20, borderRadius: 12, overflow: 'hidden', backgroundColor: '#e0e0e0' },
  typeBtn: { flex: 1, paddingVertical: 12, alignItems: 'center' },
  typeBtnActive: { backgroundColor: '#FF6B6B' },
  typeBtnActiveIncome: { backgroundColor: '#51CF66' },
  typeText: { fontSize: 15, color: '#888', fontWeight: '600' },
  typeTextActive: { color: '#fff' },
  section: { marginBottom: 20 },
  label: { fontSize: 13, color: '#888', marginBottom: 6, fontWeight: '600' },
  amountInput: {
    fontSize: 32, fontWeight: 'bold', color: '#333',
    borderBottomWidth: 2, borderBottomColor: '#45B7D1', paddingBottom: 4,
  },
  input: {
    backgroundColor: '#fff', borderRadius: 10, padding: 12,
    fontSize: 15, color: '#333',
  },
  categoryGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  categoryChip: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    paddingHorizontal: 12, paddingVertical: 8, borderRadius: 20,
    backgroundColor: '#fff', borderWidth: 1.5, borderColor: '#e0e0e0',
  },
  categoryChipText: { fontSize: 13, color: '#555', fontWeight: '500' },
  saveBtn: {
    backgroundColor: '#45B7D1', borderRadius: 14, paddingVertical: 16,
    alignItems: 'center', marginTop: 8,
  },
  saveBtnText: { color: '#fff', fontSize: 17, fontWeight: 'bold' },
});
