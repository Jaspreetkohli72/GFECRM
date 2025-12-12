import { View, ViewProps, StyleSheet } from 'react-native';
import { cn } from '@/utils/cn';

interface GlassCardProps extends ViewProps {
    className?: string;
    intensity?: number;
}

export function GlassCard({ children, className, style, ...props }: GlassCardProps) {
    // CSS: 
    // background: rgba(30, 41, 59, 0.4); -> #1e293b (slate-800) @ 0.4
    // backdrop-filter: blur(12px); -> web only, native needs BlurView (omitted for now to avoid complexity, using opacity)
    // border: 1px solid rgba(255, 255, 255, 0.1); -> border-white/10
    // border-radius: 16px; -> rounded-2xl
    // padding: 20px; -> p-5
    // box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.2); -> shadow-lg

    return (
        <View
            className={cn(
                "bg-slate-800/40 border border-white/10 rounded-2xl p-5 shadow-lg",
                className
            )}
            style={[{
                // Web-specific backdrop blur if running on web
                // @ts-ignore
                backdropFilter: 'blur(12px)',
            }, style]}
            {...props}
        >
            {children}
        </View>
    );
}
