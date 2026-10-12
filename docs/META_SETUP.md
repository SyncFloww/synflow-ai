# Meta social connection and publishing setup

Use the existing backend and frontend Vercel projects. No new Vercel project.
This increment implements real Facebook Page and linked Instagram professional
account connections, confirmed Facebook text/image and Instagram single-image
publishing, receipts/history, comment refresh and reviewed public replies.
AI reply drafts use the existing brand assistant, quota and Gemini configuration.
It also provides queued scheduling and opt-in bounded automatic replies. DMs and videos remain unsupported.

Backend Production environment:
- FACEBOOK_APP_ID and FACEBOOK_APP_SECRET: existing Meta app credentials.
- META_GRAPH_VERSION: supported version selected for your app (format vNN.N).
  Copy the version from your Meta developer dashboard; do not use an expired API.
- META_REDIRECT_URI: https://www.syncfloww.com/social/callback
- SOCIAL_TOKEN_ENCRYPTION_KEY: a URL-safe base64 encoded 32-byte Fernet key.
  Generate privately with Python/cryptography's Fernet.generate_key().
  Keep this key stable: changing it requires reconnecting these new accounts.
  It is separate from the existing Django secret and legacy OAuth token key.

In Meta app configuration, add the exact META_REDIRECT_URI to valid OAuth
redirect URIs for Facebook Login. Use your existing app and select the business
login configuration appropriate to the permissions requested. Test using app
roles while the app is in development mode. Wider access depends on Meta app
review and any required business verification; code cannot grant those approvals.

Requested Facebook Login permissions:
public Page discovery: pages_show_list; read: pages_read_engagement,
pages_read_user_content; publish: pages_manage_posts; reply:
pages_manage_engagement. Linked Instagram: instagram_basic,
instagram_content_publish, instagram_manage_comments.

The Meta consent screen selects authorised Pages. All returned authorised Pages
and linked Instagram accounts attach to the currently selected Syncflow brand.
This uses Facebook Login, not the separate Instagram Login scope family.
Tokens never appear in account API responses. The session is database-backed,
expires in 15 minutes and is consumed once. No mock fallbacks in these endpoints.
Disconnect clears the locally stored token; it does not revoke app permissions
for every Page in the Meta account. Revoke broader access in Meta settings.

Migration social.0012 adds MetaSession, MetaConnection and MetaPublication.
The existing production build applies it. No existing social records are deleted.
Legacy social adapters are not converted or promoted through the new screen.

Use /social to connect, choose an account and review a caption. Instagram requires
a publicly reachable HTTPS image URL; this increment has no new upload service.
Publish requests use a persistent client request ID. An unconfirmed send is marked
uncertain and is not resent automatically; check the platform before a new draft.
Comments are fetched only for this app's published records, first 50 per post.
Manual reply drafts are editable and sent after explicit confirmation. Automatic replies require a separate explicit per-account opt-in.

Live acceptance (all pending):
- Connect one authorised Page and its linked Instagram professional account.
- Reject replayed/expired state and an account from another workspace.
- Confirm no tokens in browser API responses or publish history.
- Publish Facebook text/image and Instagram image, inspect platform receipts.
- Fetch comments and send a reviewed reply, inspect the public platform result.
- Retry same publication request ID without producing another remote post.
- Confirm denial/reconnect errors and uncertain publish states are visible.
- Disconnect and confirm publishing is disabled for that account.

Source review and git diff --check only; local app tests/builds were not run per
owner instruction. Meta approval, configuration and actual live flows remain
unverified. The initial worker is polling-based and runs daily, rather than continuously. Real-time webhooks and frequent scheduling remain to be configured or implemented.

Official reference:
https://www.postman.com/meta/instagram/documentation/6yqw8pt/instagram-api

## Scheduled posts and opt-in reply worker

Migration social.0013 adds schedule author/time, automation settings, persistent
reply records and a worker lease. Accounts default to automatic replies OFF.
Reconnecting or disconnecting resets automation to OFF. The enabling manager's
workspace role and account activity are checked at worker execution time.

Add backend CRON_SECRET: a private random string of at least 32 characters.
The worker GET /api/social/meta/cron/ accepts Authorization: Bearer <CRON_SECRET>.
Vercel supplies this header for configured cron jobs when CRON_SECRET is set.
Do not put the secret in a URL or in frontend VITE variables.

The committed cron is 0 8 * * * (daily, nominally 08:00 UTC / 09:00 Lagos).
This is compatible with Hobby's daily-only cron limit and loose timing. It
processes one due post OR one new comment per invocation; large queues need more
worker invocations. This is not exact-time or real-time automation. A compatible
existing scheduler can call the same protected endpoint more frequently; no paid
service is created or enabled by this code. Owners can use the authenticated
Run one worker check button for their chosen account during live testing.

Posts queue after explicit content confirmation and publish on a check after
the scheduled time. Queued posts can be cancelled before the worker claims them.
Failed/uncertain sends are not retried automatically. Check the platform before
creating a replacement, as network failures can occur after a successful send.

Auto replies consider only comments newer than activation on the latest three
posts published through this app, at most the first 50 comments per post. At most
five sent/in-flight/uncertain replies per account per UTC day are allowed.
Workspace AI quota also applies. A persistent unique post/comment record prevents
manual and automatic duplicate replies. Generation failures and non-routine
comments are marked needs_review. Unconfirmed sends are uncertain. These appear
in reply history. No retry is performed on uncertain sends.

AI may reply automatically only to greetings, thanks and questions answerable
from saved brand context. It is instructed to route ambiguous comments, complaints,
orders, private data and unsupported claims to review. This classification is an
AI judgement, so account owners should review early replies closely. Disabling
automation prevents new sends, but a send already in flight may complete.

Additional live acceptance, all pending:
- Queue a post, run the worker after its due time and verify one platform receipt.
- Cancel a queued post and verify the worker never sends it.
- Enable replies deliberately; old comments are ignored.
- Add a routine comment and verify one public reply and its history receipt.
- Verify repeated worker/manual attempts do not duplicate the reply.
- Verify ambiguous comments and provider failures go to needs_review.
- Verify disconnected accounts and removed manager permissions block execution.
- Verify worker rejects missing/wrong secret and simultaneous invocations.

Source validation: Python/TSX syntax parsing and git diff --check only. No local
application tests or builds. End-to-end live verification remains pending.
