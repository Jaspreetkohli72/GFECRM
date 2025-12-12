import { ScrollView, Text, View, TouchableOpacity, TextInput, RefreshControl } from 'react-native';
import { useEffect, useState } from 'react';
import { GlassCard } from '@/components/ui/GlassCard';
import { DeepSpaceBackground } from '@/components/ui/DeepSpaceBackground';
import { supabase } from '@/utils/supabaseClient';
import { Search } from 'lucide-react-native';

export default function InventoryScreen() {
    const [activeTab, setActiveTab] = useState<'Items' | 'Suppliers'>('Items');
    const [items, setItems] = useState<any[]>([]);
    const [suppliers, setSuppliers] = useState<any[]>([]);
    const [search, setSearch] = useState('');
    const [refreshing, setRefreshing] = useState(false);

    const fetchData = async () => {
        setRefreshing(true);
        const [iRes, sRes] = await Promise.all([
            supabase.from('inventory').select('*').order('item_name'),
            supabase.from('suppliers').select('*').order('supplier_name')
        ]);
        if (iRes.data) setItems(iRes.data);
        if (sRes.data) setSuppliers(sRes.data);
        setRefreshing(false);
    };

    useEffect(() => {
        fetchData();
    }, []);

    const filteredData = activeTab === 'Items'
        ? items.filter(i => i.item_name?.toLowerCase().includes(search.toLowerCase()))
        : suppliers.filter(s => s.supplier_name?.toLowerCase().includes(search.toLowerCase()));

    return (
        <DeepSpaceBackground>
            <View className="flex-1 p-4 pt-10">
                <Text className="text-3xl font-bold text-white mb-4">Inventory</Text>

                {/* Search */}
                <View className="flex-row bg-card border border-border rounded-lg mb-4 items-center px-3">
                    <Search size={20} color="#94a3b8" />
                    <TextInput
                        className="flex-1 text-white p-3"
                        placeholder={`Search ${activeTab}...`}
                        placeholderTextColor="#94a3b8"
                        value={search}
                        onChangeText={setSearch}
                    />
                </View>

                {/* Tabs */}
                <View className="flex-row mb-4 border-b border-white/10">
                    <TouchableOpacity
                        className={`mr-6 pb-2 ${activeTab === 'Items' ? 'border-b-2 border-blue-500' : ''}`}
                        onPress={() => setActiveTab('Items')}
                    >
                        <Text className={`font-bold text-lg ${activeTab === 'Items' ? 'text-white' : 'text-slate-400'}`}>Items</Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                        className={`mr-6 pb-2 ${activeTab === 'Suppliers' ? 'border-b-2 border-blue-500' : ''}`}
                        onPress={() => setActiveTab('Suppliers')}
                    >
                        <Text className={`font-bold text-lg ${activeTab === 'Suppliers' ? 'text-white' : 'text-slate-400'}`}>Suppliers</Text>
                    </TouchableOpacity>
                </View>

                <ScrollView
                    className="flex-1"
                    refreshControl={<RefreshControl refreshing={refreshing} onRefresh={fetchData} tintColor="#fff" />}
                >
                    {activeTab === 'Items' ? (
                        filteredData.map((item, idx) => (
                            <GlassCard key={item.id || idx} className="mb-3 flex-row justify-between items-center">
                                <View>
                                    <Text className="text-white font-bold">{item.item_name}</Text>
                                    <Text className="text-muted text-xs">{item.dimension} • {item.item_type}</Text>
                                </View>
                                <View className="items-end">
                                    <Text className="text-blue-400 font-bold">₹{item.base_rate}</Text>
                                    <Text className="text-slate-500 text-xs text-right">per {item.unit}</Text>
                                </View>
                            </GlassCard>
                        ))
                    ) : (
                        filteredData.map((sup, idx) => (
                            <GlassCard key={sup.id || idx} className="mb-3">
                                <Text className="text-white font-bold text-lg">{sup.supplier_name}</Text>
                                <Text className="text-muted text-sm">{sup.contact_person} • {sup.phone}</Text>
                                {sup.gstin && <Text className="text-slate-500 text-xs mt-1">GSTIN: {sup.gstin}</Text>}
                            </GlassCard>
                        ))
                    )}
                    {filteredData.length === 0 && (
                        <Text className="text-slate-500 text-center mt-10">No results found</Text>
                    )}
                </ScrollView>
            </View>
        </DeepSpaceBackground>
    );
}
