# Brand workspace release setup

Pushes to main are the deployment trigger. Use the existing Syncflow Vercel
projects only. No separate deployment or account is required.

## Backend environment

| Variable | Value/purpose |
| --- | --- |
| DATABASE_URL | Existing Neon PostgreSQL connection string, including required SSL parameters. Production migrations need it at build time. |
| DJANGO_DEBUG | `false` |
| AI_PROVIDER | `gemini` (or explicitly `huggingface`) |
| AI_MODEL | Exact text model ID available to the chosen account. Select a model whose quota/billing you have checked; no automatic paid fallback. |
| GEMINI_API_KEY | Google AI Studio API key, only for Gemini. `GOOGLE_GENAI_API_KEY` is accepted as an alias. |
| HF_TOKEN | Only for Hugging Face: inference-enabled token. `HUGGINGFACE_API_KEY` is accepted as an alias. |
| AI_DAILY_LIMIT | Optional: AI requests per workspace per UTC day; default `30`. Failed requests count because they may consume provider quota. |
| GOOGLE_CLIENT_ID | Preserve the existing Google login client ID. |
| GOOGLE_CLIENT_SECRET | Preserve the existing Google login secret. |

For Gemini, set `AI_MODEL` explicitly. Availability changes; current official
model documentation lists `gemini-3.5-flash-lite` and `gemini-3.8-flash` for new
projects and restricts access to the older 2.5 models to prior users. Check the
chosen account's free quota before enabling it. A missing key/model, unavailable
model, provider error, or exhausted quota returns an error; no fake content is
saved. Hugging Face model IDs may include a provider suffix; choose a model that
supports JSON output. Token/model are server-only, never VITE variables.

## Frontend environment

| Variable | Value/purpose |
| --- | --- |
| VITE_API_BASE_URL | Actual backend origin, e.g. `https://api.syncfloww.com`, without an `/api` suffix. |
| VITE_GOOGLE_CLIENT_ID | Existing Google login client ID, matching the backend. |
| VITE_QA_MODE | `false` for production. |

Frontend variables are read at build time. Adding/changing them requires a new
build using the existing project's redeploy controls or the next Git push.

## Database and runtime

The backend now explicitly selects Vercel's Django framework in `vercel.json`.
It uses `syncfloww.wsgi.application`, not the old Node development proxy.
Its production build command installs dependencies and applies migrations via
`scripts/vercel-build.sh`; preview builds do not migrate a shared production DB.
Vercel's Django framework collects static files automatically.

Migrations `social.0008`, `0009`, and `0010` add interview state, assistant
conversation, and consent-recorded brand contacts. They add tables/columns and
do not remove existing business records. Back up the existing Neon database
before the first production migration using its existing backup facilities.
After setting required variables, the existing backend project must build again.
If project settings enforce a custom root directory or framework, ensure the
root is this repository's directory containing `manage.py` and framework is
Django. No Vercel account was connected or changed by this release.

`GET /api/health/` returns `ready` and the deployed commit SHA when the new DB
tables can be read. It returns HTTP 503 if database/migrations are not ready.
This does not verify AI credentials or social integrations.

## Live acceptance checklist

No local app tests/builds were run for this release, at the owner's request.
All boxes below remain open until verified on the existing live URLs.

- [ ] Backend health returns ready for the new GitHub commit.
- [ ] Frontend shows the new homepage and brand-focused dashboard.
- [ ] Password and Google login work with existing registered redirect origins.
- [ ] Brand setup saves, resumes, edits, and finishes with all required answers.
- [ ] AI interview help offers a draft that is only saved after user review.
- [ ] Assistant replies and seven-day plans persist after refresh.
- [ ] TXT/PDF/DOCX upload respects consent, size/type/text limits; deletion removes reference text.
- [ ] Voice input requests microphone permission and leaves editable text.
- [ ] Script generation uses saved brand facts; errors do not create a script.
- [ ] Script edits create versions; script deletion removes its history.
- [ ] Switching workspaces never shows another workspace's saved content.
- [ ] Viewers cannot mutate brand resources, scripts, assistant history or leads.
- [ ] Contact recording requires consent and source; deletion works.
- [ ] AI daily limit fails cleanly without simulated fallback.

## Remaining work before the complete MVP

This release implements brand setup, assistance, references, scripts and manual
consent-recorded contacts. It is not the complete social automation MVP.

- Official social OAuth adapters still contain development fallbacks and old
  API versions; connection needs an audit, durable state storage and platform
  approval before it can be called production-ready.
- Legacy publishing adapters report simulated success. Publishing and scheduling
  service entrypoints now return 503 without modifying drafts. Real publishing,
  retries, platform receipts and durable scheduling remain to implement.
- Comment/inbox synchronization, reviewed replies and automatic lead capture
  remain to implement. Comments currently show only their owner's records.
- Plan billing, per-plan features and a full limits screen remain to implement.
- Business identity, support contact, privacy/terms, optional-cookie consent and
  marketing email unsubscribe require final product implementation and verified
  owner details. Do not treat the homepage disclosure as a complete policy.
- Legacy media/AI/CRM screens and provider simulations outside the core path
  remain under audit. They are not promoted in the new primary navigation.
- Existing committed Django signing secret and OAuth encryption fallback need a
  deployment-aware migration. Do not rotate secrets blindly: encrypted social
  tokens currently depend on that secret. This release does not rotate it.

## Sources

- https://vercel.com/docs/frameworks/full-stack/django
- https://ai.google.dev/gemini-api/docs/models
- https://ai.google.dev/api/generate-content
- https://huggingface.co/docs/inference-providers/tasks/chat-completion
