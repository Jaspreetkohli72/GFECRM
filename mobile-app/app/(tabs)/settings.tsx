import { View, Text, TouchableOpacity } from 'react-native';
import { useAuth } from '@/context/AuthContext';
import { GlassCard } from '@/components/ui/GlassCard';
import { DeepSpaceBackground } from '@/components/ui/DeepSpaceBackground';

export default function SettingsScreen() {
    const { user, logout } = useAuth();

    return (
        <DeepSpaceBackground className="p-4 pt-12">
            <Text className="text-2xl font-bold text-white mb-6">Settings</Text>

            <GlassCard className="mb-4">
                <Text className="text-slate-400 text-xs uppercase mb-1">Logged in as</Text>
                <Text className="text-white font-bold text-lg">{user}</Text>
            </GlassCard>

            <TouchableOpacity
                onPress={logout}
                className="bg-red-600/20 border border-red-600/50 p-4 rounded-xl items-center"
            >
                <Text className="text-red-500 font-bold">Sign Out</Text>
            </TouchableOpacity>
        </DeepSpaceBackground>
    );
}
