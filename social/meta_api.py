"""Real Meta operations; no development tokens or simulated receipts."""
import os
import re
import secrets
import uuid
from datetime import timedelta
from urllib.parse import urlencode
import requests
from cryptography.fernet import Fernet, InvalidToken
from django.core import signing
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import APIException, ValidationError, PermissionDenied
from rest_framework import permissions
from .models import Brand, MetaSession, MetaConnection, MetaPublication
from workspaces.permissions import get_user_workspace_role

class MetaUnavailable(APIException):
    status_code = 503
    default_detail = 'Meta could not complete this request. Check app permissions or reconnect the account.'

def configuration():
    app = os.getenv('FACEBOOK_APP_ID') or os.getenv('FACEBOOK_CLIENT_ID')
    secret = os.getenv('FACEBOOK_APP_SECRET') or os.getenv('FACEBOOK_CLIENT_SECRET')
    version = os.getenv('META_GRAPH_VERSION', '')
    redirect = os.getenv('META_REDIRECT_URI', '')
    key = os.getenv('SOCIAL_TOKEN_ENCRYPTION_KEY', '')
    if not app or not secret or not re.fullmatch(r'v\d+\.\d+', version) or not redirect.startswith('https://'):
        raise MetaUnavailable('Set FACEBOOK_APP_ID, FACEBOOK_APP_SECRET, META_GRAPH_VERSION and META_REDIRECT_URI in the backend.')
    try:
        Fernet(key.encode())
    except (ValueError, TypeError):
        raise MetaUnavailable('Set SOCIAL_TOKEN_ENCRYPTION_KEY to a valid Fernet key in the backend.') from None
    return app, secret, version, redirect, key

def graph(method, path, token='', **params):
    _, _, version, _, _ = configuration()
    if not re.fullmatch(r'[A-Za-z0-9_/-]+', path):
        raise ValidationError('Invalid Meta resource.')
    headers = {'Authorization': 'Bearer ' + token} if token else {}
    try:
        response = requests.request(method, f'https://graph.facebook.com/{version}/{path}', headers=headers,
            params=params if method == 'GET' else None, data=params if method != 'GET' else None, timeout=(5, 35))
        data = response.json()
        if response.status_code >= 400 or 'error' in data:
            raise MetaUnavailable()
        return data
    except (requests.RequestException, ValueError):
        raise MetaUnavailable() from None

def brand_for(request, brand_id):
    brand = get_object_or_404(Brand, id=brand_id, is_active=True)
    if get_user_workspace_role(request.user, brand.workspace) not in ('OWNER', 'ADMIN', 'MANAGER'):
        raise PermissionDenied('Only brand managers can manage social accounts.')
    return brand

def public_connection(c):
    return {'id': c.id, 'platform': c.platform, 'name': c.name, 'remote_id': c.remote_id, 'active': c.active}

def access_token(c):
    try:
        return Fernet(configuration()[4].encode()).decrypt(c.encrypted_token.encode()).decode()
    except InvalidToken:
        raise MetaUnavailable('The saved token cannot be decrypted. Restore the encryption key or reconnect this account.') from None

class MetaAccounts(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, brand_id):
        brand = brand_for(request, brand_id)
        return Response([public_connection(c) for c in MetaConnection.objects.filter(brand=brand, active=True)])
    def post(self, request, brand_id):
        brand = brand_for(request, brand_id)
        app, _, version, redirect, key = configuration()
        nonce = secrets.token_hex(32)
        MetaSession.objects.create(nonce=nonce, user=request.user, brand=brand, expires_at=timezone.now() + timedelta(minutes=15))
        state = signing.dumps({'nonce': nonce, 'user': request.user.id}, key=key, salt='meta-connect')
        scopes = 'pages_show_list,pages_read_engagement,pages_read_user_content,pages_manage_posts,pages_manage_engagement,instagram_basic,instagram_content_publish,instagram_manage_comments'
        return Response({'url': f'https://www.facebook.com/{version}/dialog/oauth?' + urlencode({'client_id': app, 'redirect_uri': redirect, 'state': state, 'scope': scopes, 'response_type': 'code'})})

