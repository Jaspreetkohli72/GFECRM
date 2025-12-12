import { View, Text, TouchableOpacity, ScrollView } from 'react-native';
import { DeepSpaceBackground } from '@/components/ui/DeepSpaceBackground';
import { GlassCard } from '@/components/ui/GlassCard';
import { Settings, Users, IndianRupee, ChevronRight } from 'lucide-react-native';
import { router } from 'expo-router';

export default function MenuScreen() {
    const menuItems = [
        {
            title: 'Financials',
            icon: IndianRupee,
            color: '#22c55e',
            route: '/financials' as const,
            desc: 'P&L, Expenses, Revenue'
        },
        {
            title: 'Staff Management',
            icon: Users,
            color: '#3b82f6',
            route: '/staff' as const,
            desc: 'Manage Roles, Availability'
        },
        {
            title: 'Settings',
            icon: Settings,
            color: '#f97316',
            route: '/settings' as const,
            desc: 'App Defaults, Margins'
        },
    ];

    return (
        <DeepSpaceBackground>
            <View className="flex-1 p-4 pt-10">
                <Text className="text-3xl font-bold text-white mb-6">Menu</Text>

                <ScrollView>
                    {menuItems.map((item, idx) => (
                        <TouchableOpacity
                            key={idx}
                            onPress={() => router.push(item.route)}
                            activeOpacity={0.8}
                        >
                            <GlassCard className="mb-4 flex-row items-center p-4">
                                <View className="w-10 h-10 rounded-full items-center justify-center mr-4" style={{ backgroundColor: item.color + '20' }}>
                                    <item.icon size={20} color={item.color} />
                                </View>
                                <View className="flex-1">
                                    <Text className="text-white font-bold text-lg">{item.title}</Text>
                                    <Text className="text-muted text-xs">{item.desc}</Text>
                                </View>
                                <ChevronRight size={20} color="#64748b" />
                            </GlassCard>
                        </TouchableOpacity>
                    ))}
                </ScrollView>

                <Text className="text-slate-600 text-center text-xs mt-4">Version 1.0.0 • GFECRM Mobile</Text>
            </View>
        </DeepSpaceBackground>
    );
}
