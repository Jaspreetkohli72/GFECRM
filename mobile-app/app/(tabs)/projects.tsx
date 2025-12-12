import { ScrollView, Text, View, TouchableOpacity, TextInput, RefreshControl } from 'react-native';
import { useEffect, useState } from 'react';
import { GlassCard } from '@/components/ui/GlassCard';
import { DeepSpaceBackground } from '@/components/ui/DeepSpaceBackground';
import { supabase } from '@/utils/supabaseClient';
import { Search } from 'lucide-react-native';

export default function ProjectsScreen() {
    const [clients, setClients] = useState<any[]>([]);
    const [filter, setFilter] = useState<'Active' | 'All' | 'Closed'>('Active');
    const [search, setSearch] = useState('');
    const [refreshing, setRefreshing] = useState(false);

    const fetchClients = async () => {
        setRefreshing(true);
        const { data } = await supabase.from('clients').select('*').order('created_at', { ascending: false });
        if (data) setClients(data);
        setRefreshing(false);
    };

    useEffect(() => {
        fetchClients();
    }, []);

    const filteredClients = clients.filter(c => {
        const matchesSearch = c.name?.toLowerCase().includes(search.toLowerCase());
        const isClosed = ['Closed', 'Work Done'].includes(c.status);

        if (!matchesSearch) return false;

        if (filter === 'Active') return !isClosed;
        if (filter === 'Closed') return isClosed;
        return true;
    });

    return (
        <DeepSpaceBackground>
            <View className="flex-1 p-4 pt-10">
                <Text className="text-3xl font-bold text-white mb-4">Clients</Text>

                {/* Search & Filter */}
                <View className="flex-row gap-2 mb-4">
                    <View className="flex-1 bg-card border border-border rounded-lg flex-row items-center px-3">
                        <Search size={20} color="#94a3b8" />
                        <TextInput
                            className="flex-1 text-white p-3"
                            placeholder="Search Clients..."
                            placeholderTextColor="#94a3b8"
                            value={search}
                            onChangeText={setSearch}
                        />
                    </View>
                </View>

                {/* Segemented Control */}
                <View className="flex-row bg-slate-900 p-1 rounded-lg mb-4 border border-border">
                    {['Active', 'All', 'Closed'].map((f) => (
                        <TouchableOpacity
                            key={f}
                            className={`flex-1 py-2 rounded-md items-center ${filter === f ? 'bg-blue-600' : ''}`}
                            onPress={() => setFilter(f as any)}
                        >
                            <Text className={`font-bold ${filter === f ? 'text-white' : 'text-slate-400'}`}>{f}</Text>
                        </TouchableOpacity>
                    ))}
                </View>

                <ScrollView
                    className="flex-1"
                    refreshControl={<RefreshControl refreshing={refreshing} onRefresh={fetchClients} tintColor="#fff" />}
                >
                    {filteredClients.map(c => (
                        <GlassCard key={c.id} className="mb-3">
                            <View className="flex-row justify-between items-start">
                                <View>
                                    <Text className="text-white font-bold text-lg">{c.name}</Text>
                                    <Text className="text-muted text-xs">{c.phone || "No Phone"}</Text>
                                </View>
                                <View className={`px-2 py-1 rounded bg-slate-800`}>
                                    <Text className={`font-bold text-xs ${['Closed', 'Work Done'].includes(c.status) ? 'text-green-500' : 'text-yellow-500'}`}>
                                        {c.status || 'Active'}
                                    </Text>
                                </View>
                            </View>
                            <View className="h-[1px] bg-white/10 my-3" />
                            <View className="flex-row justify-between">
                                <Text className="text-slate-500 text-xs">Revenue: ₹{(c.final_settlement_amount || 0).toLocaleString()}</Text>
                                <Text className="text-slate-500 text-xs">{new Date(c.created_at).toLocaleDateString()}</Text>
                            </View>
                        </GlassCard>
                    ))}
                    {filteredClients.length === 0 && (
                        <Text className="text-slate-500 text-center mt-10">No clients found</Text>
                    )}
                </ScrollView>
            </View>
        </DeepSpaceBackground>
    );
}
