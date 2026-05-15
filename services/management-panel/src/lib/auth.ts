import { createClient, Session } from '@supabase/supabase-js';

const supabaseUrl = ((import.meta as any).env?.VITE_SUPABASE_URL || 'http://localhost:54321') as string;
const supabaseAnonKey = ((import.meta as any).env?.VITE_SUPABASE_ANON_KEY || 'test-anon-key') as string;

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// Auth helper functions
export async function getSession(): Promise<Session | null> {
  const { data: { session } } = await supabase.auth.getSession();
  return session;
}

export async function signOut() {
  await supabase.auth.signOut();
}

export async function onAuthStateChange(callback: (session: Session | null) => void) {
  const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
    callback(session);
  });
  return subscription;
}

export function getAccessToken(): string | null {
  // Try to get from localStorage first (set after setup)
  return localStorage.getItem('sb_access_token');
}

export function setAccessToken(token: string) {
  localStorage.setItem('sb_access_token', token);
}

export function clearAccessToken() {
  localStorage.removeItem('sb_access_token');
}
