import { View, Text, ScrollView, RefreshControl } from 'react-native';
import { GlassCard } from '@/components/ui/GlassCard';
import { DeepSpaceBackground } from '@/components/ui/DeepSpaceBackground';
import { useState, useEffect } from 'react';
import { supabase } from '@/utils/supabaseClient';
import { Stack } from 'expo-router';

export default function FinancialsScreen() {
    const [metrics, setMetrics] = useState({
        revenue: 0,
        pending: 0,
        expenses: 0
    });
    const [refreshing, setRefreshing] = useState(false);

    const fetchData = async () => {
        setRefreshing(true);
        // Revenue: Sum of final_settlement_amount of Closed projects
        const { data: projects } = await supabase.from('projects').select('final_settlement_amount, status');
        // Pending: Sum of final_settlement_amount of Active projects (Projected)

        // Expenses: If expenses table exists, sum amount. If not, use 0.
        // Assuming 'expenses' table exists as per app.py 'Expenses' tab.
        const { data: expenses } = await supabase.from('expenses').select('amount');

        if (projects) {
            const revenue = projects
                .filter(p => ['Closed', 'Work Done'].includes(p.status))
                .reduce((acc, p) => acc + (p.final_settlement_amount || 0), 0);

            const pending = projects
                .filter(p => !['Closed', 'Work Done'].includes(p.status))
                .reduce((acc, p) => acc + (p.final_settlement_amount || 0), 0);

            let totalExp = 0;
            if (expenses) {
                totalExp = expenses.reduce((acc, e) => acc + (e.amount || 0), 0);
            }

            setMetrics({ revenue, pending, expenses: totalExp });
        }
        setRefreshing(false);
    };

    useEffect(() => {
        fetchData();
    }, []);

    const profit = metrics.revenue - metrics.expenses;

    return (
        <DeepSpaceBackground>
            <Stack.Screen options={{ title: 'Financials', headerStyle: { backgroundColor: '#0E1117' }, headerTintColor: '#fff' }} />
            <ScrollView
                className="flex-1 p-4"
                refreshControl={<RefreshControl refreshing={refreshing} onRefresh={fetchData} tintColor="#fff" />}
            >
                <Text className="text-3xl font-bold text-white mb-6">Financials</Text>

                <View className="flex-row gap-4 mb-4">
                    <GlassCard className="flex-1 bg-green-900/20 border-green-500/30">
                        <Text className="text-green-400 text-xs uppercase font-bold">Total Revenue</Text>
                        <Text className="text-2xl font-bold text-white mt-1">₹{metrics.revenue.toLocaleString()}</Text>
                    </GlassCard>
                    <GlassCard className="flex-1 bg-red-900/20 border-red-500/30">
                        <Text className="text-red-400 text-xs uppercase font-bold">Total Expenses</Text>
                        <Text className="text-2xl font-bold text-white mt-1">₹{metrics.expenses.toLocaleString()}</Text>
                    </GlassCard>
                </View>

                <GlassCard className="mb-6 bg-blue-900/20 border-blue-500/30">
                    <Text className="text-blue-400 text-xs uppercase font-bold">Net Profit</Text>
                    <Text className="text-4xl font-bold text-white mt-2">₹{profit.toLocaleString()}</Text>
                </GlassCard>

                <GlassCard className="mb-6">
                    <Text className="text-slate-400 text-xs uppercase font-bold">Projected Revenue (Active)</Text>
                    <Text className="text-2xl font-bold text-slate-200 mt-1">₹{metrics.pending.toLocaleString()}</Text>
                    <Text className="text-muted text-xs mt-2">Value of currently active projects</Text>
                </GlassCard>

                {/* Coming Soon Charts */}
                <GlassCard className="bg-white/5 border-dashed border-white/20 items-center justify-center p-8">
                    <Text className="text-slate-500 font-bold">Detailed Charts Coming Soon</Text>
                </GlassCard>
            </ScrollView>
        </DeepSpaceBackground>
    );
}
