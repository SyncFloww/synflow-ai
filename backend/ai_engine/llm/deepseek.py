import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from langchain_huggingface import HuggingFacePipeline

# Caching the model instance in memory so that Celery workers 
# only load the model once per process, instead of on every task.
_llm_instance = None

def get_deepseek_llm(model_id="deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"):
    """
    Returns a LangChain-compatible LLM instance wrapped around a Hugging Face pipeline.
    Uses the 1.5B Qwen model by default for lightweight local development.
    """
    global _llm_instance
    if _llm_instance is not None:
        return _llm_instance

    print(f"Loading HF Model: {model_id}...")
    
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch.float16,
        device_map="auto" # Automatically uses GPU if available
    )

    # Wrap in a text-generation pipeline
    hf_pipeline = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=256,
        temperature=0.7,
        do_sample=True,
    )

    # Wrap the Hugging Face pipeline into a LangChain LLM object
    _llm_instance = HuggingFacePipeline(pipeline=hf_pipeline)
    
    return _llm_instance
