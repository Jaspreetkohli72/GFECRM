import { ScrollView, Text, View, RefreshControl, TouchableOpacity } from 'react-native';
import { useEffect, useState } from 'react';
import { GlassCard } from '@/components/ui/GlassCard';
import { DeepSpaceBackground } from '@/components/ui/DeepSpaceBackground';
import { supabase } from '@/utils/supabaseClient';
import { FontAwesome } from '@expo/vector-icons';

export default function DashboardScreen() {
  const [metrics, setMetrics] = useState({
    totalClients: 0,
    activeProjects: 0,
    completionRate: 0
  });
  const [recentProjects, setRecentProjects] = useState<any[]>([]);
  const [topClients, setTopClients] = useState<any[]>([]);
  const [refreshing, setRefreshing] = useState(false);

  const fetchDashboard = async () => {
    setRefreshing(true);
    try {
      // 1. Clients & Top Clients
      // Fetch all clients to calculate stats and top 5
      const { data: clients, error: clientError } = await supabase
        .from('clients')
        .select('name, status, final_settlement_amount')
        .order('final_settlement_amount', { ascending: false }); // Top value first

      if (clients) {
        const total = clients.length;
        // Active definition: Not Closed, Not Work Done
        const activeCount = clients.filter(c => !['Closed', 'Work Done'].includes(c.status || '')).length;
        const closedCount = total - activeCount;
        const rate = total > 0 ? (closedCount / total) * 100 : 0;

        setMetrics({
          totalClients: total,
          activeProjects: activeCount,
          completionRate: rate
        });

        // Top 5 Clients by Value
        setTopClients(clients.slice(0, 5));
      }

      // 2. Recent Activity (Projects created recently)
      // Actually app.py "Recent Activity" is client updates? 
      // "Feed of the 5 most recent client updates." (Usually created_at or updated_at)
      // We will fetch 5 most recently updated clients.
      const { data: recent } = await supabase
        .from('clients')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(5);

      if (recent) {
        setRecentProjects(recent);
      }

    } catch (e) {
      console.error(e);
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  return (
    <DeepSpaceBackground>
      <ScrollView
        className="flex-1"
        contentContainerStyle={{ padding: 16, paddingBottom: 100 }}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={fetchDashboard} tintColor="#fff" />}
      >
        <Text className="text-3xl font-bold text-white mb-6 mt-10">Dashboard</Text>

        {/* Summary Metrics */}
        <View className="flex-row gap-3 mb-6">
          <GlassCard className="flex-1 items-center">
            <Text className="text-muted text-xs uppercase font-bold text-center">Total Clients</Text>
            <Text className="text-2xl font-bold text-white mt-1">{metrics.totalClients}</Text>
          </GlassCard>
          <GlassCard className="flex-1 items-center">
            <Text className="text-muted text-xs uppercase font-bold text-center">Active</Text>
            <Text className="text-2xl font-bold text-blue-400 mt-1">{metrics.activeProjects}</Text>
          </GlassCard>
          <GlassCard className="flex-1 items-center">
            <Text className="text-muted text-xs uppercase font-bold text-center">Completion</Text>
            <Text className="text-2xl font-bold text-green-400 mt-1">{metrics.completionRate.toFixed(0)}%</Text>
          </GlassCard>
        </View>

        {/* Top Clients */}
        <Text className="text-xl font-bold text-white mb-4">Top Clients</Text>
        <GlassCard className="mb-6 p-0 overflow-hidden">
          {topClients.map((client, index) => (
            <View key={index} className={`flex-row justify-between items-center p-4 ${index !== topClients.length - 1 ? 'border-b border-border' : ''}`}>
              <View className="flex-row items-center gap-3">
                <View className="w-8 h-8 rounded-full bg-slate-700 items-center justify-center">
                  <Text className="text-white font-bold">{index + 1}</Text>
                </View>
                <Text className="text-white font-semibold">{client.name}</Text>
              </View>
              <Text className="text-green-400 font-bold">₹{(client.final_settlement_amount || 0).toLocaleString()}</Text>
            </View>
          ))}
          {topClients.length === 0 && <Text className="text-muted p-4 text-center">No data available</Text>}
        </GlassCard>

        {/* Recent Activity */}
        <Text className="text-xl font-bold text-white mb-4">Recent Activity</Text>
        <View className="gap-3">
          {recentProjects.map(p => (
            <GlassCard key={p.id} className="flex-row items-center justify-between">
              <View>
                <Text className="text-white font-bold">{p.name}</Text>
                <Text className="text-muted text-xs">{p.phone || 'No Phone'}</Text>
              </View>
              <View className="items-end">
                <View className={`px-2 py-1 rounded bg-slate-800`}>
                  <Text className="text-sky-400 text-xs font-bold">{p.status || 'New'}</Text>
                </View>
              </View>
            </GlassCard>
          ))}
        </View>

      </ScrollView>
    </DeepSpaceBackground>
  );
}
