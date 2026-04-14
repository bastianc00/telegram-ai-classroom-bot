import { createContext, useContext, useState, useEffect } from 'react';
import {
  onAuthStateChange,
  signInWithGoogle as firebaseSignInWithGoogle,
  signInWithEmail as firebaseSignInWithEmail,
  registerWithEmail as firebaseRegisterWithEmail,
  signOut as firebaseSignOut
} from '@/lib/firebase';
import { authAPI } from '@/services/api';

const AuthContext = createContext({
  isAuthenticated: false,
  loading: true,
  user: null,
  signIn: async () => {},
  signInWithEmail: async (email, password) => {},
  registerWithEmail: async (email, password) => {},
  signOut: async () => {},
});

export const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState(null);

  useEffect(() => {
    // Listen to Firebase auth state changes
    const unsubscribe = onAuthStateChange(async (firebaseUser) => {
      if (firebaseUser) {
        try {
          console.log('Firebase user detected:', firebaseUser.email);
          // Get user profile from backend
          const profile = await authAPI.getProfile();
          console.log('Backend profile received:', profile);
          setUser(profile);
          setIsAuthenticated(true);
        } catch (error) {
          console.error('Error fetching user profile:', error);
          console.error('Error details:', error.message);
          // Si Firebase tiene el usuario pero backend falla, aún autenticamos
          // El backend creará el usuario en la próxima solicitud
          setUser({
            email: firebaseUser.email,
            display_name: firebaseUser.displayName,
            firebase_uid: firebaseUser.uid
          });
          setIsAuthenticated(true);
        }
      } else {
        setUser(null);
        setIsAuthenticated(false);
      }
      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  const signIn = async () => {
    try {
      setLoading(true);
      await firebaseSignInWithGoogle();
      // onAuthStateChange will handle the rest
    } catch (error) {
      console.error('Error signing in:', error);
      setLoading(false);
      throw error;
    }
  };

  const signInWithEmail = async (email, password) => {
    try {
      setLoading(true);
      await firebaseSignInWithEmail(email, password);
      // onAuthStateChange will handle the rest
    } catch (error) {
      console.error('Error signing in with email:', error);
      setLoading(false);
      throw error;
    }
  };

  const registerWithEmail = async (email, password) => {
    try {
      setLoading(true);
      await firebaseRegisterWithEmail(email, password);
      // onAuthStateChange will handle the rest
    } catch (error) {
      console.error('Error registering with email:', error);
      setLoading(false);
      throw error;
    }
  };

  const signOut = async () => {
    try {
      await firebaseSignOut();
      setUser(null);
      setIsAuthenticated(false);
    } catch (error) {
      console.error('Error signing out:', error);
      throw error;
    }
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, loading, user, signIn, signInWithEmail, registerWithEmail, signOut }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
