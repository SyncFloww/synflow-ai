# Facebook and TikTok release execution

Goal: real Facebook Page and TikTok creator publishing flows, then business engagement.
Owner constraints: push main in both repos, existing Vercel projects only, live app tests only, preserve brand identity.

- [x] TikTok durable OAuth, encrypted refresh rotation and private-by-default audit gate.
- [x] Creator info, explicit post options, URL video preview, send/status/scheduling/cancel.
- [x] Facebook PostgreSQL schedule repair, permission/readiness checks and reviewed Messenger replies.
- [x] Platform readiness UI and complete setup/approval checklist; separate restricted TikTok business APIs.
- [ ] Static source checks, review, main pushes and deployment status.

Ruling: no local application tests/builds — owner's explicit live-only instruction supersedes skill TDD.
Ruling: main publication is pre-authorized; use a working branch and fast-forward main via GitHub.
Ruling: TikTok business comment/DM access cannot be inferred from Login Kit. Do not simulate it or expose unavailable controls as working.

Final review: independent source review completed; no local app execution.
Important findings corrected: Meta/TikTok route isolation, rotated token rollback and lock ordering, inactive workspace access, cross-tenant worker cleanup, mismatched duplicate payloads, inaccurate worker status and editable sent composer.
Ruling: no paid scheduler enabled — retain existing daily worker with explicit timing limits; exact-time posts remain unavailable until a compatible frequent scheduler is configured.
Ruling: do not rotate existing Django/OAuth encryption secret — unrelated token migration could break existing accounts.
Static checks and publication results are recorded in the release commit message.
