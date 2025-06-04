// Supabase client setup and API endpoints for session management and metadata

import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.REACT_APP_SUPABASE_URL || '';
const supabaseKey = process.env.REACT_APP_SUPABASE_ANON_KEY || '';

export const supabase = createClient(supabaseUrl, supabaseKey);

// Example: Save session metadata
export async function saveSessionMetadata(userId: string, sessionData: any) {
  const { data, error } = await supabase
    .from('sessions')
    .insert([{ user_id: userId, data: sessionData }]);
  if (error) throw error;
  return data;
}

// Example: Fetch user sessions
export async function fetchUserSessions(userId: string) {
  const { data, error } = await supabase
    .from('sessions')
    .select('*')
    .eq('user_id', userId);
  if (error) throw error;
  return data;
}
