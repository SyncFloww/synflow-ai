"""TikTok creator publishing. Only official endpoints; no mock receipts."""
import os
import math
import secrets
import uuid
from datetime import timedelta
from urllib.parse import urlencode, urlsplit
import requests
from cryptography.fernet import Fernet, InvalidToken
from django.core import signing
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import permissions, serializers
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import MetaConnection, MetaPublication, MetaSession
from .meta_api import brand_for, public_connection

class TikTokUnavailable(APIException):
    status_code = 503
    default_detail = 'TikTok could not complete this request. Check access or reconnect your account.'


def cipher():
    try: return Fernet(os.getenv('SOCIAL_TOKEN_ENCRYPTION_KEY', '').encode())
    except (ValueError, TypeError): raise TikTokUnavailable('Set a valid SOCIAL_TOKEN_ENCRYPTION_KEY in the backend.') from None


def configuration():
    key = os.getenv('TIKTOK_CLIENT_KEY', '').strip()
    secret = os.getenv('TIKTOK_CLIENT_SECRET', '').strip()
    redirect = os.getenv('TIKTOK_REDIRECT_URI', '').strip()
    parts = urlsplit(redirect)
    if not key or not secret or parts.scheme != 'https' or not parts.hostname or parts.query or parts.fragment:
        raise TikTokUnavailable('Set TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET and the exact HTTPS TIKTOK_REDIRECT_URI.')
    cipher()
    return key, secret, redirect


def public_approved():
    return os.getenv('TIKTOK_PUBLIC_POSTING_APPROVED', 'false').lower() == 'true'


def call(path, token=None, payload=None, form=False, params=None, method='POST'):
    headers = {'Authorization': f'Bearer {token}'} if token else {}
    try:
        response = requests.request(method, 'https://open.tiktokapis.com' + path, headers=headers,
            json=payload if not form else None, data=payload if form else None, params=params, timeout=(5, 35))
        data = response.json()
    except (requests.RequestException, ValueError):
        raise TikTokUnavailable('TikTok did not confirm the request. Check its status before attempting another publish.') from None
    error = data.get('error')
    code = error.get('code') if isinstance(error, dict) else error
    if response.status_code >= 400 or code not in (None, 'ok'):
        messages = {
            'unaudited_client_can_only_post_to_private_accounts': 'TikTok has not audited this app. Use a private test account and Only me visibility.',
            'url_ownership_unverified': 'Verify the media URL domain or prefix in your TikTok developer app.',
            'scope_not_authorized': 'TikTok has not granted this account the required scope. Approve the product and reconnect.',
            'access_token_invalid': 'TikTok access expired or was revoked. Reconnect the account.',
            'privacy_level_option_mismatch': 'TikTok privacy settings changed. Reload creator options and review the post again.',
            'spam_risk_too_many_posts': 'TikTok posting quota has been reached. Try later.',
            'spam_risk_user_banned_from_posting': 'TikTok has restricted publishing for this account.',
            'invalid_client': 'TikTok rejected the app credentials. Check the client key and secret.',
            'invalid_grant': 'TikTok authorization expired. Reconnect the account.',
        }
        raise TikTokUnavailable(messages.get(code, TikTokUnavailable.default_detail))
    return data if form else data.get('data', {})


def account_for(request, account_id):
    c = get_object_or_404(MetaConnection, id=account_id, platform='tiktok', active=True)
    brand_for(request, c.brand_id)
    return c


def store_tokens(c, data):
    if not data.get('access_token') or not data.get('refresh_token') or str(data.get('open_id')) != c.remote_id:
        raise TikTokUnavailable('TikTok returned incomplete or mismatched credentials. Reconnect.')
    try:
        access_age = max(1, min(int(data['expires_in']), 60 * 60 * 24 * 365))
        refresh_age = max(1, min(int(data['refresh_expires_in']), 60 * 60 * 24 * 365))
    except (KeyError, ValueError, TypeError):
        raise TikTokUnavailable('TikTok did not return valid token expiry information.') from None
    c.encrypted_token = cipher().encrypt(data['access_token'].encode()).decode()
    c.encrypted_refresh_token = cipher().encrypt(data['refresh_token'].encode()).decode()
    c.token_expires_at = timezone.now() + timedelta(seconds=access_age)
    c.refresh_expires_at = timezone.now() + timedelta(seconds=refresh_age)
    c.scopes = str(data['scope']).split(',') if data.get('scope') else c.scopes
    c.save()


