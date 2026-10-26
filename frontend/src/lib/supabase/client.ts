import { createBrowserClient } from "@supabase/ssr";
import type { SupabaseClient } from "@supabase/supabase-js";

import { supabaseConfig } from "./config";

let browserClient: SupabaseClient | null = null;

/** Browser-side Supabase client, or null when the project keys are not set. */
export function createClient(): SupabaseClient | null {
  const config = supabaseConfig();
  if (!config) return null;
  browserClient ??= createBrowserClient(config.url, config.anonKey);
  return browserClient;
}
