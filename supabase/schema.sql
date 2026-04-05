-- Run this once in Supabase SQL editor

create extension if not exists "uuid-ossp";

-- Main jobs table
create table if not exists jobs (
  id           uuid primary key default uuid_generate_v4(),
  hash         text unique not null,
  title        text not null,
  company      text,
  location     text,
  job_type     text,
  salary       text,
  url          text,
  description  text,
  source       text,
  posted_at    timestamptz,
  scraped_at   timestamptz default now(),
  status       text default 'new',
  is_bookmarked boolean default false,
  is_hidden    boolean default false,
  applied_at   timestamptz
);

create index if not exists jobs_source_idx on jobs(source);
create index if not exists jobs_status_idx on jobs(status);
create index if not exists jobs_scraped_at_idx on jobs(scraped_at desc);
create index if not exists jobs_is_hidden_idx on jobs(is_hidden);

-- Scrape run logs
create table if not exists scrape_runs (
  id          uuid primary key default uuid_generate_v4(),
  started_at  timestamptz default now(),
  ended_at    timestamptz,
  jobs_added  integer default 0,
  jobs_found  integer default 0,
  source      text,
  status      text default 'running',
  error_msg   text
);

-- Saved search profiles
create table if not exists search_profiles (
  id        uuid primary key default uuid_generate_v4(),
  name      text,
  keywords  text[],
  location  text,
  sites     text[],
  is_active boolean default true,
  created_at timestamptz default now()
);