def valid_token(connection):
    # Token rotation is serialised to prevent reuse of a replaced refresh token.
    with transaction.atomic():
        c = MetaConnection.objects.select_for_update().get(id=connection.id, platform='tiktok', active=True)
        try:
            if c.token_expires_at and c.token_expires_at > timezone.now() + timedelta(seconds=90):
                return cipher().decrypt(c.encrypted_token.encode()).decode()
            if not c.refresh_expires_at or c.refresh_expires_at <= timezone.now():
                raise TikTokUnavailable('TikTok authorization expired. Reconnect the account.')
            refresh = cipher().decrypt(c.encrypted_refresh_token.encode()).decode()
            key, secret, _ = configuration()
            data = call('/v2/oauth/token/', form=True, payload={'client_key': key, 'client_secret': secret, 'grant_type': 'refresh_token', 'refresh_token': refresh})
            store_tokens(c, data)
            return data['access_token']
        except InvalidToken:
            raise TikTokUnavailable('Saved TikTok credentials cannot be decrypted. Restore the encryption key or reconnect.') from None


def creator_info(c):
    token = valid_token(c)
    if 'video.publish' not in MetaConnection.objects.get(id=c.id).scopes:
        raise TikTokUnavailable('video.publish was not granted. Enable Direct Post, obtain scope approval and reconnect.')
    return call('/v2/post/publish/creator_info/query/', token, {})


def validate_url(value):
    prefix = os.getenv('TIKTOK_MEDIA_URL_PREFIX', '').strip()
    media, allowed = urlsplit(value), urlsplit(prefix)
    if allowed.scheme != 'https' or not allowed.hostname:
        raise ValidationError('Set TIKTOK_MEDIA_URL_PREFIX to a URL prefix verified in your TikTok app.')
    path = allowed.path.rstrip('/') + '/'
    if media.scheme != 'https' or media.netloc != allowed.netloc or media.username or media.password or media.fragment or not media.path.startswith(path):
        raise ValidationError('Choose a video URL under the configured, TikTok-verified HTTPS media prefix.')
    # Match the exact published prefix as well, preventing path traversal tricks.
    if any(part in ('.', '..') for part in media.path.split('/')) or '%' in media.path:
        raise ValidationError('Use a media URL with a plain, canonical path.')
    return value

class PostInput(serializers.Serializer):
    caption = serializers.CharField(max_length=2200, allow_blank=True)
    video_url = serializers.URLField(max_length=2000)
    duration_seconds = serializers.FloatField(min_value=0.1, max_value=36000)
    privacy_level = serializers.ChoiceField(choices=['SELF_ONLY', 'PUBLIC_TO_EVERYONE', 'MUTUAL_FOLLOW_FRIENDS', 'FOLLOWER_OF_CREATOR'])
    allow_comment = serializers.BooleanField(default=False)
    allow_duet = serializers.BooleanField(default=False)
    allow_stitch = serializers.BooleanField(default=False)
    commercial = serializers.BooleanField(default=False)
    brand_organic_toggle = serializers.BooleanField(default=False)
    brand_content_toggle = serializers.BooleanField(default=False)
    is_aigc = serializers.BooleanField(default=False)
    confirm = serializers.BooleanField()
    music_consent = serializers.BooleanField()
    request_id = serializers.UUIDField()
    scheduled_at = serializers.DateTimeField(required=False, allow_null=True)