class MetaCallback(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        app, secret, _, redirect, key = configuration()
        code = request.data.get('code')
        if not isinstance(code, str) or not code or len(code) > 4096:
            raise ValidationError('Authorization code is missing.')
        try:
            state = signing.loads(request.data.get('state', ''), key=key, salt='meta-connect', max_age=900)
        except (signing.BadSignature, TypeError):
            raise ValidationError('Connection expired or invalid. Start again.') from None
        with transaction.atomic():
            session = get_object_or_404(MetaSession.objects.select_for_update(), nonce=state.get('nonce'), user=request.user, used=False, expires_at__gt=timezone.now())
            brand = brand_for(request, session.brand_id)
            session.used = True
            session.save(update_fields=['used'])
        token = graph('GET', 'oauth/access_token', client_id=app, client_secret=secret, redirect_uri=redirect, code=code).get('access_token')
        if not token:
            raise MetaUnavailable()
        token = graph('GET', 'oauth/access_token', grant_type='fb_exchange_token', client_id=app, client_secret=secret, fb_exchange_token=token).get('access_token')
        if not token: raise MetaUnavailable()
        # Enumerate authorised Pages, retaining Page tokens rather than user tokens.
        pages = []
        after = None
        for _ in range(5):
            params = {'fields': 'id,name,access_token,instagram_business_account{id,username}', 'limit': 100}
            if after: params['after'] = after
            result = graph('GET', 'me/accounts', token, **params)
            pages.extend(result.get('data', []))
            after = result.get('paging', {}).get('cursors', {}).get('after') if result.get('paging', {}).get('next') else None
            if not after: break
        saved = []
        with transaction.atomic():
            for page in pages:
                if not page.get('access_token') or not page.get('id'): continue
                targets = [('facebook', page['id'], page.get('name', 'Facebook Page'))]
                ig = page.get('instagram_business_account') or {}
                if ig.get('id'): targets.append(('instagram', ig['id'], ig.get('username', 'Instagram')))
                for platform, remote_id, name in targets:
                    c, _ = MetaConnection.objects.update_or_create(brand=brand, platform=platform, remote_id=str(remote_id), defaults={'name': name[:255], 'active': True, 'encrypted_token': Fernet(key.encode()).encrypt(page['access_token'].encode()).decode()})
                    saved.append(public_connection(c))
        if not saved: raise ValidationError('No authorised Facebook Pages or linked Instagram professional accounts were found.')
        return Response({'accounts': saved, 'brand_id': brand.id})

class MetaAccount(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def delete(self, request, account_id):
        c = get_object_or_404(MetaConnection, id=account_id)
        brand_for(request, c.brand_id)
        c.active = False
        c.encrypted_token = ''
        c.save()
        return Response(status=204)

class MetaPosts(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, account_id):
        c = get_object_or_404(MetaConnection, id=account_id, active=True)
        brand_for(request, c.brand_id)
        return Response(list(MetaPublication.objects.filter(connection=c).order_by('-created_at').values('id', 'caption', 'status', 'remote_id', 'created_at')[:100]))
    def post(self, request, account_id):
        c = get_object_or_404(MetaConnection, id=account_id, active=True)
        brand_for(request, c.brand_id)
        caption = request.data.get('caption', '')
        image = request.data.get('image_url', '')
        if request.data.get('confirm') is not True: raise ValidationError('Confirm that this post should be published now.')
        if not isinstance(caption, str) or not caption.strip() or len(caption) > 2200: raise ValidationError('Enter a caption of 1–2,200 characters.')
        if image and (not isinstance(image, str) or len(image) > 2000 or not image.startswith('https://')): raise ValidationError('Use a public HTTPS image URL.')
        if c.platform == 'instagram' and not image: raise ValidationError('Instagram requires a public image URL for this post type.')
        try: request_id = uuid.UUID(str(request.data.get('request_id')))
        except ValueError: raise ValidationError('A valid publication request ID is required.') from None
        token = access_token(c)
        with transaction.atomic():
            # Serialise duplicate requests for an account. Never retry an uncertain send.
            MetaConnection.objects.select_for_update().get(id=c.id)
            post, created = MetaPublication.objects.get_or_create(request_id=request_id, defaults={'connection': c, 'caption': caption, 'image_url': image})
            if not created:
                if post.connection_id != c.id: raise ValidationError('Publication request ID already used.')
                return Response({'id': post.id, 'status': post.status, 'remote_id': post.remote_id})
        try:
            if c.platform == 'facebook':
                result = graph('POST', c.remote_id + ('/photos' if image else '/feed'), token, **({'url': image, 'caption': caption} if image else {'message': caption}))
                remote = result.get('post_id') or result.get('id')
            else:
                container = graph('POST', c.remote_id + '/media', token, image_url=image, caption=caption)
                if not container.get('id'): raise MetaUnavailable()
                result = graph('POST', c.remote_id + '/media_publish', token, creation_id=container['id'])
                remote = result.get('id')
            if not remote: raise MetaUnavailable()
            post.remote_id = str(remote)
            post.status = 'published'
            post.save()
        except MetaUnavailable:
            post.status = 'uncertain'
            post.save(update_fields=['status'])
            raise MetaUnavailable('Publishing was not confirmed. Check the social account before attempting another post to avoid duplicates.') from None
        return Response({'id': post.id, 'status': post.status, 'remote_id': post.remote_id}, status=201)

class MetaComments(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, post_id):
        p = get_object_or_404(MetaPublication, id=post_id, status='published', connection__active=True)
        brand_for(request, p.connection.brand_id)
        fields = 'id,message,created_time' if p.connection.platform == 'facebook' else 'id,text,timestamp'
        data = graph('GET', p.remote_id + '/comments', access_token(p.connection), fields=fields, limit=50)
        return Response([{'id': x['id'], 'text': x.get('message', x.get('text', ''))} for x in data.get('data', [])])
    def post(self, request, post_id):
        p = get_object_or_404(MetaPublication, id=post_id, status='published', connection__active=True)
        brand_for(request, p.connection.brand_id)
        text = request.data.get('text', '')
        if request.data.get('confirm') is not True or not isinstance(text, str) or not text.strip() or len(text) > 2000:
            raise ValidationError('Review and confirm a reply of 1–2,000 characters.')
        comment = str(request.data.get('comment_id', ''))
        token = access_token(p.connection)
        # Accept replies only to comments retrieved from this app's owned post.
        comments = graph('GET', p.remote_id + '/comments', token, fields='id', limit=50).get('data', [])
        if comment not in [str(x['id']) for x in comments]: raise PermissionDenied('Comment does not belong to this post or is outside the current page.')
        edge = '/comments' if p.connection.platform == 'facebook' else '/replies'
        result = graph('POST', comment + edge, token, message=text)
        return Response({'id': result.get('id')}, status=201)
