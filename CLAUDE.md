# SkillBridge — Project Context for Claude Code

> Working name. Rename freely. This file is the source of truth for scope, stack and rules.
> Read it fully before every task. If a request conflicts with this file, ask before proceeding.

## 1. What we are building

An AI-powered career-guidance and rapid-skill-acquisition web platform for **undergraduate students in Bangladesh**.

Flow: **Profile (CV upload or manual) → Field + Track → Live opportunity discovery (with sources) → Skill-gap analysis → 20-hour learning protocol → Progress tracking → Re-analysis.**

### Tracks (enum `track`)
| Track | Target | Typical requirements |
|---|---|---|
| `job` | Companies / industry roles | Technical tools, internships, portfolio |
| `research` | Research assistant roles under professors | Methods, programming, papers, scientific writing |
| `scholarship` | Higher study abroad | CGPA, IELTS/GRE, research exposure, SOP |

### Fields (initial seed, configurable via DB table `fields`)
Biological Sciences, Computer Science & Engineering, Business Administration. Architecture must allow adding fields without code changes.

## 2. Tech stack (fixed unless I approve a change)

| Layer | Choice |
|---|---|
| Frontend | Next.js 15 (App Router) + TypeScript + Tailwind CSS + shadcn/ui |
| Backend | Python 3.12 + FastAPI + Pydantic v2 |
| Database | PostgreSQL (Supabase) + SQLAlchemy 2 + Alembic migrations |
| Auth | Supabase Auth (email + Google). Backend verifies Supabase JWT on every request |
| File storage | Supabase Storage, private bucket `cvs` |
| LLM | Google Gemini API via `google-genai` SDK. Model name in env var `LLM_MODEL` |
| Live search | Gemini **Google Search grounding** (returns source URLs) |
| Videos | YouTube Data API v3 |
| Local dev | Docker Compose (frontend, backend, postgres) |
| Tests | pytest (backend), Vitest + Playwright (frontend) |

Put all LLM calls behind a single `llm/` service module with a provider interface, so the provider can be swapped later (e.g. to the Claude API) without touching routes.

## 3. Hard rules (non-negotiable)

1. **No scraping of LinkedIn, Bdjobs or any site whose terms forbid it.** Opportunity discovery uses search grounding + a manually curated `seed_opportunities` table only.
2. **Never show an opportunity, professor or company without a real source URL.** If grounding returns no source, drop the item. Store `source_url` and `retrieved_at` for every opportunity. Show "Last checked: <date>" in the UI.
3. **Never invent YouTube timestamps.** Only show timestamps that come from video chapters in the YouTube API description. Otherwise link the whole video.
4. **All LLM output that drives UI must use structured JSON output** validated by Pydantic. On validation failure: retry once, then return a clean error.
5. **CV privacy:**
   - Consent checkbox before upload (store consent timestamp).
   - CVs in a private bucket; signed URLs only, max 10 minutes.
   - Strip phone, address, NID, email from text before it is sent to the search step (only the parse step sees the raw CV).
   - "Delete my data" endpoint removes DB rows + stored files.
   - Postgres Row Level Security: users can only read their own rows.
6. **API keys live only in backend env vars.** Never in frontend code or the repo. Provide `.env.example`.
7. **Learning-method content:** the 20-hour protocol follows the *principles* of rapid skill acquisition (deconstruct the skill, learn just enough to self-correct, remove practice barriers, commit to ~20 hours of deliberate practice), written in our own words. Credit Josh Kaufman's *The First 20 Hours* as inspiration in an About page. Never reproduce text from the book.
8. **Rate limiting:** max 10 analysis runs and 30 LLM calls per user per day (configurable).
9. **Disclaimer** on results pages: guidance only, no guarantee of selection; verify opportunities at the source.

## 4. Data model (initial — refine in Phase 1)

- `users` (from Supabase auth) → `profiles` (name, university, year, department, cgpa, track, field_id, consent_at)
- `skills` (normalized skill names + aliases)
- `profile_skills` (profile_id, skill_id, level 0–5, source: `cv` | `manual` | `quiz`)
- `cv_uploads` (profile_id, storage_path, parsed_json, parsed_at)
- `fields`
- `opportunities` (title, org, person_name nullable, type, field_id, track, location, required_skills jsonb, source_url, retrieved_at, origin: `seed` | `grounded`)
- `analyses` (profile_id, created_at, match_results jsonb, gaps jsonb)
- `skill_gaps` (analysis_id, skill_id, priority_score, unlocks_count, reason)
- `learning_plans` (profile_id, skill_id, plan_json, created_at)
- `practice_sessions` (plan_id, hour_block, completed_at, notes)
- `self_checks` (plan_id, stage: `pre` | `post`, score, answers jsonb)

## 5. Core logic

### Skill-gap priority score
`priority = (number of matched opportunities requiring the skill) × (importance weight from the LLM, 1–3) ÷ (estimated hours to reach basic proficiency)`
Show the top 3 gaps first. Explain each gap in one sentence.

### Match percentage
Per opportunity: weighted share of required skills the student has at level ≥ 2. Show matched vs missing skills side by side.

### "30–40% proficiency" definition
A student reaches the target when they pass the **post self-check** (≥ 60%) AND complete the **capstone mini-task** in their plan. Pre and post self-checks are 8–10 LLM-generated questions/tasks per skill.

### 20-hour protocol (JSON schema returned by the LLM)
```
{
  "skill": str,
  "context": str,                 // e.g. "Python for biological data analysis"
  "target_performance": str,      // what the student can DO after 20h
  "subskills": [{ "name", "why", "order" }],   // 3–6 items
  "learn_just_enough": [str],
  "avoid_for_now": [str],         // explicit "do not study yet" list
  "barriers_to_remove": [str],
  "schedule": [{ "hours": "1-3", "goal", "activities": [str], "done_when": str }],
  "capstone": { "task", "success_criteria": [str] },
  "video_queries": [str]          // used to call the YouTube API, not raw links
}
```

## 6. Working agreements for Claude Code

- Work **one phase at a time** (see the phases prompt file). Plan first, wait for my OK, then implement.
- After each phase: run tests and linters, then give me a short summary — what was built, how to run it, and what is left.
- Keep functions small; type everything; no `any` in TypeScript.
- Do not add new dependencies or services without telling me why.
- Commit after each working step with clear messages.
- If something in this file is unclear or wrong, ask me — do not guess.

## 7. Out of scope for MVP

Scheduled background crawlers, payment, mobile app, admin CMS (use seed SQL/JSON), Bangla UI (but keep all UI strings in an i18n file so Bangla can be added later).