def check_options(c, values):
    validate_url(values['video_url'])
    if not math.isfinite(values['duration_seconds']): raise ValidationError('Video duration must be finite.')
    if not values.get('confirm') or not values.get('music_consent'): raise ValidationError('Review the preview, post options and music usage confirmation before publishing.')
    if len(values['caption'].encode('utf-16-le')) // 2 > 2200: raise ValidationError('Caption exceeds TikTok’s 2,200 UTF-16 character limit.')
    if values['brand_content_toggle'] and values['privacy_level'] not in ('PUBLIC_TO_EVERYONE', 'MUTUAL_FOLLOW_FRIENDS'):
        raise ValidationError('Paid partnerships require public or friends visibility.')
    if values['commercial'] != bool(values['brand_organic_toggle'] or values['brand_content_toggle']):
        raise ValidationError('Choose the applicable commercial disclosure, or turn disclosure off.')
    if not public_approved() and values['privacy_level'] != 'SELF_ONLY': raise ValidationError('Public posting is locked until TikTok audits this app. Select Only me.')
    creator = creator_info(c)
    if values['privacy_level'] not in creator.get('privacy_level_options', []): raise ValidationError('Privacy setting is no longer available. Reload creator options.')
    if values['duration_seconds'] > creator.get('max_video_post_duration_sec', 0): raise ValidationError('Video exceeds this creator’s current duration limit.')
    for feature in ('comment', 'duet', 'stitch'):
        if values.get('allow_' + feature) and creator.get(feature + '_disabled', True): raise ValidationError('TikTok disabled this interaction. Reload creator options.')
    return creator

class TikTokAccounts(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, brand_id):
        brand = brand_for(request, brand_id)
        return Response([public_connection(c) for c in MetaConnection.objects.filter(brand=brand, platform='tiktok', active=True)])
    def post(self, request, brand_id):
        brand = brand_for(request, brand_id)
        key, _, redirect = configuration()
        nonce = secrets.token_hex(32)
        MetaSession.objects.create(nonce=nonce, user=request.user, brand=brand, expires_at=timezone.now() + timedelta(minutes=15))
        state = signing.dumps({'nonce': nonce}, key=os.environ['SOCIAL_TOKEN_ENCRYPTION_KEY'], salt='tiktok-connect')
        return Response({'url': 'https://www.tiktok.com/v2/auth/authorize/?' + urlencode({'client_key': key, 'scope': 'user.info.basic,video.publish', 'response_type': 'code', 'redirect_uri': redirect, 'state': state})})

