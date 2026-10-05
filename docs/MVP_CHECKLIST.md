# Syncflow MVP checklist

Checked = implemented in code, not yet live verified. See RELEASE_SETUP.md for
live checks and environment variables. The ten days are an overall deadline,
not a requirement to wait between tasks.

## Brand understanding
- [x] Saved/resumable seven-question brand interview and review
- [x] AI help for unclear answers with explicit acceptance of suggested drafts
- [x] Saved conversational assistant and seven-day strategy suggestions
- [x] Browser voice-to-text with editable transcript and service disclosure
- [x] TXT/Markdown/PDF/DOCX text extraction with consent and limits
- [x] Reference deletion and conversation clearing
- [x] Brand audience, voice, products, boundaries and goal in script context
- [ ] Live verification of the above

## Content
- [x] Real server-configured Gemini/Hugging Face text requests
- [x] Validated scripts with no fake fallback on failed generation
- [x] Brand-scoped script library, search of loaded results, editing and versions
- [x] Script deletion and copy
- [x] Saved-script review and approval; edits and restored versions clear approval
- [x] Restore version content as a new draft while keeping history
- [x] Revision checks prevent approving a script that changed since it was opened
- [x] Workspace AI daily request limit
- [x] Usage screen with request counts, remaining allowance and reset time
- [x] Dedicated brand idea library with editing, review, approval and conversion to scripts
- [ ] Complete live verification of provider quota, generation and editing

## Social automation
- [ ] Audited official social OAuth with production state storage
- [ ] Facebook Page/Instagram account selection and capability checks
- [ ] One real official publishing path with verified receipts
- [ ] Durable scheduling, cancellation, retries and logs
- [ ] Comment/inbox synchronization and consent-respecting reviewed replies
- [ ] Automatic lead capture with source and opt-in evidence
- [x] Manual brand contact list with required consent/source and deletion
- [ ] Live social integration acceptance

## Trust and release
- [x] New homepage, dashboard and focused navigation; existing logo/theme retained
- [x] Manager-only mutation permissions on brand resources and core script paths
- [x] Comments isolated by owner; explicit confirmation for social-login account deletion
- [x] Repository-controlled Django runtime and production migration build hook
- [x] Public readiness endpoint exposing release SHA without customer records
- [x] Working display-name settings, password change, device theme and core brand-data export
- [ ] Complete tenant/security audit of legacy modules
- [ ] Signing secret and OAuth encryption migration
- [ ] Privacy/terms/business identity, optional-cookie and email consent workflows
- [ ] Plans, billing and per-plan entitlements
- [ ] Full mobile, keyboard and accessibility acceptance
- [ ] End-to-end live acceptance and rollback verification
