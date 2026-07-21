import time
try:
    from litellm import completion
except ImportError:
    # Fallback for when litellm is not installed locally
    def completion(*args, **kwargs):
        raise ImportError("litellm is not installed.")
from .models import ContentGeneration, GenerationHistory

class AIService:
    @staticmethod
    def generate_text(generation: ContentGeneration, system_prompt: str, user_prompt: str) -> str:
        """
        Uses LiteLLM to generate text based on the configured model.
        Logs the generation history.
        """
        provider_string = generation.ai_model.provider_string if generation.ai_model else "openai/gpt-4o-mini"
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        start_time = time.time()
        
        try:
            # For Phase 1 we use basic chat completions
            response = completion(
                model=provider_string,
                messages=messages
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            generated_text = response.choices[0].message.content
            generation.generated_text = generated_text
            generation.save()
            
            GenerationHistory.objects.create(
                generation=generation,
                full_prompt=f"System: {system_prompt}\nUser: {user_prompt}",
                provider_response=response.model_dump(),
                tokens_used=response.usage.total_tokens if response.usage else 0,
                latency_ms=latency_ms
            )
            
            return generated_text
            
        except Exception as e:
            # Here we might log to the ErrorLog later
            latency_ms = int((time.time() - start_time) * 1000)
            GenerationHistory.objects.create(
                generation=generation,
                full_prompt=f"System: {system_prompt}\nUser: {user_prompt}",
                provider_response={"error": str(e)},
                tokens_used=0,
                latency_ms=latency_ms
            )
            raise e
