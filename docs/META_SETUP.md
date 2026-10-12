# Meta social connection and publishing setup

Use the existing backend and frontend Vercel projects. No new Vercel project.
This increment implements real Facebook Page and linked Instagram professional
account connections, confirmed Facebook text/image and Instagram single-image
publishing, receipts/history, comment refresh and reviewed public replies.
AI reply drafts use the existing brand assistant, quota and Gemini configuration.
It does not implement continuous automatic replies, DMs, videos or scheduling.

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
Reply drafts are editable and only sent after explicit confirmation.

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
unverified. Continuous autonomous publishing/comment replies need the next
scheduler/webhook increment and an explicit per-brand automation policy.

Official reference:
https://www.postman.com/meta/instagram/documentation/6yqw8pt/instagram-api
