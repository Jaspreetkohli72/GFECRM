import { ScrollView, Text, View, TextInput, TouchableOpacity, Alert, ActivityIndicator } from 'react-native';
import { useEffect, useState } from 'react';
import { GlassCard } from '@/components/ui/GlassCard';
import { supabase } from '@/utils/supabaseClient';
import { Picker } from '@react-native-picker/picker';
import { InventoryItem, EstimateItem, CalculationResult, LaborRole } from '@/types';
import { calculate_estimate_details } from '@/utils/calculations';
import * as Print from 'expo-print';
import { shareAsync } from 'expo-sharing';
import { generateInvoiceHTML } from '@/utils/pdfGenerator';
import { DeepSpaceBackground } from '@/components/ui/DeepSpaceBackground';
import { Plus, Trash2 } from 'lucide-react-native';

export default function EstimatorScreen() {
    const [loading, setLoading] = useState(false);
    const [clients, setClients] = useState<any[]>([]);
    const [projects, setProjects] = useState<any[]>([]);
    const [inventory, setInventory] = useState<InventoryItem[]>([]);
    const [settings, setSettings] = useState<any>({});

    // Dynamic Staff Roles
    const [staffRoles, setStaffRoles] = useState<any[]>([]);
    const [laborCounts, setLaborCounts] = useState<Record<string, string>>({});

    // Selections
    const [selectedClientId, setSelectedClientId] = useState<number | null>(null);
    const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);

    // Inventory Selection
    const [invType, setInvType] = useState<string>('');
    const [invDim, setInvDim] = useState<string>('');
    const [invTypes, setInvTypes] = useState<string[]>([]);
    const [invDims, setInvDims] = useState<string[]>([]);
    const [qty, setQty] = useState('1');

    // Estimate Data
    const [items, setItems] = useState<EstimateItem[]>([]);
    const [laborDays, setLaborDays] = useState('1');

    const [result, setResult] = useState<CalculationResult | null>(null);

    // Initial Load
    useEffect(() => {
        loadInitialData();
    }, []);

    const loadInitialData = async () => {
        setLoading(true);
        try {
            const [cRes, iRes, sRes, rRes] = await Promise.all([
                supabase.from('clients').select('id, name').neq('status', 'Closed'),
                supabase.from('inventory').select('*').order('item_name'),
                supabase.from('settings').select('*').eq('id', 1).single(),
                supabase.from('staff_roles').select('*')
            ]);

            if (cRes.data) setClients(cRes.data);
            if (iRes.data) {
                setInventory(iRes.data);
                const types = Array.from(new Set(iRes.data.map((i: any) => i.item_type).filter(Boolean))) as string[];
                setInvTypes(types);
            }
            if (sRes.data) setSettings(sRes.data);
            if (rRes.data) {
                setStaffRoles(rRes.data);
                // Initialize labor counts
                const initialCounts: Record<string, string> = {};
                rRes.data.forEach((r: any) => initialCounts[r.role_name] = '0');
                setLaborCounts(initialCounts);
            }
        } catch (e) { console.error(e); }
        setLoading(false);
    };

    // Load Projects when Client changes
    useEffect(() => {
        if (selectedClientId) {
            supabase.from('projects')
                .select('*, project_types(type_name)')
                .eq('client_id', selectedClientId)
                .then(({ data }) => setProjects(data || []));
        } else {
            setProjects([]);
            setSelectedProjectId(null);
        }
    }, [selectedClientId]);

    // Load Estimate when Project changes
    useEffect(() => {
        if (selectedProjectId && projects.length) {
            const p = projects.find(proj => proj.id === selectedProjectId);
            if (p && p.internal_estimate) {
                const est = p.internal_estimate;
                if (est.items) setItems(est.items);
                if (est.days) setLaborDays(String(est.days));

                // Load saved labor counts
                // The saved data might be in 'labor_details' array or legacy fields?
                // Our new logic saves 'labor_details'.
                if (est.labor_details && Array.isArray(est.labor_details)) {
                    const loadedCounts: Record<string, string> = {};
                    // Reset first
                    staffRoles.forEach(r => loadedCounts[r.role_name] = '0');
                    // Fill from saved
                    est.labor_details.forEach((d: any) => {
                        loadedCounts[d.role] = String(d.count);
                    });
                    setLaborCounts(loadedCounts);
                } else {
                    // Legacy fallback or empty
                    const initialCounts: Record<string, string> = {};
                    staffRoles.forEach(r => initialCounts[r.role_name] = '0');
                    setLaborCounts(initialCounts);
                }

            } else {
                setItems([]);
                setLaborDays('1');
                const initialCounts: Record<string, string> = {};
                staffRoles.forEach(r => initialCounts[r.role_name] = '0');
                setLaborCounts(initialCounts);
            }
        }
    }, [selectedProjectId, staffRoles]);

    // Recalculate
    useEffect(() => {
        if (settings && staffRoles.length > 0) {
            // Build labor_details
            const labor_details: LaborRole[] = staffRoles.map(role => ({
                role: role.role_name,
                count: Number(laborCounts[role.role_name] || 0),
                rate: Number(role.default_salary || 0)
            })).filter(r => r.count > 0);

            const res = calculate_estimate_details(
                items,
                Number(laborDays) || 1,
                settings.profit_margin,
                settings,
                labor_details
            );
            setResult(res);
        }
    }, [items, laborDays, laborCounts, settings, staffRoles]);

    // Dynamic Inventory Filtering
    useEffect(() => {
        if (invType && inventory.length) {
            const dims = Array.from(new Set(inventory.filter((i: any) => i.item_type === invType).map((i: any) => i.dimension).filter(Boolean))) as string[];
            setInvDims(dims);
        }
    }, [invType, inventory]);

    const addItem = () => {
        const match = inventory.find((i: any) => i.item_type === invType && i.dimension === invDim);
        if (match) {
            const newItem: EstimateItem = {
                Item: match.item_name,
                Qty: Number(qty),
                Unit: match.unit,
                "Base Rate": match.base_rate
            };
            setItems([...items, newItem]);
        } else {
            Alert.alert("Item not found", "Please select valid Type and Dimension");
        }
    };

    const removeItem = (idx: number) => {
        const n = [...items];
        n.splice(idx, 1);
        setItems(n);
    };

    const handleSave = async () => {
        if (!selectedProjectId) return;
        setLoading(true);

        const labor_details: LaborRole[] = staffRoles.map(role => ({
            role: role.role_name,
            count: Number(laborCounts[role.role_name] || 0),
            rate: Number(role.default_salary || 0)
        })).filter(r => r.count > 0);

        const estimateData = {
            items,
            days: Number(laborDays),
            labor_details,
            profit_margin: settings.profit_margin
        };

        const { error } = await supabase.from('projects').update({
            internal_estimate: estimateData,
            status: `Estimate Updated ${new Date().toLocaleDateString()}`
        }).eq('id', selectedProjectId);

        setLoading(false);
        if (error) Alert.alert("Error", error.message);
        else Alert.alert("Success", "Estimate saved!");
    };

    const handlePDF = async () => {
        if (!result || !selectedClientId) return;
        const client = clients.find(c => c.id === selectedClientId);
        const html = generateInvoiceHTML(client?.name || "Client", result, false);
        const { uri } = await Print.printToFileAsync({ html });
        await shareAsync(uri, { UTI: '.pdf', mimeType: 'application/pdf' });
    };

    const updateLaborCount = (role: string, val: string) => {
        setLaborCounts(prev => ({
            ...prev,
            [role]: val
        }));
    };

    return (
        <DeepSpaceBackground>
            <ScrollView className="flex-1 p-4" contentContainerStyle={{ paddingBottom: 100 }}>
                <Text className="text-2xl font-bold text-white mb-4 mt-8">Estimator</Text>

                {/* Client/Project Select */}
                <GlassCard className="mb-4">
                    <Text className="text-muted text-xs uppercase mb-1">Select Client</Text>
                    <View className="bg-card border border-border rounded-lg mb-3">
                        <Picker
                            selectedValue={selectedClientId}
                            onValueChange={(v) => setSelectedClientId(v)}
                            style={{ color: 'white' }}
                            dropdownIconColor="white"
                        >
                            <Picker.Item label="Select Client..." value={null} />
                            {clients.map(c => <Picker.Item key={c.id} label={c.name} value={c.id} />)}
                        </Picker>
                    </View>

                    <Text className="text-muted text-xs uppercase mb-1">Select Project</Text>
                    <View className="bg-card border border-border rounded-lg">
                        <Picker
                            selectedValue={selectedProjectId}
                            onValueChange={(v) => setSelectedProjectId(v)}
                            style={{ color: 'white' }}
                            dropdownIconColor="white"
                        >
                            <Picker.Item label="Select Project..." value={null} />
                            {projects.map(p => <Picker.Item key={p.id} label={`${p.project_types?.type_name} - ${p.status}`} value={p.id} />)}
                        </Picker>
                    </View>
                </GlassCard>

                {selectedProjectId && (
                    <>
                        {/* Inventory Adder */}
                        <GlassCard className="mb-4">
                            <Text className="text-white font-bold mb-2">Add Item</Text>
                            <View className="flex-row gap-2 mb-2">
                                <View className="flex-1 bg-card border border-border rounded-lg">
                                    <Picker selectedValue={invType} onValueChange={setInvType} style={{ color: 'white' }}>
                                        <Picker.Item label="Type..." value="" />
                                        {invTypes.map(t => <Picker.Item key={t} label={t} value={t} />)}
                                    </Picker>
                                </View>
                                <View className="flex-1 bg-card border border-border rounded-lg">
                                    <Picker selectedValue={invDim} onValueChange={setInvDim} style={{ color: 'white' }}>
                                        <Picker.Item label="Dim..." value="" />
                                        {invDims.map(d => <Picker.Item key={d} label={d} value={d} />)}
                                    </Picker>
                                </View>
                            </View>
                            <View className="flex-row gap-2 items-center">
                                <TextInput
                                    className="flex-1 bg-card text-white p-3 rounded-lg border border-border"
                                    placeholder="Qty"
                                    placeholderTextColor="#666"
                                    keyboardType="numeric"
                                    value={qty}
                                    onChangeText={setQty}
                                />
                                <TouchableOpacity onPress={addItem} className="bg-blue-600 p-3 rounded-lg">
                                    <Plus size={24} color="white" />
                                </TouchableOpacity>
                            </View>
                        </GlassCard>

                        {/* Items List */}
                        <View className="mb-4">
                            {items.map((item, idx) => (
                                <GlassCard key={idx} className="mb-2 p-3 flex-row justify-between items-center">
                                    <View className="flex-1">
                                        <Text className="text-white font-bold">{item.Item}</Text>
                                        <Text className="text-muted text-xs">{item.Qty} {item.Unit} x ₹{item['Base Rate']}</Text>
                                    </View>
                                    <View className="items-end mr-3">
                                        <Text className="text-blue-400 font-bold">₹{((item.Qty * item['Base Rate'])).toFixed(0)}</Text>
                                    </View>
                                    <TouchableOpacity onPress={() => removeItem(idx)}>
                                        <Trash2 size={20} color="#ef4444" />
                                    </TouchableOpacity>
                                </GlassCard>
                            ))}
                        </View>

                        {/* Labor Config */}
                        <GlassCard className="mb-4">
                            <Text className="text-white font-bold mb-2">Labor Details</Text>
                            <View className="mb-3">
                                <Text className="text-muted text-xs">Total Days</Text>
                                <TextInput
                                    className="bg-card text-white p-2 rounded border border-border mt-1"
                                    value={laborDays}
                                    onChangeText={setLaborDays}
                                    keyboardType="numeric"
                                />
                            </View>

                            <View className="flex-row flex-wrap gap-2">
                                {staffRoles.map(role => (
                                    <View key={role.role_name} className="w-[48%] mb-2">
                                        <Text className="text-muted text-xs">{role.role_name} (₹{role.default_salary})</Text>
                                        <TextInput
                                            className="bg-card text-white p-2 rounded border border-border mt-1"
                                            value={laborCounts[role.role_name] || '0'}
                                            onChangeText={(val) => updateLaborCount(role.role_name, val)}
                                            keyboardType="numeric"
                                        />
                                    </View>
                                ))}
                            </View>
                        </GlassCard>

                        {/* Metrics */}
                        {result && (
                            <GlassCard className="mb-6 bg-blue-900/20">
                                <View className="flex-row justify-between mb-2">
                                    <Text className="text-slate-300">Material Cost</Text>
                                    <Text className="text-white font-bold">₹{result.total_material_base_cost.toFixed(0)}</Text>
                                </View>
                                <View className="flex-row justify-between mb-2">
                                    <Text className="text-slate-300">Labor Cost</Text>
                                    <Text className="text-white font-bold">₹{result.labor_actual_cost.toFixed(0)}</Text>
                                </View>
                                <View className="h-[1px] bg-white/10 my-2" />
                                <View className="flex-row justify-between mb-1">
                                    <Text className="text-xl text-white font-bold">Bill Amount</Text>
                                    <Text className="text-xl text-green-400 font-bold">₹{result.bill_amount.toLocaleString('en-IN')}</Text>
                                </View>
                                <View className="flex-row justify-between">
                                    <Text className="text-muted">Profit</Text>
                                    <Text className="text-green-600">₹{result.total_profit.toFixed(0)}</Text>
                                </View>
                            </GlassCard>
                        )}

                        {/* Actions */}
                        <View className="flex-row gap-4 mb-10">
                            <TouchableOpacity onPress={handleSave} className="flex-1 bg-green-600 p-4 rounded-xl items-center" disabled={loading}>
                                {loading ? <ActivityIndicator color="white" /> : <Text className="text-white font-bold">Save Estimate</Text>}
                            </TouchableOpacity>
                            <TouchableOpacity onPress={handlePDF} className="flex-1 bg-orange-600 p-4 rounded-xl items-center">
                                <Text className="text-white font-bold">Share PDF</Text>
                            </TouchableOpacity>
                        </View>
                    </>
                )}
            </ScrollView>
        </DeepSpaceBackground>
    );
}
