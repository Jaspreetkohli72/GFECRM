import { ScrollView, Text, View, RefreshControl } from 'react-native';
import { useEffect, useState } from 'react';
import { GlassCard } from '@/components/ui/GlassCard';
import { DeepSpaceBackground } from '@/components/ui/DeepSpaceBackground';
import { supabase } from '@/utils/supabaseClient';
import { PieChart } from 'react-native-gifted-charts';

export default function DashboardScreen() {
  const [metrics, setMetrics] = useState({
    totalClients: 0,
    activeProjects: 0,
    completionRate: 0,
    totalRevenue: 0,
    matCost: 0,
    laborCost: 0
  });
  const [refreshing, setRefreshing] = useState(false);
  const [recentProjects, setRecentProjects] = useState<any[]>([]);

  const fetchDashboard = async () => {
    setRefreshing(true);
    try {
      // Clients
      const { count: clientCount } = await supabase.from('clients').select('*', { count: 'exact', head: true });

      // Projects
      const { data: projects } = await supabase.from('projects').select('*, clients(name), project_types(type_name)').order('created_at', { ascending: false });

      if (projects) {
        const total = projects.length;
        const active = projects.filter(p => !['Closed', 'Work Done'].includes(p.status)).length;
        const closed = total - active;
        const rate = total > 0 ? (closed / total) * 100 : 0;

        // Finances (Simulated from internal_estimate for now as per app.py logic roughly)
        // app.py used 'final_settlement_amount' for Revenue
        const revenue = projects.reduce((acc, p) => acc + (p.final_settlement_amount || 0), 0);

        // For logic port, we'd need to parse internal_estimate for every project to get cost split. 
        // For MVP Dashboard, we'll just show what we can easily.

        setMetrics({
          totalClients: clientCount || 0,
          activeProjects: active,
          completionRate: rate,
          totalRevenue: revenue,
          matCost: 0, // Placeholder
          laborCost: 0 // Placeholder
        });

        setRecentProjects(projects.slice(0, 5));
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

  const pieData = [
    { value: metrics.activeProjects, color: '#3b82f6', text: `${metrics.activeProjects}` },
    { value: metrics.totalClients, color: '#22c55e', text: `${metrics.totalClients}` }
  ];

  return (
    <DeepSpaceBackground>
      <ScrollView
        className="flex-1"
        contentContainerStyle={{ padding: 16, paddingBottom: 100 }}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={fetchDashboard} tintColor="#fff" />}
      >
        <Text className="text-3xl font-bold text-white mb-6 mt-10">Dashboard</Text>

        {/* Metrics Row */}
        <View className="flex-row gap-4 mb-6">
          <GlassCard className="flex-1">
            <Text className="text-slate-400 text-xs uppercase font-bold">Total Clients</Text>
            <Text className="text-2xl font-bold text-white mt-1">{metrics.totalClients}</Text>
          </GlassCard>
          <GlassCard className="flex-1">
            <Text className="text-slate-400 text-xs uppercase font-bold">Active Proj</Text>
            <Text className="text-2xl font-bold text-blue-400 mt-1">{metrics.activeProjects}</Text>
          </GlassCard>
          <GlassCard className="flex-1">
            <Text className="text-slate-400 text-xs uppercase font-bold">Completion</Text>
            <Text className="text-2xl font-bold text-green-400 mt-1">{metrics.completionRate.toFixed(0)}%</Text>
          </GlassCard>
        </View>

        {/* Chart Section */}
        <GlassCard className="mb-6 items-center">
          <Text className="text-white font-bold mb-4 self-start">Project Distribution</Text>
          <View className="flex-row items-center justify-between w-full">
            <PieChart
              data={pieData}
              donut
              radius={60}
              innerRadius={40}
              showText
              textColor="white"
            />
            <View className="flex-1 ml-8">
              <View className="flex-row items-center mb-2">
                <View className="w-3 h-3 bg-blue-500 rounded-full mr-2" />
                <Text className="text-slate-300">Active Projects</Text>
              </View>
              <View className="flex-row items-center">
                <View className="w-3 h-3 bg-green-500 rounded-full mr-2" />
                <Text className="text-slate-300">Total Clients</Text>
              </View>
            </View>
          </View>
        </GlassCard>

        {/* Recent Activity */}
        <Text className="text-xl font-bold text-white mb-4">Recent Projects</Text>
        <View className="gap-3">
          {recentProjects.map(p => (
            <GlassCard key={p.id} className="flex-row items-center justify-between">
              <View>
                <Text className="text-white font-bold">{p.project_types?.type_name || 'Unknown Project'}</Text>
                <Text className="text-slate-400 text-sm">{p.clients?.name || 'Unknown Client'}</Text>
              </View>
              <View className="items-end">
                <Text className={`font-bold ${p.status === 'Closed' ? 'text-green-500' : 'text-yellow-500'}`}>{p.status}</Text>
                <Text className="text-slate-500 text-xs">{new Date(p.created_at).toLocaleDateString()}</Text>
              </View>
            </GlassCard>
          ))}
        </View>
      </ScrollView>
    </DeepSpaceBackground>
  );
}
