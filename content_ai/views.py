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

        ai_model = AIModel.objects.filter(is_active=True).first()

        generation = ContentGeneration.objects.create(
            workspace=workspace,
            user=request.user,
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
