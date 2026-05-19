import React, { useState } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  TextInput, Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useKakeibo } from '../hooks/useKakeibo';
import { TransactionType } from '../types';

const COLORS = ['#FF6B6B', '#FF8C00', '#FFEAA7', '#51CF66', '#45B7D1', '#4ECDC4', '#55A3FF', '#DDA0DD', '#96CEB4', '#F08080'];
const ICONS = ['restaurant', 'train', 'shopping-cart', 'game-controller', 'flash', 'medical', 'briefcase', 'cash', 'home', 'car', 'fitness', 'book', 'beer', 'airplane', 'gift'];

interface Props {
  kakeibo: ReturnType<typeof useKakeibo>;
}

export default function CategoryScreen({ kakeibo }: Props) {
  const { categories, addCategory } = kakeibo;
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState('');
  const [selectedColor, setSelectedColor] = useState(COLORS[0]);
  const [selectedIcon, setSelectedIcon] = useState(ICONS[0]);
  const [type, setType] = useState<TransactionType>('expense');

  const handleAdd = async () => {
    if (!name.trim()) {
      Alert.alert('エラー', 'カテゴリ名を入力してください');
      return;
    }
    await addCategory({ name: name.trim(), color: selectedColor, icon: selectedIcon, type });
    setName('');
    setShowForm(false);
  };

  const expenseCategories = categories.filter(c => c.type === 'expense');
  const incomeCategories = categories.filter(c => c.type === 'income');

  const renderCategory = (cat: typeof categories[0]) => (
    <View key={cat.id} style={styles.catRow}>
      <View style={[styles.iconCircle, { backgroundColor: cat.color }]}>
        <Ionicons name={cat.icon as any} size={20} color="#fff" />
      </View>
      <Text style={styles.catName}>{cat.name}</Text>
    </View>
  );

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.scroll}>
      <View style={styles.header}>
        <Text style={styles.title}>カテゴリ管理</Text>
        <TouchableOpacity style={styles.addBtn} onPress={() => setShowForm(!showForm)}>
          <Ionicons name={showForm ? 'close' : 'add'} size={22} color="#fff" />
          <Text style={styles.addBtnText}>{showForm ? '閉じる' : '追加'}</Text>
        </TouchableOpacity>
      </View>

      {showForm && (
        <View style={styles.form}>
          <View style={styles.typeRow}>
            <TouchableOpacity
              style={[styles.typeBtn, type === 'expense' && styles.typeBtnActive]}
              onPress={() => setType('expense')}
            >
              <Text style={[styles.typeText, type === 'expense' && { color: '#fff' }]}>支出</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.typeBtn, type === 'income' && styles.typeBtnActiveIncome]}
              onPress={() => setType('income')}
            >
              <Text style={[styles.typeText, type === 'income' && { color: '#fff' }]}>収入</Text>
            </TouchableOpacity>
          </View>

          <TextInput
            style={styles.input}
            value={name}
            onChangeText={setName}
            placeholder="カテゴリ名"
            placeholderTextColor="#ccc"
          />

          <Text style={styles.sectionLabel}>色</Text>
          <View style={styles.colorRow}>
            {COLORS.map(c => (
              <TouchableOpacity
                key={c}
                style={[styles.colorDot, { backgroundColor: c }, selectedColor === c && styles.colorDotSelected]}
                onPress={() => setSelectedColor(c)}
              />
            ))}
          </View>

          <Text style={styles.sectionLabel}>アイコン</Text>
          <View style={styles.iconRow}>
            {ICONS.map(icon => (
              <TouchableOpacity
                key={icon}
                style={[styles.iconOption, selectedIcon === icon && { backgroundColor: selectedColor }]}
                onPress={() => setSelectedIcon(icon)}
              >
                <Ionicons name={icon as any} size={20} color={selectedIcon === icon ? '#fff' : '#555'} />
              </TouchableOpacity>
            ))}
          </View>

          <TouchableOpacity style={styles.saveBtn} onPress={handleAdd}>
            <Text style={styles.saveBtnText}>追加する</Text>
          </TouchableOpacity>
        </View>
      )}

      <Text style={styles.sectionTitle}>支出カテゴリ</Text>
      <View style={styles.catList}>{expenseCategories.map(renderCategory)}</View>

      <Text style={styles.sectionTitle}>収入カテゴリ</Text>
      <View style={styles.catList}>{incomeCategories.map(renderCategory)}</View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  scroll: { padding: 16, paddingBottom: 32 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 },
  title: { fontSize: 20, fontWeight: 'bold', color: '#333' },
  addBtn: {
    flexDirection: 'row', alignItems: 'center', gap: 4,
    backgroundColor: '#45B7D1', paddingHorizontal: 14, paddingVertical: 8, borderRadius: 20,
  },
  addBtnText: { color: '#fff', fontWeight: '600' },
  form: {
    backgroundColor: '#fff', borderRadius: 14, padding: 16, marginBottom: 20,
    shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.06, shadowRadius: 4, elevation: 2,
  },
  typeRow: { flexDirection: 'row', marginBottom: 12, borderRadius: 8, overflow: 'hidden', backgroundColor: '#eee' },
  typeBtn: { flex: 1, paddingVertical: 8, alignItems: 'center' },
  typeBtnActive: { backgroundColor: '#FF6B6B' },
  typeBtnActiveIncome: { backgroundColor: '#51CF66' },
  typeText: { color: '#888', fontWeight: '600' },
  input: {
    borderWidth: 1, borderColor: '#e0e0e0', borderRadius: 8, padding: 10,
    fontSize: 15, color: '#333', marginBottom: 12,
  },
  sectionLabel: { fontSize: 12, color: '#888', marginBottom: 6, fontWeight: '600' },
  colorRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 12 },
  colorDot: { width: 28, height: 28, borderRadius: 14 },
  colorDotSelected: { borderWidth: 3, borderColor: '#333' },
  iconRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 14 },
  iconOption: { width: 38, height: 38, borderRadius: 8, alignItems: 'center', justifyContent: 'center', backgroundColor: '#f0f0f0' },
  saveBtn: { backgroundColor: '#45B7D1', borderRadius: 10, paddingVertical: 12, alignItems: 'center' },
  saveBtnText: { color: '#fff', fontWeight: 'bold', fontSize: 15 },
  sectionTitle: { fontSize: 15, fontWeight: '700', color: '#555', marginBottom: 10, marginTop: 8 },
  catList: { backgroundColor: '#fff', borderRadius: 14, padding: 8, marginBottom: 16 },
  catRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 8, paddingHorizontal: 6 },
  iconCircle: { width: 36, height: 36, borderRadius: 18, alignItems: 'center', justifyContent: 'center', marginRight: 12 },
  catName: { fontSize: 15, color: '#333' },
});
