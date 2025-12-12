import React from 'react';
import { View, StyleSheet } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';

export function DeepSpaceBackground({ children, className }: { children?: React.ReactNode, className?: string }) {
    // CSS: background: radial-gradient(circle at 10% 20%, #0f172a 0%, #020617 90%);
    // We approximate this with a linear gradient from Top-Left to Bottom-Right.
    return (
        <LinearGradient
            colors={['#0f172a', '#020617']}
            start={{ x: 0.1, y: 0.1 }}
            end={{ x: 0.9, y: 0.9 }}
            locations={[0, 0.9]}
            style={[StyleSheet.absoluteFill, { flex: 1 }]}
        >
            <View className={className ? `flex-1 ${className}` : "flex-1"}>
                {children}
            </View>
        </LinearGradient>
    );
}
