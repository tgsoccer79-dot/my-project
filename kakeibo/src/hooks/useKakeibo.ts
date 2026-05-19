import { useState, useEffect, useCallback } from 'react';
import { Transaction, Category, Budget } from '../types';
import {
  loadTransactions, saveTransactions,
  loadCategories, saveCategories,
  loadBudgets, saveBudgets,
} from '../utils/storage';
import { format } from 'date-fns';

export function useKakeibo() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [budgets, setBudgets] = useState<Budget[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      const [t, c, b] = await Promise.all([
        loadTransactions(),
        loadCategories(),
        loadBudgets(),
      ]);
      setTransactions(t);
      setCategories(c);
      setBudgets(b);
      setLoading(false);
    })();
  }, []);

  const addTransaction = useCallback(async (tx: Omit<Transaction, 'id'>) => {
    const newTx: Transaction = { ...tx, id: Date.now().toString() };
    const updated = [newTx, ...transactions];
    setTransactions(updated);
    await saveTransactions(updated);
  }, [transactions]);

  const deleteTransaction = useCallback(async (id: string) => {
    const updated = transactions.filter(t => t.id !== id);
    setTransactions(updated);
    await saveTransactions(updated);
  }, [transactions]);

  const addCategory = useCallback(async (cat: Omit<Category, 'id'>) => {
    const newCat: Category = { ...cat, id: Date.now().toString() };
    const updated = [...categories, newCat];
    setCategories(updated);
    await saveCategories(updated);
  }, [categories]);

  const setBudget = useCallback(async (budget: Budget) => {
    const updated = budgets.filter(
      b => !(b.categoryId === budget.categoryId && b.month === budget.month)
    );
    updated.push(budget);
    setBudgets(updated);
    await saveBudgets(updated);
  }, [budgets]);

  const getMonthlyStats = useCallback((month: string) => {
    const monthTxs = transactions.filter(t => t.date.startsWith(month));
    const totalIncome = monthTxs.filter(t => t.type === 'income').reduce((s, t) => s + t.amount, 0);
    const totalExpense = monthTxs.filter(t => t.type === 'expense').reduce((s, t) => s + t.amount, 0);
    return { month, totalIncome, totalExpense, balance: totalIncome - totalExpense };
  }, [transactions]);

  const getCategorySpending = useCallback((month: string) => {
    const monthTxs = transactions.filter(t => t.date.startsWith(month) && t.type === 'expense');
    const map: Record<string, number> = {};
    for (const tx of monthTxs) {
      map[tx.categoryId] = (map[tx.categoryId] || 0) + tx.amount;
    }
    return map;
  }, [transactions]);

  const getBudgetForCategory = useCallback((categoryId: string, month: string) => {
    return budgets.find(b => b.categoryId === categoryId && b.month === month);
  }, [budgets]);

  return {
    transactions, categories, budgets, loading,
    addTransaction, deleteTransaction,
    addCategory,
    setBudget, getBudgetForCategory,
    getMonthlyStats, getCategorySpending,
  };
}
