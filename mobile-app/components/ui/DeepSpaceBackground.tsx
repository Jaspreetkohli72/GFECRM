import React from 'react';
import { View, StyleSheet } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';

export function DeepSpaceBackground({ children, className }: { children?: React.ReactNode, className?: string }) {
    return (
        <View className={`flex-1 bg-background ${className || ''}`}>
            {children}
        </View>
    );
}
