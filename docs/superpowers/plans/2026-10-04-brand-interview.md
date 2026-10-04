# Brand interview implementation plan

**Goal:** Save and resume a guided brand interview, review its answers, and use the resulting brand context for scripts.

**Architecture:** Reuse BrandProfile and BrandVoice. Store a validated answer map and completion flag on BrandProfile. A brand-scoped endpoint returns questions and progress and updates structured profile fields atomically. The existing onboarding page consumes it; authentication stays unchanged.

**Tech stack:** Django/DRF, React/TypeScript, existing UI components.

**Spec:** ../../MVP_EXECUTION.md. Ten days is a deadline, not a daily work restriction.

## Constraints and review focus

- No new paid service or AI credentials required for the guided interview.
- Label the interview as guided setup, without pretending rule-based questions are live AI responses. Adaptive AI assistance and document ingestion follow separately.
- Refuse writes from non-manager members and users outside the workspace.
- Partial answers must survive reload and cannot complete an incomplete interview.
- Explicit workspace selection must prevent accidental creation in another workspace.
- Reject unknown fields, oversized answers, and malformed payloads without partial writes.
- Do not retain interview answers in browser storage; store them on the authenticated backend.

## Tasks

- [x] Add `BrandProfile.onboarding_answers` and `onboarding_completed` with an additive migration.
- [x] Add `social/onboarding.py`: question definitions, validation serializer, profile synchronization, response progress.
- [x] Add GET/PATCH `/api/social/brands/{id}/onboarding/`, reusing membership checks and manager write permissions.
- [x] Test save/resume, completion validation, scope isolation, permissions, malformed answers, and goal propagation.
- [x] Replace onboarding with accessible one-question-at-a-time setup, server saving, review/edit, explicit workspace selection, and script-studio continuation.
- [x] Run backend regression checks and frontend build; commit verified changes separately in each repository.

## Verification

16 backend tests pass. Frontend TypeScript check and production build pass. No live browser, provider, or Vercel deployment verification has been performed. Apply `python manage.py migrate` before deploying the frontend. No new credentials are needed for guided setup.
