import json
from django.http import StreamingHttpResponse
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
from rest_framework.decorators import action
from ai_agents.models import AIScript, AIScriptVersion
from .models import BrandProfile, BrandVoice, BrandGuideline

class BrandDataActions:
    @action(detail=True, methods=['get'], url_path='export')
    def export_data(self, request, pk=None):
        brand = self.get_object()
        self.require_brand_manager(brand)
        # Export only core brand records. Never include credentials, OAuth tokens,
        # provider raw responses, another workspace, or unrelated user records.
        def records():
            yield {'record_type': 'manifest', 'format_version': 1, 'exported_at': timezone.now(),
                   'brand_id': brand.pk, 'scope': 'brand profile, references, conversations, contacts, ideas, scripts and script versions'}
            yield {'record_type': 'brand', 'data': {'id': brand.pk, 'name': brand.name, 'description': brand.description,
                   'industry': brand.industry, 'voice': brand.voice, 'target_audience': brand.target_audience, 'website': brand.website}}
            sources = [
                ('profile', BrandProfile.objects.filter(brand=brand).values()),
                ('voice', BrandVoice.objects.filter(brand=brand).values()),
                ('guidelines', BrandGuideline.objects.filter(brand=brand).values()),
                ('reference', brand.knowledge_items.values()),
                ('conversation', brand.messages.values('id', 'role', 'content', 'created_at')),
                ('contact', brand.leads.values('id', 'name', 'email', 'source', 'note', 'consent_at', 'created_at')),
                ('idea', brand.ideas.values()),
                ('script', AIScript.objects.filter(brand=brand).values()),
                ('script_version', AIScriptVersion.objects.filter(script__brand=brand).values()),
            ]
            for kind, queryset in sources:
                # Keyset batches avoid server-side cursors on pooled Neon connections.
                last_id = 0
                while True:
                    batch = list(queryset.filter(id__gt=last_id).order_by('id')[:100])
                    if not batch:
                        break
                    for row in batch:
                        yield {'record_type': kind, 'data': row}
                    last_id = batch[-1]['id']
        def stream():
            for record in records():
                yield json.dumps(record, cls=DjangoJSONEncoder, ensure_ascii=False) + '\n'
        response = StreamingHttpResponse(stream(), content_type='application/x-ndjson; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="syncflow-brand-{brand.pk}.ndjson"'
        response['Cache-Control'] = 'no-store'
        response['X-Content-Type-Options'] = 'nosniff'
        return response
