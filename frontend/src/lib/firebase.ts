import { getApps, initializeApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider, signInWithPopup } from 'firebase/auth';

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
};

export const firebaseAuthConfigured = Object.values(firebaseConfig).every(Boolean);

const firebaseAuth = firebaseAuthConfigured
  ? getAuth(getApps()[0] ?? initializeApp(firebaseConfig))
  : null;

export async function signInWithGoogle() {
  if (!firebaseAuth) throw new Error('Firebase is not configured');
  const provider = new GoogleAuthProvider();
  provider.setCustomParameters({ prompt: 'select_account' });
  return signInWithPopup(firebaseAuth, provider);
}
