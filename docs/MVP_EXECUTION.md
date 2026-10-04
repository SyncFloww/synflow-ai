# Syncflow MVP execution

## Product and constraints

Syncflow helps a user teach an assistant about their brand, set business goals,
generate scripts, connect supported social accounts, publish content, manage
permitted conversations, and capture leads with consent. Retain the current
visual theme and working password and Google authentication. Use free services
first; no purchase or paid fallback is authorized. Keep credentials server-side.

Reuse Django/DRF and React. Keep one brand for initial testers while retaining
the existing workspace and brand model for later plans. Do not delete existing
business records when simplifying navigation. Push authorized changes to main in both repositories. The existing Vercel
integration deploys them; acceptance testing is live only at the owner’s request.

## Execution sequence within the ten-day deadline

The day labels below indicate order and dependencies, not daily restrictions.
Complete and test increments as quickly as possible; finish early when feasible.

| Day | Deliverable | Acceptance |
| --- | --- | --- |
| 1 | Baseline and script integrity | Provider failures never create fake scripts; successful scripts use brand context; login regression checks recorded |
| 2 | Conversational brand onboarding | Interview can resume; user reviews and edits the saved profile; unclear answers produce useful follow-up questions |
| 3 | Goals and brand references | Save goals and source documents; enforce tenant isolation and upload limits; disclose AI processing |
| 4 | Script workspace | Generate, edit, save, regenerate and retrieve scripts; explicit error states; accessible inputs |
| 5 | Free AI configuration | Verify current provider credits, terms and available models; configure server-side credentials; stop cleanly at quota exhaustion |
| 6 | Social connection | Start with Facebook Pages/Instagram professional accounts subject to verified official API support; preserve login separately from account connection |
| 7 | Publish and scheduling | One real supported publishing path; approval before sending; durable execution and logs verified against hosting constraints |
| 8 | Conversations and leads | Permitted comment/inbox replies with brand context, review controls, opt-in lead capture and source tracking |
| 9 | Trust and accessibility | Accurate policies and business details, optional-cookie consent, data deletion, form consent, email unsubscribe, SDK and asset audit, keyboard/contrast fixes |
| 10 | Tester release | End-to-end production checks, usage limits, account isolation, rollback procedure and known limitations documented |

This sequence is a target, not a promise that platform review or service approval
will finish within ten days. Unsupported social actions must be shown as
unavailable; do not substitute browser automation or mock success.

## Current repository findings

- Backend: brand profile, knowledge, voice/goal, scripts and version records exist.
- Frontend: onboarding is a short form; social connect controls there are disabled.
- Script generation previously substituted generic content for missing AI fields
  and persisted scripts after failed jobs.
- Router detail routes shadowed named generation routes such as
  `/api/ai/scripts/generate/`, producing HTTP 405.
- Provider adapters can return offline simulations. The script path now rejects
  these because they lack required script fields. Other AI paths need auditing.
- Authentication tests currently include JWT lifetime expectations and a Google
  development-mock expectation that disagree with existing behavior. Do not
  label authentication regression-free until those are resolved or explained.
- The committed Django secret key needs a separate deployment-aware remediation;
  rotating it requires checking the current JWT and session configuration.

## First increment

Script jobs use saved brand context and validate required and optional fields.
Failed or malformed generations return a generic HTTP 503 without exposing
provider details or creating scripts. Named action URLs precede router detail
URLs. Focused tests use controlled provider responses and require no API token.

No new environment variables or database migrations are required for this
increment. Live inference and deployment verification are separate from local
tests. Provider choice and free-tier feasibility remain unverified; do not
advertise unlimited free inference or guaranteed performance.


## Current implementation status

The historical findings above describe the initial audit. For the current code
and remaining work, use [MVP_CHECKLIST.md](MVP_CHECKLIST.md). Environment and live
acceptance instructions are in [RELEASE_SETUP.md](RELEASE_SETUP.md).
