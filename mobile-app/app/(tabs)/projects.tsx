import { ScrollView, Text, View, TouchableOpacity, Alert } from 'react-native';
import { useEffect, useState } from 'react';
import { GlassCard } from '@/components/ui/GlassCard';
import { DeepSpaceBackground } from '@/components/ui/DeepSpaceBackground';
import { supabase } from '@/utils/supabaseClient';
import { router } from 'expo-router';

export default function ProjectsScreen() {
    const [projects, setProjects] = useState<any[]>([]);

    useEffect(() => {
        const fetchProjects = async () => {
            const { data } = await supabase.from('projects').select('*, clients(name), project_types(type_name)').order('created_at', { ascending: false });
            if (data) setProjects(data);
        };
        fetchProjects();
    }, []);

    return (
        <DeepSpaceBackground>
            <ScrollView className="flex-1 p-4">
                <Text className="text-2xl font-bold text-white mb-4 mt-8">Projects</Text>
                {projects.map(p => (
                    <GlassCard key={p.id} className="mb-3">
                        <View className="flex-row justify-between items-start">
                            <View>
                                <Text className="text-white font-bold text-lg">{p.project_types?.type_name || "Project"}</Text>
                                <Text className="text-slate-400">{p.clients?.name}</Text>
                            </View>
                            <Text className={`font-bold ${p.status === 'Closed' ? 'text-green-500' : 'text-yellow-500'}`}>{p.status}</Text>
                        </View>
                        <View className="h-[1px] bg-white/10 my-3" />
                        <View className="flex-row justify-between">
                            <Text className="text-slate-500 text-xs">Created: {new Date(p.created_at).toLocaleDateString()}</Text>
                        </View>
                    </GlassCard>
                ))}
            </ScrollView>
        </DeepSpaceBackground>
    );
}
