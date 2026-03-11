from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import warnings
warnings.filterwarnings("ignore")

def test_llm():
    print("Loading TinyLlama...")
    model_id = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    # Load model. We aren't doing 8-bit quantization here to keep it simple, 
    # but `bitsandbytes` is installed if you want to add `load_in_8bit=True` later.
    model = AutoModelForCausalLM.from_pretrained(model_id)
    
    print("Model loaded. Testing generation...")
    pipe = pipeline("text-generation", model=model, tokenizer=tokenizer, max_new_tokens=50)
    
    prompt = "Write a tweet about productivity"
    print(f"\nPrompt: {prompt}")
    print("-" * 40)
    
    result = pipe(prompt)
    print(result[0]['generated_text'])
    print("-" * 40)

if __name__ == "__main__":
    test_llm()
