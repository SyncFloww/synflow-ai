# Facebook and TikTok live setup — November 2026

Code is pushed to main in the existing frontend/backend repositories. Use the
existing Syncflow Vercel projects. No separate deployment account is required.
This release is implemented code awaiting live platform setup and verification.

## What this release implements

| Platform | Implemented | Still pending |
| --- | --- | --- |
| Facebook Pages | Real OAuth/Page discovery, text/image posts, scheduled queue/cancel, comment fetch, reviewed replies, opt-in bounded automatic replies, reviewed Messenger text replies with AI drafts | Live permission/review verification, video posts, real-time webhooks, autonomous inbox replies |
| TikTok | Real creator OAuth, encrypted/rotating refresh credentials, creator-specific privacy/interaction options, MP4 URL preview, direct video posts, scheduled queue/cancel, processing status checks | App/scope approval and audit; local file uploads; photos; separate business comment and inbox adapters/authorization |

Ordinary TikTok Login Kit tokens do NOT grant Accounts API comment access or
Business Messaging access. The product explicitly identifies those as not yet
implemented. They must not be declared working until the proper business
connection has been implemented, approved and tested. Focus remains Facebook
and TikTok; no X/other-platform expansion is part of this release.

## Backend variables

Keep the core variables in [SETUP_CHECKLIST.md](SETUP_CHECKLIST.md), plus:

| Variable | Purpose |
| --- | --- |
| FACEBOOK_APP_ID | Existing/new Meta app ID |
| FACEBOOK_APP_SECRET | That app's secret; server only |
| META_GRAPH_VERSION | Version supported by your Meta developer app, e.g. format vNN.N; copy the actual supported version |
| META_REDIRECT_URI | https://www.syncfloww.com/social/callback |
| META_ENABLE_MESSENGER | true when the app has Messenger/pages_messaging access; default false |
| META_ENABLE_INSTAGRAM | false for current Facebook/TikTok focus; default false |
| SOCIAL_TOKEN_ENCRYPTION_KEY | Existing private Fernet key. Keep stable for all connected accounts |
| TIKTOK_CLIENT_KEY | Client key from TikTok for Developers Login Kit app |
| TIKTOK_CLIENT_SECRET | That app's secret; server only |
| TIKTOK_REDIRECT_URI | https://www.syncfloww.com/social/tiktok/callback |
| TIKTOK_MEDIA_URL_PREFIX | HTTPS media domain/prefix you own and have verified in the TikTok app; e.g. https://media.your-domain.example/videos/ |
| TIKTOK_PUBLIC_POSTING_APPROVED | false until the Direct Post audit is actually approved; only then true |
| CRON_SECRET | Existing private worker secret, at least 32 characters |

No additional frontend secrets or variables. Keep VITE_API_BASE_URL and
VITE_GOOGLE_CLIENT_ID. Never use VITE_ names for provider secrets or tokens.
No business API credential is requested for TikTok yet: that adapter is pending.
A refresh token's expiry is taken from TikTok, and every returned refresh token
is stored atomically before later status checks; no hard-coded access lifetime.

## Facebook app setup

1. Register the existing Syncflow frontend website and add the exact
   META_REDIRECT_URI to Facebook Login's valid OAuth redirect URIs.
2. Enable the appropriate Facebook Login/Page/Messenger products for your app.
3. Page flow requests pages_show_list, pages_read_engagement,
   pages_read_user_content, pages_manage_posts and pages_manage_engagement.
4. For the inbox, enable META_ENABLE_MESSENGER=true and obtain pages_messaging
   permission. Reconnect previously stored Pages: old connections did not record
   actual granted permission scopes. If permission is missing the inbox explains
   that it must be reconnected; it never pretends that access was granted.
5. Test using authorised app roles and a Page you manage. Public user access can
   require app review/business verification. Use genuine app branding, privacy
   policy and data deletion instructions required by Meta. These documents and
   business details must be supplied/verified by the project owner.
6. Connect through /social, choose the Page and publish a small reviewed test.
7. Fetch/reply to a test comment. Keep automatic replies off until manual access
   is verified. Enable only deliberately for the selected account.
8. For Messenger, have a tester message the Page, select that conversation and
   send a reviewed text reply. Only current inbound conversations are supported;
   the standard 24-hour reply window is enforced. No unsolicited messages/tags.

## TikTok app setup

1. Create/complete the public-facing Syncflow app on TikTok for Developers.
   Add Login Kit and Content Posting API / Direct Post. Request user.info.basic
   and video.publish. The account must authorise the approved scopes.
