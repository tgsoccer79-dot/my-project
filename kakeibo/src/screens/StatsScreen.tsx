import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Dimensions } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { PieChart, BarChart } from 'react-native-chart-kit';
import { format, subMonths, addMonths } from 'date-fns';
import { ja } from 'date-fns/locale';
import { useKakeibo } from '../hooks/useKakeibo';

const SCREEN_WIDTH = Dimensions.get('window').width;

interface Props {
  kakeibo: ReturnType<typeof useKakeibo>;
}

export default function StatsScreen({ kakeibo }: Props) {
  const [currentMonth, setCurrentMonth] = useState(format(new Date(), 'yyyy-MM'));
  const { categories, getMonthlyStats, getCategorySpending } = kakeibo;

  const stats = getMonthlyStats(currentMonth);
  const spending = getCategorySpending(currentMonth);
  const displayMonth = format(new Date(currentMonth + '-01'), 'yyyy年M月', { locale: ja });

  // Pie chart data for expenses by category
  const pieData = Object.entries(spending)
    .filter(([, amt]) => amt > 0)
    .map(([catId, amount]) => {
      const cat = categories.find(c => c.id === catId);
      return {
        name: cat?.name ?? '',
        amount,
        color: cat?.color ?? '#888',
        legendFontColor: '#555',
        legendFontSize: 12,
      };
    })
    .sort((a, b) => b.amount - a.amount);

  // Last 6 months bar chart
  const last6 = Array.from({ length: 6 }, (_, i) => {
    const m = format(subMonths(new Date(currentMonth + '-01'), 5 - i), 'yyyy-MM');
    const s = getMonthlyStats(m);
    return { month: format(new Date(m + '-01'), 'M月'), income: s.totalIncome, expense: s.totalExpense };
  });

  const barData = {
    labels: last6.map(d => d.month),
    datasets: [
      { data: last6.map(d => d.expense), color: () => '#FF6B6B' },
    ],
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

      {/* Summary */}
      <View style={styles.summaryCard}>
        <View style={styles.summaryItem}>
          <Text style={styles.summaryLabel}>収入</Text>
          <Text style={[styles.summaryValue, { color: '#51CF66' }]}>¥{stats.totalIncome.toLocaleString()}</Text>
        </View>
        <View style={styles.summaryDivider} />
        <View style={styles.summaryItem}>
          <Text style={styles.summaryLabel}>支出</Text>
          <Text style={[styles.summaryValue, { color: '#FF6B6B' }]}>¥{stats.totalExpense.toLocaleString()}</Text>
        </View>
        <View style={styles.summaryDivider} />
        <View style={styles.summaryItem}>
          <Text style={styles.summaryLabel}>収支</Text>
          <Text style={[styles.summaryValue, { color: stats.balance >= 0 ? '#45B7D1' : '#FF8C00' }]}>
            ¥{stats.balance.toLocaleString()}
          </Text>
        </View>
      </View>

      {/* Pie chart */}
      {pieData.length > 0 && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>カテゴリ別支出</Text>
          <PieChart
            data={pieData}
            width={SCREEN_WIDTH - 32}
            height={200}
            chartConfig={chartConfig}
            accessor="amount"
            backgroundColor="transparent"
            paddingLeft="0"
            center={[0, 0]}
          />
        </View>
      )}

      {/* Bar chart */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>過去6ヶ月の支出</Text>
        <BarChart
          data={barData}
          width={SCREEN_WIDTH - 48}
          height={200}
          chartConfig={chartConfig}
          yAxisLabel="¥"
          yAxisSuffix=""
          showValuesOnTopOfBars={false}
          fromZero
        />
      </View>

      {/* Category breakdown list */}
      {pieData.length > 0 && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>内訳</Text>
          {pieData.map(item => {
            const pct = stats.totalExpense > 0 ? Math.round((item.amount / stats.totalExpense) * 100) : 0;
            return (
              <View key={item.name} style={styles.breakdownRow}>
                <View style={[styles.dot, { backgroundColor: item.color }]} />
                <Text style={styles.breakdownName}>{item.name}</Text>
                <Text style={styles.breakdownPct}>{pct}%</Text>
                <Text style={styles.breakdownAmt}>¥{item.amount.toLocaleString()}</Text>
              </View>
            );
          })}
        </View>
      )}
    </ScrollView>
  );
}

const chartConfig = {
  backgroundGradientFrom: '#fff',
  backgroundGradientTo: '#fff',
  color: (opacity = 1) => `rgba(69, 183, 209, ${opacity})`,
  labelColor: () => '#555',
  strokeWidth: 2,
  decimalPlaces: 0,
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  scroll: { paddingBottom: 32 },
  monthRow: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    backgroundColor: '#45B7D1', paddingHorizontal: 20, paddingVertical: 14,
  },
  monthText: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
  summaryCard: {
    flexDirection: 'row', backgroundColor: '#fff', margin: 12, borderRadius: 14,
    padding: 16, shadowColor: '#000', shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.07, shadowRadius: 4, elevation: 3,
  },
  summaryItem: { flex: 1, alignItems: 'center' },
  summaryLabel: { fontSize: 12, color: '#888', marginBottom: 4 },
  summaryValue: { fontSize: 16, fontWeight: 'bold' },
  summaryDivider: { width: 1, backgroundColor: '#eee' },
  card: {
    backgroundColor: '#fff', marginHorizontal: 12, marginBottom: 12, borderRadius: 14,
    padding: 16, shadowColor: '#000', shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.07, shadowRadius: 4, elevation: 3,
  },
  cardTitle: { fontSize: 15, fontWeight: '700', color: '#333', marginBottom: 12 },
  breakdownRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 6 },
  dot: { width: 10, height: 10, borderRadius: 5, marginRight: 8 },
  breakdownName: { flex: 1, fontSize: 14, color: '#444' },
  breakdownPct: { fontSize: 13, color: '#888', marginRight: 12 },
  breakdownAmt: { fontSize: 14, fontWeight: '600', color: '#333' },
});
