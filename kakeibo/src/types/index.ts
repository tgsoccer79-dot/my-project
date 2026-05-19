export type TransactionType = 'income' | 'expense';

export interface Category {
  id: string;
  name: string;
  icon: string;
  color: string;
  type: TransactionType;
}

export interface Transaction {
  id: string;
  type: TransactionType;
  amount: number;
  categoryId: string;
  memo: string;
  date: string; // ISO date string
}

export interface Budget {
  categoryId: string;
  amount: number;
  month: string; // YYYY-MM
}

export interface MonthlyStats {
  month: string;
  totalIncome: number;
  totalExpense: number;
  balance: number;
}
