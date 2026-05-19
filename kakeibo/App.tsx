import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import { Ionicons } from '@expo/vector-icons';
import { View, ActivityIndicator } from 'react-native';

import HomeScreen from './src/screens/HomeScreen';
import StatsScreen from './src/screens/StatsScreen';
import BudgetScreen from './src/screens/BudgetScreen';
import CategoryScreen from './src/screens/CategoryScreen';
import AddTransactionScreen from './src/screens/AddTransactionScreen';
import { useKakeibo } from './src/hooks/useKakeibo';

const Tab = createBottomTabNavigator();
const Stack = createStackNavigator();

function MainTabs({ kakeibo, navigation }: { kakeibo: ReturnType<typeof useKakeibo>; navigation: any }) {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          const icons: Record<string, string> = {
            ホーム: focused ? 'home' : 'home-outline',
            グラフ: focused ? 'bar-chart' : 'bar-chart-outline',
            予算: focused ? 'wallet' : 'wallet-outline',
            カテゴリ: focused ? 'grid' : 'grid-outline',
          };
          return <Ionicons name={(icons[route.name] ?? 'ellipse') as any} size={size} color={color} />;
        },
        tabBarActiveTintColor: '#45B7D1',
        tabBarInactiveTintColor: '#aaa',
        headerStyle: { backgroundColor: '#45B7D1' },
        headerTintColor: '#fff',
        headerTitleStyle: { fontWeight: 'bold' },
      })}
    >
      <Tab.Screen name="ホーム">
        {() => <HomeScreen navigation={navigation} kakeibo={kakeibo} />}
      </Tab.Screen>
      <Tab.Screen name="グラフ">
        {() => <StatsScreen kakeibo={kakeibo} />}
      </Tab.Screen>
      <Tab.Screen name="予算">
        {() => <BudgetScreen kakeibo={kakeibo} />}
      </Tab.Screen>
      <Tab.Screen name="カテゴリ">
        {() => <CategoryScreen kakeibo={kakeibo} />}
      </Tab.Screen>
    </Tab.Navigator>
  );
}

export default function App() {
  const kakeibo = useKakeibo();

  if (kakeibo.loading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" color="#45B7D1" />
      </View>
    );
  }

  return (
    <NavigationContainer>
      <StatusBar style="light" />
      <Stack.Navigator>
        <Stack.Screen name="Main" options={{ headerShown: false }}>
          {({ navigation }) => <MainTabs kakeibo={kakeibo} navigation={navigation} />}
        </Stack.Screen>
        <Stack.Screen
          name="AddTransaction"
          options={{
            title: '取引を追加',
            headerStyle: { backgroundColor: '#45B7D1' },
            headerTintColor: '#fff',
            headerTitleStyle: { fontWeight: 'bold' },
          }}
        >
          {(props) => <AddTransactionScreen {...props} />}
        </Stack.Screen>
      </Stack.Navigator>
    </NavigationContainer>
  );
}
