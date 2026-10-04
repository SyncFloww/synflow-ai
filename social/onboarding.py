from rest_framework import serializers
from .models import BrandProfile, BrandVoice

QUESTIONS = [
    {'key': 'description', 'title': 'Tell me what your brand does.', 'hint': 'What do you offer, and what problem do you help people solve?', 'required': True},
    {'key': 'products_services', 'title': 'What products or services should we talk about?', 'hint': 'List your main offers, one per line. Include only facts you want used in content.', 'required': True},
    {'key': 'target_audience', 'title': 'Who would you most like to reach?', 'hint': 'Describe their needs, location, interests, or the problem they are trying to solve.', 'required': True},
    {'key': 'unique_selling_points', 'title': 'Why should someone choose your brand?', 'hint': 'What makes your approach useful or different? One point per line.', 'required': False},
    {'key': 'tone', 'title': 'How should your brand sound?', 'hint': 'For example: warm and practical, playful and bold, or clear and professional.', 'required': True},
    {'key': 'goal', 'title': 'What should Syncflow help you achieve first?', 'hint': 'Choose a focus such as sales, leads, engagement, awareness, or followers. Explain what success would look like.', 'required': True},
    {'key': 'do_not_say', 'title': 'What should we avoid saying?', 'hint': 'Add restricted claims, sensitive topics, or promises you cannot support. One per line. You can leave this blank.', 'required': False},
]


class InterviewUpdateSerializer(serializers.Serializer):
    answers = serializers.DictField(child=serializers.CharField(max_length=2000, allow_blank=True), required=False)
    complete = serializers.BooleanField(required=False, default=False)

    def validate_answers(self, answers):
        if set(answers) - {q['key'] for q in QUESTIONS}:
            raise serializers.ValidationError('Unknown interview question.')
        for key in ('tone', 'goal'):
            if len(answers.get(key, '')) > 255:
                raise serializers.ValidationError(f'{key} must be at most 255 characters.')
        return answers


def interview_state(brand, profile):
    answers = dict(profile.onboarding_answers)
    # Existing brand details prefill the interview; they are not overwritten on reads.
    for key in ('description', 'target_audience'):
        answers.setdefault(key, getattr(brand, key, '') or getattr(profile, key, ''))
    answers.setdefault('tone', profile.tone or profile.brand_voice or brand.voice)
    for key in ('products_services', 'unique_selling_points', 'do_not_say'):
        answers.setdefault(key, '\n'.join(str(item) for item in getattr(profile, key)))
    voice = getattr(brand, 'brand_voice', None)
    answers.setdefault('goal', voice.goal if voice else '')
    missing = [q['key'] for q in QUESTIONS if q['required'] and not answers.get(q['key'], '').strip()]
    return {'answers': answers, 'questions': QUESTIONS, 'missing': missing, 'completed': profile.onboarding_completed}


def save_interview(brand, payload):
    profile, _ = BrandProfile.objects.get_or_create(brand=brand)
    profile = BrandProfile.objects.select_for_update().get(pk=profile.pk)
    answers = interview_state(brand, profile)['answers']
    answers.update(payload.get('answers', {}))
    if payload.get('complete') and any(q['required'] and not answers.get(q['key'], '').strip() for q in QUESTIONS):
        raise serializers.ValidationError({'complete': 'Answer all required questions before finishing.'})
    profile.onboarding_answers = answers
    profile.onboarding_completed = payload.get('complete', False)
    profile.target_audience = answers.get('target_audience', '')
    profile.tone = profile.brand_voice = answers.get('tone', '')
    for key in ('products_services', 'unique_selling_points', 'do_not_say'):
        setattr(profile, key, [line.strip() for line in answers.get(key, '').splitlines() if line.strip()])
    profile.save()
    brand.description = answers.get('description', '')
    brand.target_audience = answers.get('target_audience', '')[:255]
    brand.voice = answers.get('tone', '')[:255]
    brand.save(update_fields=['description', 'target_audience', 'voice', 'updated_at'])
    voice, _ = BrandVoice.objects.get_or_create(brand=brand, defaults={'tone': brand.voice})
    voice.tone = brand.voice
    voice.goal = answers.get('goal', '')[:255]
    voice.save(update_fields=['tone', 'goal'])
    return interview_state(brand, profile)
