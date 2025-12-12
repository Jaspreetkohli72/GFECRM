import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, ImageBackground, ActivityIndicator, Alert, Platform } from 'react-native';
import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'expo-router';
import { DeepSpaceBackground } from '@/components/ui/DeepSpaceBackground';

export default function LoginScreen() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const { login } = useAuth();
    const router = useRouter();

    const handleLogin = async () => {
        console.log("Attempting login...");
        try {
            if (!username || !password) {
                Alert.alert('Error', 'Please enter username and password');
                return;
            }

            setLoading(true);
            await new Promise(r => setTimeout(r, 100)); // Small yield

            const success = await login(username, password);
            console.log("Login success:", success);

            if (success) {
                router.replace('/(tabs)');
            } else {
                setLoading(false);
                Alert.alert('Error', 'Invalid credentials');
            }
        } catch (e: any) {
            setLoading(false);
            console.error("Login Error:", e);
            Alert.alert('Error', e.message || "An unexpected error occurred");
        }
    };

    return (
        <DeepSpaceBackground className="justify-center items-center p-4">
            {/* Glass Card */}
            <View className="w-full max-w-md bg-slate-900/60 border border-white/10 rounded-2xl p-8 backdrop-blur-xl">
                <Text className="text-3xl font-bold text-white text-center mb-2">Galaxy CRM</Text>
                <Text className="text-slate-400 text-center mb-8">Sign in to continue</Text>

                <View className="space-y-4 gap-4">
                    <View>
                        <Text className="text-slate-300 mb-2 font-medium">Username</Text>
                        <TextInput
                            className="w-full bg-slate-950/50 border border-slate-700 rounded-lg p-4 text-white placeholder:text-slate-600 focus:border-blue-500"
                            placeholder="Enter username"
                            placeholderTextColor="#475569"
                            value={username}
                            onChangeText={setUsername}
                            autoCapitalize="none"
                        />
                    </View>

                    <View>
                        <Text className="text-slate-300 mb-2 font-medium">Password</Text>
                        <TextInput
                            className="w-full bg-slate-950/50 border border-slate-700 rounded-lg p-4 text-white placeholder:text-slate-600 focus:border-blue-500"
                            placeholder="Enter password"
                            placeholderTextColor="#475569"
                            value={password}
                            onChangeText={setPassword}
                            secureTextEntry
                        />
                    </View>

                    <TouchableOpacity
                        className="w-full bg-blue-600 p-4 rounded-xl mt-4 active:bg-blue-700 items-center justify-center"
                        onPress={handleLogin}
                        disabled={loading}
                    >
                        {loading ? (
                            <ActivityIndicator color="white" />
                        ) : (
                            <Text className="text-white font-bold text-lg">Sign In</Text>
                        )}
                    </TouchableOpacity>
                </View>
            </View>
        </DeepSpaceBackground>
    );
}
