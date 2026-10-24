# SkillBridge — Phase Prompts for Claude Code

How to use:
1. Create an empty project folder, put `CLAUDE.md` in its root.
2. Paste ONE phase prompt at a time. Don't move on until that phase works.
3. Tick the checklist at the end of each phase yourself.

---

## Phase 0 — Project setup
```
Read CLAUDE.md fully. Then set up the monorepo:
- /frontend (Next.js 15, TypeScript, Tailwind, shadcn/ui)
- /backend (FastAPI, SQLAlchemy 2, Alembic, pytest)
- docker-compose.yml with frontend, backend, postgres
- .env.example for both apps (Supabase URL/keys, GEMINI_API_KEY, LLM_MODEL, YOUTUBE_API_KEY)
- Lint/format: ruff + black (backend), eslint + prettier (frontend)
- A /health endpoint and a homepage that calls it
Plan first and show me the folder tree before writing code.
```
✅ Done when: `docker compose up` works and the homepage shows "backend: ok".

---

## Phase 1 — Auth, profile and data model
```
Implement Phase 1 from CLAUDE.md:
- Supabase Auth (email + Google) on the frontend; backend verifies the JWT
- Alembic migrations for every table in CLAUDE.md section 4
- Row Level Security policies so users only see their own rows
- Seed script: 3 fields + ~60 common skills with aliases
- Onboarding page: name, university, year, department, CGPA, field, track
- Manual skill picker (search skills, set level 0–5) for students without a CV
Write tests for the JWT check and the profile endpoints.
```
✅ Done when: I can sign up, finish onboarding, add skills manually, and log out/in without losing data.

---

## Phase 2 — CV upload and parsing
```
Implement CV upload and parsing:
- Consent checkbox (store consent_at) before the upload button activates
- Upload PDF/DOCX (max 5 MB) to the private Supabase bucket
- Send the file to Gemini and get structured JSON: education, cgpa, skills (name + estimated level + evidence line), projects, experience, languages, test scores, stated interests
- Validate with Pydantic; map skills to the skills table via aliases; unknown skills go to a review list
- Show a "Review your profile" screen where the student confirms or edits extracted skills before saving
- Handle errors: scanned/blurry PDF, empty CV, wrong file type
Add tests with 2–3 sample CVs (fake data only) in /backend/tests/fixtures.
```
✅ Done when: a sample CV becomes an editable, saved skill profile.

---

## Phase 3 — Opportunity discovery
```
Implement opportunity discovery for the student's field + track:
- seed_opportunities: load ~10 verified real examples per field from /backend/seed/opportunities.json (I will fill real data; create the file with the schema and 2 clearly marked placeholder rows)
- Grounded search: use Gemini with Google Search grounding to find current openings (job), professors/labs recruiting RAs (research), or scholarships (scholarship) relevant to Bangladeshi undergrads
- Extract structured items: title, org, person_name, location, required_skills, deadline, source_url
- HARD RULE: drop any item without a real source URL from the grounding metadata
- Cache results per field+track for 24 hours in the opportunities table
- Use the PII-stripped profile summary only — never the raw CV
```
✅ Done when: each result shows a working source link and "Last checked" date, and no item lacks a source.

---

## Phase 4 — Skill-gap analysis
```
Implement the analysis from CLAUDE.md section 5:
- Match % per opportunity (matched vs missing skills)
- Skill-gap priority score; top 3 gaps highlighted with a one-line reason each
- Save each run in analyses + skill_gaps
- Results dashboard: opportunity cards (match %, source link), gap list sorted by priority, disclaimer banner
- Enforce the daily rate limit
Unit-test the scoring functions with fixed inputs.
```
✅ Done when: the dashboard shows ranked opportunities and a prioritized gap list, and the scoring tests pass.

---

## Phase 5 — 20-hour learning protocol
```
Implement the learning engine:
- "Start learning" button on a gap → generate a plan using the exact JSON schema in CLAUDE.md section 5, tailored to the student's field and track
- Pre self-check (8–10 questions/tasks) before the plan starts
- YouTube Data API: run each video_query, pick 2–3 short, recent, well-rated videos per subskill; show timestamps ONLY from real chapter markers in the description
- Plan page: target performance, subskills, "learn just enough", "avoid for now", barriers to remove, schedule, capstone
- About page crediting Josh Kaufman's "The First 20 Hours" as inspiration (our own wording only)
```
✅ Done when: a gap turns into a full plan with real video links and a pre-check score.

---

## Phase 6 — Progress tracking and re-analysis
```
Implement progress and the feedback loop:
- Hour-block checkboxes with notes, saved to practice_sessions; visual 0–20h progress bar
- Post self-check unlocks at 20 hours; target reached = post-check ≥ 60% AND capstone marked complete
- On success: raise the skill level in profile_skills (source: quiz) and offer "Re-run analysis" showing the before/after match %
- Simple streak counter and "next session" reminder text on the dashboard
```
✅ Done when: finishing a plan visibly raises the match % in a new analysis.

---

## Phase 7 — Hardening and privacy
```
Harden the app:
- Audit RLS policies and every endpoint for auth checks; list any gaps you find
- "Delete my data" (DB rows + stored CVs) with confirmation
- Loading, empty and error states on every page
- Basic logging without PII; LLM cost/usage counter per user
- Playwright end-to-end test of the full flow: sign up → CV → analysis → plan → progress
- Move all UI strings to an i18n file (English only for now)
Report findings as a checklist before fixing them.
```
✅ Done when: the E2E test passes and the security checklist is all green.

---

## Phase 8 — Deployment
```
Prepare deployment:
- Frontend on Vercel, backend on Render or Railway (Dockerfile), Supabase for DB/auth/storage
- Production env var checklist, CORS locked to the frontend domain
- README: setup, architecture diagram (Mermaid), env vars, how to add a new field, known limitations
Explain each step I need to do manually in the hosting dashboards.
```
✅ Done when: the live URL works end-to-end with a fresh account.

---

## Release 2 ideas (after MVP)
- Professor cold-email drafter (from the student's profile + the professor's source page)
- CV improvement suggestions after finishing a skill
- Bangla UI toggle
- Scheduled daily opportunity refresh
- Admin page to verify/flag opportunities