2. Add the exact TIKTOK_REDIRECT_URI in Login Kit Web redirect configuration.
3. Verify the owned media domain or URL prefix in the app's URL properties.
   Host a publicly readable MP4 there with correct content type and HTTPS.
   Its URL must fall under TIKTOK_MEDIA_URL_PREFIX. The media path must be
   canonical/plain (no percent-encoded path segments). URL query signatures
   are supported, but must remain valid through the scheduled publish time.
4. In unaudited testing, use a private TikTok test account and SELF_ONLY (Only me).
   Public publishing remains locked by default. A public account's creator-info
   response does not prove the app passed its audit. Do not flip the approval
   variable to bypass TikTok restrictions: it cannot grant platform permission.
5. Use /social/tiktok to connect. Select the creator account; current nickname,
   visibility choices, interaction restrictions and duration limit are loaded.
6. Load video preview, edit caption, manually choose privacy. Interactions and
   commercial disclosure default off. Add the correct promotional/paid/AI labels
   and confirm Music Usage (and Branded Content Policy when applicable).
7. Publish once. Processing is not completion; the screen polls the status
   endpoint while open. The worker also checks pending TikTok posts when no
   scheduled posts are due. Only PUBLISH_COMPLETE becomes published.
8. Scope approval/audit is separate from coding. Do not promise public results
   before TikTok approves. Submit the actual multi-user Syncflow use case and
   accurate screencast; do not describe this as a private/internal upload utility.

## Scheduling and reliability

The existing secret-protected cron remains daily at 08:00 UTC / 09:00 Lagos,
with Vercel Hobby's timing limits. One action is processed per run: a due post,
a TikTok status check, or a bounded Meta comment check/reply. This is not precise
or continuous scheduling. More frequent checks need a compatible existing
scheduler/hosting plan. No paid service is enabled by this code.

Creators authorise the exact queued payload. TikTok creator settings, scopes,
media prefix and duration limits are checked again on delivery. Changed options
produce needs_review instead of silently changing privacy/consent. Queue authors
must still have a live manager role in the active workspace. Queued posts can be
cancelled before claim. Disconnecting TikTok clears stored credentials and cancels
its queued posts. Local disconnect does not revoke other apps/account access.

Request IDs deduplicate publish/reply attempts and reject changed payloads using
an old ID. Provider calls with uncertain results are not automatically repeated.
Use history and the platform itself before creating a new request. Meta routes
cannot accept TikTok IDs or send TikTok credentials to Meta. Manual worker checks
can only clean up the selected account's rows. Cron has a separate server secret.

## Live acceptance — all pending

- [ ] Production backend applies social.0014 and health returns the deployed SHA.
- [ ] Facebook OAuth returns real Page identity and actual granted scopes.
- [ ] Page publish/comment workflow works with real platform receipts.
- [ ] Messenger lists owned conversations and sends one reviewed reply in-window.
- [ ] Missing permission, closed window and duplicate inbox send fail clearly.
- [ ] TikTok callback binds the correct user/brand and rejects replayed state.
- [ ] Token refresh persists a rotated refresh token even if a later status request fails.
- [ ] Video preview/options/consent are required and unaudited posts stay private.
- [ ] TikTok status transitions processing to published/failed without duplicate posts.
- [ ] Queued posts deliver only on authorised worker checks and can be cancelled.
- [ ] Another workspace's account/post/conversation cannot be accessed by ID.
- [ ] Meta endpoints reject TikTok IDs without calling Meta with TikTok tokens.
- [ ] Changing an old publish request payload is rejected; new request is explicit.

Validation so far: static Python/TSX syntax parsing, source review including an
independent reviewer, and git diff --check. No local app tests/builds, per owner.
Actual social sends, token refresh, migrations and approvals remain unverified.

Official references checked November 5, 2026:
- https://developers.tiktok.com/docs/en/content-sharing-guidelines
- https://developers.tiktok.com/docs/en/content-posting-api-reference-direct-post
- https://developers.tiktok.com/docs/en/content-posting-api-reference-query-creator-info
- https://developers.tiktok.com/docs/en/oauth-user-access-token-management
- https://developers.tiktok.com/docs/en/content-posting-api-reference-get-video-status
- https://business-api.tiktok.com/portal/docs/business-messaging-api-get-started/v1.3
- https://www.postman.com/meta/messenger-platform-api/overview
