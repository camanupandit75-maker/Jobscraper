-- Run once in Supabase SQL Editor: removes legacy "ai" row and inserts the corrected profile.
-- Location: india, uae, remote | Sites: indeed, linkedin, remoteok only

delete from search_profiles
where lower(trim(name)) = 'ai';

insert into search_profiles (name, keywords, location, sites, is_active)
values (
  'ai',
  array[
    'AI engineer',
    'machine learning',
    'ML engineer',
    'artificial intelligence',
    'LLM'
  ],
  'india, uae, remote',
  array['indeed', 'linkedin', 'remoteok']::text[],
  true
);
