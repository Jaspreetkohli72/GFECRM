import { View, Text, TouchableOpacity, ScrollView, TextInput, RefreshControl, Alert, ActivityIndicator } from 'react-native';
import { GlassCard } from '@/components/ui/GlassCard';
import { DeepSpaceBackground } from '@/components/ui/DeepSpaceBackground';
import { useState, useEffect } from 'react';
import { supabase } from '@/utils/supabaseClient';
import { Plus, Trash2 } from 'lucide-react-native';
import { Stack } from 'expo-router';

export default function StaffScreen() {
    const [roles, setRoles] = useState<any[]>([]);
    const [refreshing, setRefreshing] = useState(false);

    // New Role State
    const [newRole, setNewRole] = useState('');
    const [newSalary, setNewSalary] = useState('500');
    const [adding, setAdding] = useState(false);

    const fetchRoles = async () => {
        setRefreshing(true);
        const { data } = await supabase.from('staff_roles').select('*').order('role_name');
        if (data) setRoles(data);
        setRefreshing(false);
    };

    useEffect(() => {
        fetchRoles();
    }, []);

    const addRole = async () => {
        if (!newRole) return Alert.alert("Error", "Role Name is required");
        setAdding(true);
        const { error } = await supabase.from('staff_roles').insert({
            role_name: newRole,
            default_salary: Number(newSalary)
        });
        if (error) Alert.alert("Error", error.message);
        else {
            setNewRole('');
            setNewSalary('500');
            fetchRoles();
        }
        setAdding(false);
    };

    const deleteRole = async (roleName: string) => {
        Alert.alert("Confirm Delete", `Delete role ${roleName}?`, [
            { text: "Cancel", style: "cancel" },
            {
                text: "Delete",
                style: "destructive",
                onPress: async () => {
                    const { error } = await supabase.from('staff_roles').delete().eq('role_name', roleName);
                    if (error) Alert.alert("Error", error.message);
                    else fetchRoles();
                }
            }
        ]);
    };

    const updateSalary = async (roleName: string, newSal: string) => {
        // Optimistic update
        setRoles(roles.map(r => r.role_name === roleName ? { ...r, default_salary: newSal } : r));
        // Debounce or just fire? Fire for now.
        const { error } = await supabase.from('staff_roles').update({ default_salary: Number(newSal) }).eq('role_name', roleName);
        if (error) console.error(error);
    };

    return (
        <DeepSpaceBackground>
            <Stack.Screen options={{ title: 'Staff', headerStyle: { backgroundColor: '#0E1117' }, headerTintColor: '#fff' }} />
            <ScrollView
                className="flex-1 p-4"
                refreshControl={<RefreshControl refreshing={refreshing} onRefresh={fetchRoles} tintColor="#fff" />}
            >
                <Text className="text-3xl font-bold text-white mb-6">Staff Roles</Text>

                {/* List */}
                {roles.map((role) => (
                    <GlassCard key={role.role_name} className="mb-3">
                        <View className="flex-row justify-between items-center mb-2">
                            <Text className="text-white font-bold text-lg">{role.role_name}</Text>
                            <TouchableOpacity onPress={() => deleteRole(role.role_name)}>
                                <Trash2 size={20} color="#ef4444" />
                            </TouchableOpacity>
                        </View>
                        <View className="flex-row items-center gap-2">
                            <Text className="text-muted text-xs">Daily Salary</Text>
                            <TextInput
                                className="flex-1 bg-background text-white p-2 rounded border border-border"
                                value={String(role.default_salary)}
                                onChangeText={(v) => updateSalary(role.role_name, v)}
                                keyboardType="numeric"
                            />
                        </View>
                    </GlassCard>
                ))}

                {/* Add New */}
                <GlassCard className="mt-4 border-dashed border-slate-600 bg-transparent">
                    <Text className="text-white font-bold mb-3">Add New Role</Text>
                    <View className="gap-3">
                        <TextInput
                            className="bg-card text-white p-3 rounded-lg border border-border"
                            placeholder="Role Name (e.g. Senior Tech)"
                            placeholderTextColor="#666"
                            value={newRole}
                            onChangeText={setNewRole}
                        />
                        <View className="flex-row gap-3">
                            <TextInput
                                className="flex-1 bg-card text-white p-3 rounded-lg border border-border"
                                placeholder="Salary"
                                placeholderTextColor="#666"
                                value={newSalary}
                                onChangeText={setNewSalary}
                                keyboardType="numeric"
                            />
                            <TouchableOpacity
                                onPress={addRole}
                                className="bg-green-600 p-3 rounded-lg items-center justify-center w-14"
                                disabled={adding}
                            >
                                {adding ? <ActivityIndicator color="white" size="small" /> : <Plus size={24} color="white" />}
                            </TouchableOpacity>
                        </View>
                    </View>
                </GlassCard>

                <View className="h-20" />
            </ScrollView>
        </DeepSpaceBackground>
    );
}