class TikTokCallback(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        key, secret, redirect = configuration()
        try: state = signing.loads(request.data.get('state', ''), key=os.environ['SOCIAL_TOKEN_ENCRYPTION_KEY'], salt='tiktok-connect', max_age=900)
        except (signing.BadSignature, TypeError): raise ValidationError('TikTok connection expired or invalid. Start again.') from None
        code = request.data.get('code')
        if not isinstance(code, str) or not code or len(code) > 4096: raise ValidationError('TikTok authorization code is missing.')
        with transaction.atomic():
            session = get_object_or_404(MetaSession.objects.select_for_update(), nonce=state.get('nonce'), user=request.user, used=False, expires_at__gt=timezone.now())
            brand = brand_for(request, session.brand_id)
            session.used = True
            session.save(update_fields=['used'])
        data = call('/v2/oauth/token/', form=True, payload={'client_key': key, 'client_secret': secret, 'grant_type': 'authorization_code', 'code': code, 'redirect_uri': redirect})
        if not data.get('open_id'): raise TikTokUnavailable('TikTok returned no account identity.')
        profile = call('/v2/user/info/', data.get('access_token'), method='GET', params={'fields': 'open_id,display_name'})
        user = profile.get('user', {})
        if user.get('open_id') != data['open_id']: raise TikTokUnavailable('TikTok account identity did not match the authorization.')
        with transaction.atomic():
            c, _ = MetaConnection.objects.get_or_create(brand=brand, platform='tiktok', remote_id=data['open_id'], defaults={'name': user.get('display_name', 'TikTok')[:255], 'encrypted_token': ''})
            c = MetaConnection.objects.select_for_update().get(id=c.id)
            c.active = True
            c.name = user.get('display_name', 'TikTok')[:255]
            store_tokens(c, data)
        return Response({'account': public_connection(c), 'brand_id': brand.id})

class TikTokCreator(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, account_id):
        c = account_for(request, account_id)
        info = creator_info(c)
        return Response({**info, 'public_posting_approved': public_approved()})

class TikTokDisconnect(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def delete(self, request, account_id):
        c = account_for(request, account_id)
        with transaction.atomic():
            c = MetaConnection.objects.select_for_update().get(id=c.id)
            c.active = False
            c.encrypted_token = ''
            c.encrypted_refresh_token = ''
            c.save()
            MetaPublication.objects.filter(connection=c, status='scheduled').update(status='cancelled')
        return Response(status=204)

class TikTokPosts(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, account_id):
        c = account_for(request, account_id)
        return Response(list(MetaPublication.objects.filter(connection=c).order_by('-created_at').values('id', 'caption', 'status', 'remote_id', 'provider_publish_id', 'scheduled_at')[:100]))
    def post(self, request, account_id):
        c = account_for(request, account_id)
        data = PostInput(data=request.data)
        data.is_valid(raise_exception=True)
        values = data.validated_data
        when = values.get('scheduled_at')
        if when and when <= timezone.now(): raise ValidationError('Choose a future scheduled time.')
        # Check duplicate before any new provider operation; preserve exact approved snapshot.
        previous = MetaPublication.objects.filter(request_id=values['request_id']).first()
        if previous:
            expected = {k: v for k, v in values.items() if k not in ('request_id', 'scheduled_at')}
            if previous.connection_id != c.id or previous.post_options != expected or previous.scheduled_at != when: raise ValidationError('This request ID belongs to another approved payload. Start a new publish request.')
            return Response({'id': previous.id, 'status': previous.status})
        check_options(c, values)
        with transaction.atomic():
            MetaConnection.objects.select_for_update().get(id=c.id, active=True)
            options = {k: v for k, v in values.items() if k not in ('request_id', 'scheduled_at')}
            post, created = MetaPublication.objects.get_or_create(request_id=values['request_id'], defaults={'connection': c, 'caption': values['caption'], 'video_url': values['video_url'], 'post_options': options, 'status': 'scheduled' if when else 'sending', 'scheduled_at': when, 'requested_by': request.user})
            if post.connection_id != c.id or post.post_options != options or post.scheduled_at != when: raise ValidationError('This request ID belongs to another approved payload. Start a new publish request.')
        if created and not when: send_tiktok(post)
        return Response({'id': post.id, 'status': post.status}, status=201 if created else 200)


def send_tiktok(post):
    c = post.connection
    try:
        c.refresh_from_db()
        if not c.active: raise ValidationError('TikTok account is disconnected.')
        check_options(c, post.post_options)
    except APIException:
        post.status = 'needs_review'
        post.save(update_fields=['status'])
        raise
    values = post.post_options
    info = {'title': post.caption, 'privacy_level': values['privacy_level'], 'disable_comment': not values['allow_comment'], 'disable_duet': not values['allow_duet'], 'disable_stitch': not values['allow_stitch'], 'brand_content_toggle': values['brand_content_toggle'], 'brand_organic_toggle': values['brand_organic_toggle'], 'is_aigc': values['is_aigc']}
    try:
        result = call('/v2/post/publish/video/init/', valid_token(c), {'post_info': info, 'source_info': {'source': 'PULL_FROM_URL', 'video_url': post.video_url}})
        if not result.get('publish_id'): raise TikTokUnavailable()
        post.provider_publish_id = result['publish_id']
        post.status = 'processing'
        post.save(update_fields=['provider_publish_id', 'status'])
    except APIException:
        post.status = 'uncertain'
        post.save(update_fields=['status'])
        raise

class TikTokStatus(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, post_id):
        p = get_object_or_404(MetaPublication, id=post_id, connection__platform='tiktok', connection__active=True)
        account_for(request, p.connection_id)
        if not p.provider_publish_id: raise ValidationError('No confirmed TikTok publish ID exists. Check the account before creating another post.')
        return Response(refresh_status(p))


def refresh_status(p):
    token = valid_token(p.connection)
    data = call('/v2/post/publish/status/fetch/', token, {'publish_id': p.provider_publish_id})
    state = data.get('status')
    with transaction.atomic():
        p = MetaPublication.objects.select_for_update().get(id=p.id)
        if state == 'PUBLISH_COMPLETE':
            p.status = 'published'
            ids = data.get('publicaly_available_post_id') or data.get('publicly_available_post_id') or []
            if isinstance(ids, list) and ids: p.remote_id = str(ids[0])
        elif state == 'FAILED' and p.status != 'published': p.status = 'failed'
        p.last_status_checked_at = timezone.now()
        p.save(update_fields=['status', 'remote_id', 'last_status_checked_at'])
    return {'id': p.id, 'status': p.status, 'provider_status': state}

class TikTokWorker(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, account_id):
        c = account_for(request, account_id)
        from .meta_automation import run_worker
        return Response(run_worker(c.id))
