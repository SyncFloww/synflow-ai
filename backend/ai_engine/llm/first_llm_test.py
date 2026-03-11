# backend/ai_engine/llm/first_llm_test.py

import sys
import os

# Ensure backend directory is in python path to handle relative imports if needed later
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

def generate_response(prompt: str):
    model_id = "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"
    print("Loading model...")
    
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    
    # We load safely. If running on a machine without a dedicated GPU
    # we may need to drop `device_map="auto"` or `torch_dtype`. 
    # But we will stick to the requested script.
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch.float16,
        device_map="auto"
    )
    
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    print("Generating response...")
    output = model.generate(
        **inputs,
        max_new_tokens=100,
        temperature=0.7,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id # Prevents HuggingFace warning
    )
    
    response = tokenizer.decode(output[0], skip_special_tokens=True)
    
    return response

if __name__ == "__main__":
    user_input = "Write a short tweet announcing SyncflowAI, an AI automation platform."
    
    ai_response = generate_response(user_input)
    
    print("\n==============================")
    print("AI RESPONSE")
    print("==============================")
    print(ai_response)
