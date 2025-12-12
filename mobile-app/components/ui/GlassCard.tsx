import { View, ViewProps, StyleSheet } from 'react-native';
import { cn } from '@/utils/cn';

interface GlassCardProps extends ViewProps {
    className?: string;
    intensity?: number;
}

export function GlassCard({ children, className, style, ...props }: GlassCardProps) {
    return (
        <View
            className={cn(
                "bg-card border border-border rounded-lg p-4",
                className
            )}
            style={style}
            {...props}
        >
            {children}
        </View>
    );
}
