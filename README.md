# JobRadar — Personal Job Scraper

Scrapes 7 job sites every 4 hours. Private dashboard on Vercel.

## Stack

- **Frontend**: Next.js 14 → Vercel (free)
- **Worker**: Python + Playwright → Railway (~$5/mo)
- **Database**: Supabase (free tier)

## Setup in 4 steps

### Step 1 — Supabase

1. Create a free project at [supabase.com](https://supabase.com)
2. Go to SQL Editor → paste contents of `supabase/schema.sql` → Run
3. Copy your Project URL and anon/service keys

### Step 2 — Railway Worker

1. Push the `worker/` folder to a GitHub repo (or subdirectory)
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Select the `worker/` directory
4. Add environment variables:
   - `SUPABASE_URL` = your Supabase project URL
   - `SUPABASE_KEY` = your Supabase **service role** key
5. Railway auto-detects the Dockerfile and deploys
6. Worker starts immediately and runs every 4 hours

### Step 3 — Vercel Frontend

1. Push the `frontend/` folder to GitHub
2. Go to [vercel.com](https://vercel.com) → New Project → Import
3. Set Root Directory to `frontend/`
4. Add environment variables:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_KEY`
5. Deploy

### Step 4 — Edit Your Search Preferences

Edit `worker/config.py`:

- Change keywords to match your target roles
- Change locations to your target markets
- Adjust `SCRAPE_INTERVAL_HOURS` (default: 4)

## Customizing

- Add more search profiles in `config.py`
- Toggle which sites to scrape per profile
- Use the dashboard to bookmark, mark applied, or hide jobs
- Export filtered results to Excel anytime

## Local development

1. `cd frontend && npm install && cp .env.local.example .env.local` — fill Supabase keys, then `npm run dev` (config is `next.config.mjs` because Next 14.2 does not load `next.config.ts`)
2. `cd worker && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && playwright install chromium` — copy `.env.example` to `.env`, then `python main.py`

The worker runs one scrape on startup, then every `SCRAPE_INTERVAL_HOURS`. The app is at [http://localhost:3000](http://localhost:3000).

## Manual scrape from the dashboard

Optional: expose an HTTP endpoint on Railway that runs `run_scrape` and set `RAILWAY_TRIGGER_URL` in Vercel so **Run scrape** can call it. The worker in this repo is process-only; add a small HTTP server if you need remote triggers.
