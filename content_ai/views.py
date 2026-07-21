from rest_framework import status, views, permissions
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from workspaces.models import Workspace
from .models import ContentGeneration, AIModel, PromptTemplate
from .services import AIService

class GenerateContentView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, workspace_id):
        workspace = get_object_or_404(Workspace, id=workspace_id)
        
        gen_type = request.data.get("type", "caption") # caption, ideas, rewrite, hashtags, variations
        topic = request.data.get("topic", "")
        tone = request.data.get("tone", "professional")
        platform = request.data.get("platform", "general")
        extra_instructions = request.data.get("extra_instructions", "")
        brand_id = request.data.get("brand_id")
        
        brand = None
        brand_context = ""
        if brand_id:
            from brands.models import Brand
            brand = get_object_or_404(Brand, id=brand_id, workspace=workspace)
            brand_context = f"\nBrand Name: {brand.name}\nTarget Audience: {brand.target_audience}\nMission: {brand.mission}\n"
            if hasattr(brand, 'voice'):
                brand_context += f"Brand Tone: {brand.voice.tone}\nDo list: {', '.join(brand.voice.do_list)}\nDon't list: {', '.join(brand.voice.dont_list)}\n"
        
        # In a real system, we'd fetch the specific PromptTemplate for this gen_type
        # For MVP, we'll construct it on the fly if not found
        template = PromptTemplate.objects.filter(workspace=workspace, name=gen_type).first()
        
        if template:
            system_prompt = template.system_prompt
            user_prompt = template.user_prompt_template.format(
                topic=topic, tone=tone, platform=platform
            )
        else:
            system_prompt = f"You are an expert social media manager generating a {gen_type}."
            user_prompt = f"Topic: {topic}\nTone: {tone}\nPlatform: {platform}\nExtra: {extra_instructions}"

        if brand_context:
            system_prompt += f"\n\nAdhere to the following brand guidelines:\n{brand_context}"

        ai_model = AIModel.objects.filter(is_active=True).first()

        generation = ContentGeneration.objects.create(
            workspace=workspace,
            user=request.user,
            brand=brand,
            ai_model=ai_model,
            template_used=template,
            platform=platform,
            topic=topic,
            tone=tone,
            extra_instructions=extra_instructions
        )

        try:
            generated_text = AIService.generate_text(generation, system_prompt, user_prompt)
            return Response({
                "id": generation.id,
                "generated_text": generated_text
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": "AI Provider error"}, status=status.HTTP_502_BAD_GATEWAY)


class GenerationHistoryAPIView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, workspace_id):
        workspace = get_object_or_404(Workspace, id=workspace_id)
        # Verify permissions
        generations = ContentGeneration.objects.filter(workspace=workspace).order_by('-created_at')
        
        data = []
        for gen in generations:
            hist = gen.history if hasattr(gen, 'history') else None
            data.append({
                "id": gen.id,
                "platform": gen.platform,
                "topic": gen.topic,
                "tone": gen.tone,
                "generated_text": gen.generated_text,
                "created_at": gen.created_at,
                "tokens_used": hist.tokens_used if hist else 0,
                "latency_ms": hist.latency_ms if hist else 0,
            })
            
        return Response(data, status=status.HTTP_200_OK)
