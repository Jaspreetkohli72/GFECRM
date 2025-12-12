import { View, Text, TouchableOpacity, ScrollView, TextInput, Alert, ActivityIndicator } from 'react-native';
import { useAuth } from '@/context/AuthContext';
import { GlassCard } from '@/components/ui/GlassCard';
import { DeepSpaceBackground } from '@/components/ui/DeepSpaceBackground';
import { useState, useEffect } from 'react';
import { supabase } from '@/utils/supabaseClient';

export default function SettingsScreen() {
    const { user, logout } = useAuth();
    const [settings, setSettings] = useState<any>({});
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        fetchSettings();
    }, []);

    const fetchSettings = async () => {
        setLoading(true);
        const { data } = await supabase.from('settings').select('*').eq('id', 1).single();
        if (data) setSettings(data);
        setLoading(false);
    };

    const handleSave = async () => {
        setSaving(true);
        const { error } = await supabase.from('settings').update({
            profit_margin: Number(settings.profit_margin),
            advance_percentage: Number(settings.advance_percentage)
        }).eq('id', 1);
        setSaving(false);
        if (error) Alert.alert("Error", error.message);
        else Alert.alert("Success", "Settings saved");
    };

    const updateSetting = (key: string, val: string) => {
        setSettings({ ...settings, [key]: val });
    };

    return (
        <DeepSpaceBackground>
            <ScrollView className="flex-1 p-4 pt-10">
                <Text className="text-3xl font-bold text-white mb-6">Settings</Text>

                <GlassCard className="mb-6">
                    <Text className="text-muted text-xs uppercase mb-1">Account</Text>
                    <Text className="text-white font-bold text-lg">{user}</Text>
                    <TouchableOpacity
                        onPress={logout}
                        className="mt-4 bg-red-600/20 border border-red-600/50 p-3 rounded-lg items-center"
                    >
                        <Text className="text-red-500 font-bold">Sign Out</Text>
                    </TouchableOpacity>
                </GlassCard>

                <GlassCard className="mb-6">
                    <Text className="text-white font-bold mb-4">Global Defaults</Text>

                    <View className="mb-3">
                        <Text className="text-muted text-xs">Default Profit Margin (%)</Text>
                        <TextInput
                            className="bg-background text-white p-3 rounded-lg border border-border mt-1"
                            value={String(settings.profit_margin || '')}
                            onChangeText={(v) => updateSetting('profit_margin', v)}
                            keyboardType="numeric"
                        />
                    </View>

                    <View className="mb-3">
                        <Text className="text-muted text-xs">Advance Percentage (%)</Text>
                        <TextInput
                            className="bg-background text-white p-3 rounded-lg border border-border mt-1"
                            value={String(settings.advance_percentage || '')}
                            onChangeText={(v) => updateSetting('advance_percentage', v)}
                            keyboardType="numeric"
                        />
                    </View>

                    <TouchableOpacity
                        onPress={handleSave}
                        className="bg-blue-600 p-4 rounded-xl items-center mt-2"
                        disabled={saving}
                    >
                        {saving ? <ActivityIndicator color="white" /> : <Text className="text-white font-bold">Save Changes</Text>}
                    </TouchableOpacity>
                </GlassCard>
            </ScrollView>
        </DeepSpaceBackground>
    );
}
