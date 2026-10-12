# One-time release configuration checklist

Use existing Syncflow Vercel projects connected to GitHub main. Add secrets only
in backend Production environment, then redeploy. Never paste values into chat.

## Backend

| Variable | Purpose |
| --- | --- |
| DATABASE_URL | Existing Neon PostgreSQL SSL connection string |
| DJANGO_DEBUG | false |
| AI_PROVIDER | gemini |
| AI_MODEL | Gemini text model available to your Google project |
| GEMINI_API_KEY | Active Gemini key with access to that model |
| GOOGLE_CLIENT_ID | Google account sign-in client ID |
| GOOGLE_CLIENT_SECRET | Google account sign-in secret |
| AI_DAILY_LIMIT | Optional; defaults to 30 requests/workspace/UTC day |
| FACEBOOK_APP_ID | Existing Meta app ID |
| FACEBOOK_APP_SECRET | Existing Meta app secret |
| META_GRAPH_VERSION | Supported version from your Meta developer dashboard, vNN.N |
| META_REDIRECT_URI | https://www.syncfloww.com/social/callback |
| SOCIAL_TOKEN_ENCRYPTION_KEY | Privately generated Fernet key; keep stable |
| CRON_SECRET | Private random string of at least 32 characters |

Generate a Fernet key privately with cryptography.fernet.Fernet.generate_key().
Do not rotate SOCIAL_TOKEN_ENCRYPTION_KEY after connections are stored without
planning to reconnect them. Existing SECRET_KEY environment settings are not
used by the legacy Django settings; this release does not rotate that secret.

## Frontend

| Variable | Purpose |
| --- | --- |
| VITE_API_BASE_URL | Backend origin, e.g. https://api.syncfloww.com, no /api suffix |
| VITE_GOOGLE_CLIENT_ID | Same Google sign-in client ID |

Remove old VITE_QA_TEST_TOKEN and VITE_DEMO_EMAIL/VITE_DEMO_PASSWORD values.
Only public values belong in VITE variables. Google login client ID is public.

## Account settings and live checks

Register frontend origins in your existing Google OAuth configuration. Register
META_REDIRECT_URI exactly in Facebook Login valid redirect URIs. Meta permissions,
app roles/review and linked professional Instagram accounts are described in
[META_SETUP.md](META_SETUP.md). Google login and social account connection are
separate flows; signing into Syncflow does not grant social publishing access.

Confirm both production deployments succeed for current main. Backend build
applies additive migrations social.0012 and .0013; verify /api/health/ first.
Then test account sign-in, brand setup, AI generation, Meta connection, manual
publishing, comment review, queued posts and deliberately enabled auto replies.

The initial worker cron checks daily and processes one action per run. Precise
scheduling and continuous replies require a compatible frequent scheduler.
AI access denial remains a Google project/key configuration blocker until verified.
This checklist covers this implemented release, not billing or other social
platforms. Those parts of the broader MVP remain unfinished.
