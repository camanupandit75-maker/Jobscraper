export interface SearchProfile {
  id: string;
  name: string | null;
  keywords: string[] | null;
  location: string | null;
  sites: string[] | null;
  is_active: boolean | null;
  created_at?: string;
}

export const PROFILE_SITE_OPTIONS = [
  "remoteok",
  "indeed",
  "linkedin",
  "naukri",
  "internshala",
  "wellfound",
  "glassdoor",
] as const;
