"""Reviewed Facebook Messenger replies to existing inbound conversations."""
import json
import re
import uuid
from datetime import timedelta
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import permissions
from rest_framework.exceptions import ValidationError, APIException
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import MetaConnection, InboxSend
from .meta_api import brand_for, graph, access_token, MetaUnavailable


def connection(request, account_id):
    c = get_object_or_404(MetaConnection, id=account_id, platform='facebook', active=True)
    brand_for(request, c.brand_id)
    if 'pages_messaging' not in c.scopes:
        raise ValidationError('Messenger permission was not granted. Enable Messenger in app setup and reconnect this Page.')
    return c


def conversations(c):
    return graph('GET', c.remote_id + '/conversations', access_token(c), fields='id,participants,updated_time', limit=50).get('data', [])


def owned_messages(c, conversation_id):
    if not isinstance(conversation_id, str) or not re.fullmatch(r'[A-Za-z0-9_:.-]{1,255}', conversation_id):
        raise ValidationError('Choose a valid conversation.')
    if conversation_id not in [str(x['id']) for x in conversations(c)]:
        raise ValidationError('Conversation is not in this Page’s current inbox list. Refresh and select it again.')
    return graph('GET', conversation_id + '/messages', access_token(c), fields='id,message,from,created_time', limit=50).get('data', [])

class FacebookInbox(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, account_id):
        c = connection(request, account_id)
        conversation_id = request.query_params.get('conversation_id')
        if not conversation_id: return Response(conversations(c))
        return Response(owned_messages(c, conversation_id))
    def post(self, request, account_id):
        c = connection(request, account_id)
        thread = request.data.get('conversation_id')
        text = request.data.get('text', '')
        if request.data.get('confirm') is not True or not isinstance(text, str) or not text.strip() or len(text) > 2000:
            raise ValidationError('Review and confirm a reply of 1–2,000 characters.')
        try: request_id = uuid.UUID(str(request.data.get('request_id')))
        except ValueError: raise ValidationError('A valid send request ID is required.') from None
        previous = InboxSend.objects.filter(request_id=request_id).first()
        if previous:
            if previous.connection_id != c.id or previous.conversation_id != thread or previous.text != text: raise ValidationError('Send request ID already used.')
            return Response({'status': previous.status, 'id': previous.remote_id})
        messages = owned_messages(c, thread)
        inbound = []
        for message in messages:
            sender = str((message.get('from') or {}).get('id', ''))
            try: created = parse_datetime(message.get('created_time', ''))
            except ValueError: continue
            if sender and sender != c.remote_id and created and not timezone.is_naive(created): inbound.append((created, sender))
        if not inbound: raise ValidationError('No inbound message was found in this conversation.')
        last_time, recipient = max(inbound)
        if last_time < timezone.now() - timedelta(hours=24): raise ValidationError('The standard Messenger reply window has closed. Wait for a new inbound message.')
        with transaction.atomic():
            MetaConnection.objects.select_for_update().get(id=c.id, active=True)
            send, created = InboxSend.objects.get_or_create(request_id=request_id, defaults={'connection': c, 'conversation_id': thread, 'text': text})
            if send.connection_id != c.id or send.conversation_id != thread or send.text != text: raise ValidationError('Send request ID already used.')
        if not created: return Response({'status': send.status, 'id': send.remote_id})
        try:
            data = graph('POST', c.remote_id + '/messages', access_token(c), recipient=json.dumps({'id': recipient}), message=json.dumps({'text': text}), messaging_type='RESPONSE')
            if not data.get('message_id'): raise MetaUnavailable()
            send.status = 'sent'
            send.remote_id = str(data['message_id'])
            send.save()
        except APIException:
            send.status = 'uncertain'
            send.save(update_fields=['status'])
            raise MetaUnavailable('Messenger send was not confirmed. Check the Page inbox before starting a new reply.') from None
        return Response({'status': send.status, 'id': send.remote_id}, status=201)
