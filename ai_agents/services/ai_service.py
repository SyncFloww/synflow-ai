import time
import logging
from typing import Optional, Dict, Any, Tuple
from decimal import Decimal

from django.contrib.auth.models import User
from workspaces.models import Workspace
from social.models import Brand

from ..providers import LLMProviderRegistry, GenerationResult
from ..models import AIUsageRecord, GeneratedContent
from .prompt_manager import PromptManager
from .model_router import ModelRouter
from .output_parser import OutputParser

logger = logging.getLogger(__name__)

class AIService:
    def __init__(
        self,
        prompt_manager: Optional[PromptManager] = None,
        model_router: Optional[ModelRouter] = None,
        output_parser: Optional[OutputParser] = None
    ):
        self.prompt_manager = prompt_manager or PromptManager()
        self.model_router = model_router or ModelRouter()
        self.output_parser = output_parser or OutputParser()

    def generate_content(
        self,
        prompt: str,
        user: User,
        workspace: Optional[Workspace] = None,
        brand: Optional[Brand] = None,
        task_type: str = "content",
        platform: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        json_schema: Optional[Dict[str, Any]] = None,
        inputs: Optional[Dict[str, Any]] = None,
        extra_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[GenerationResult, Optional[AIUsageRecord]]:
        """
        Main AIService orchestration endpoint:
        1. Resolves provider and model via ModelRouter.
        2. Builds system and user prompts via PromptManager.
        3. Invokes Provider via LLMProviderRegistry.
        4. Parses structured output via OutputParser.
        5. Logs usage via AIUsageRecord.
        """
        start_time = time.time()
        
        # 1. Resolve Provider & Model
        target_provider_name, target_model_name = self.model_router.resolve_target(
            task_type=task_type,
            provider=provider,
            model=model
        )

        # 2. Build Prompts
        system_prompt = self.prompt_manager.build_system_prompt(
            task_type=task_type,
            platform=platform,
            brand=brand,
            extra_context=extra_context
        )
        user_prompt = self.prompt_manager.build_user_prompt(
            prompt=prompt,
            task_type=task_type,
            platform=platform,
            inputs=inputs
        )

        # 3. Retrieve Provider & Execute Generation
        llm_provider = LLMProviderRegistry.get(target_provider_name)
        result: GenerationResult = llm_provider.generate_text(
            prompt=user_prompt,
            system_prompt=system_prompt,
            model=target_model_name,
            temperature=temperature,
            json_schema=json_schema
        )

        # 4. Clean / Parse Output
        if json_schema and not result.structured_data:
            result.structured_data = self.output_parser.parse_json(result.text)

        elapsed_ms = int((time.time() - start_time) * 1000)

        # 5. Log Usage Record if Workspace is provided
        usage_record = None
        if workspace:
            try:
                usage_record = AIUsageRecord.objects.create(
                    workspace=workspace,
                    user=user,
                    provider=target_provider_name,
                    model=target_model_name,
                    generation_type=task_type,
                    input_tokens=result.prompt_tokens,
                    output_tokens=result.completion_tokens,
                    seconds_used=elapsed_ms / 1000.0,
                    estimated_cost=Decimal(str(round(result.estimated_cost, 6)))
                )
            except Exception as e:
                logger.error(f"Failed to record AIUsageRecord: {e}")

        return result, usage_record
