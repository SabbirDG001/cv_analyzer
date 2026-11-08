# Deploying SkillBridge for free

| Part | Where | Cost |
|---|---|---|
| Database, auth, CV storage | Supabase | Free tier |
| Backend (FastAPI) | Render web service | Free (sleeps after ~15 min idle; first request takes ~30-60 s) |
| Frontend (Next.js) | Vercel | Free (Hobby) |
| LLM | Google AI Studio key | Free tier with rate limits |

## 1. Supabase
1. Create a project. Storage -> new **private** bucket named `cvs`.
2. Auth -> URL Configuration: set Site URL to your Vercel URL and add `<vercel-url>/auth/callback` to Redirect URLs.
3. Collect: Project URL, anon key, service_role key (secret), and the **Session pooler** connection string
   (change the prefix to `postgresql+psycopg://`).

## 2. Backend on Render
1. render.com -> New -> Blueprint -> pick this GitHub repo (reads `render.yaml`).
2. Fill the env vars it asks for: `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `GEMINI_API_KEY`,
   `LLM_MODEL`, `FRONTEND_ORIGIN` (set after step 3, then redeploy).
3. On each start it runs the Alembic migration and seed, then serves. Check `https://<service>.onrender.com/health`.

## 3. Frontend on Vercel
1. vercel.com -> Add New Project -> this repo -> **Root Directory: `frontend`**.
2. Env vars: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`,
   `NEXT_PUBLIC_API_URL` = the Render URL.
3. Deploy, then put the Vercel URL into Render's `FRONTEND_ORIGIN` and Supabase's redirect settings.

Secrets only go in these dashboards, never in the repo. Google sign-in needs a Google Cloud OAuth client
whose redirect is `https://<project>.supabase.co/auth/v1/callback`, configured under Supabase -> Auth -> Providers.
