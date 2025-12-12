import React, { createContext, useContext, useEffect, useState } from 'react';
import { supabase } from '../utils/supabaseClient';
import AsyncStorage from '@react-native-async-storage/async-storage';

type AuthContextType = {
    user: string | null;
    loading: boolean;
    login: (username: string, password: string) => Promise<boolean>;
    logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextType>({ user: null, loading: true, login: async () => false, logout: async () => { } });

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
    const [user, setUser] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        checkSession();
    }, []);

    const checkSession = async () => {
        try {
            const storedUser = await AsyncStorage.getItem('galaxy_user');
            if (storedUser) {
                setUser(storedUser);
            }
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    const login = async (username: string, password: string): Promise<boolean> => {
        console.log("AuthContext: login called for", username);
        try {
            // Replicates check_login from app.py
            const { data, error } = await supabase
                .from('users')
                .select('username, password')
                .eq('username', username)
                .single();

            if (error) {
                console.error("AuthContext: Supabase Error", error);
                return false;
            }
            if (!data) {
                console.error("AuthContext: User not found");
                return false;
            }

            console.log("AuthContext: User found, checking password...");
            if (data.password === password) { // Plain text comparison as per app.py
                await AsyncStorage.setItem('galaxy_user', username);
                setUser(username);
                console.log("AuthContext: Login successful");
                return true;
            } else {
                console.error("AuthContext: Password mismatch");
            }
            return false;
        } catch (e) {
            console.error("AuthContext: Exception", e);
            return false;
        }
    };

    const logout = async () => {
        await AsyncStorage.removeItem('galaxy_user');
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, loading, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
};
