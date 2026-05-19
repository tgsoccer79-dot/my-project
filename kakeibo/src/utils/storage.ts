import AsyncStorage from '@react-native-async-storage/async-storage';
import { Transaction, Category, Budget } from '../types';

const KEYS = {
  TRANSACTIONS: 'kakeibo_transactions',
  CATEGORIES: 'kakeibo_categories',
  BUDGETS: 'kakeibo_budgets',
};

const DEFAULT_CATEGORIES: Category[] = [
  { id: '1', name: '食費', icon: 'restaurant', color: '#FF6B6B', type: 'expense' },
  { id: '2', name: '交通費', icon: 'train', color: '#4ECDC4', type: 'expense' },
  { id: '3', name: '日用品', icon: 'shopping-cart', color: '#45B7D1', type: 'expense' },
  { id: '4', name: '娯楽', icon: 'game-controller', color: '#96CEB4', type: 'expense' },
  { id: '5', name: '光熱費', icon: 'flash', color: '#FFEAA7', type: 'expense' },
  { id: '6', name: '医療費', icon: 'medical', color: '#DDA0DD', type: 'expense' },
  { id: '7', name: '給与', icon: 'briefcase', color: '#55A3FF', type: 'income' },
  { id: '8', name: '副収入', icon: 'cash', color: '#51CF66', type: 'income' },
];

export async function loadTransactions(): Promise<Transaction[]> {
  const data = await AsyncStorage.getItem(KEYS.TRANSACTIONS);
  return data ? JSON.parse(data) : [];
}

export async function saveTransactions(transactions: Transaction[]): Promise<void> {
  await AsyncStorage.setItem(KEYS.TRANSACTIONS, JSON.stringify(transactions));
}

export async function loadCategories(): Promise<Category[]> {
  const data = await AsyncStorage.getItem(KEYS.CATEGORIES);
  if (!data) {
    await AsyncStorage.setItem(KEYS.CATEGORIES, JSON.stringify(DEFAULT_CATEGORIES));
    return DEFAULT_CATEGORIES;
  }
  return JSON.parse(data);
}

export async function saveCategories(categories: Category[]): Promise<void> {
  await AsyncStorage.setItem(KEYS.CATEGORIES, JSON.stringify(categories));
}

export async function loadBudgets(): Promise<Budget[]> {
  const data = await AsyncStorage.getItem(KEYS.BUDGETS);
  return data ? JSON.parse(data) : [];
}

export async function saveBudgets(budgets: Budget[]): Promise<void> {
  await AsyncStorage.setItem(KEYS.BUDGETS, JSON.stringify(budgets));
}
