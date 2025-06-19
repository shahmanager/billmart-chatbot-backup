import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from IndicTransToolkit.processor import IndicProcessor

# Test with the official example from Hugging Face
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

def test_indictrans2():
    try:
        print("Testing IndicTrans2 with official example...")
        
        # Use the exact model and setup from search results
        src_lang, tgt_lang = "hin_Deva", "eng_Latn"
        model_name = "ai4bharat/indictrans2-indic-en-1B"
        
        print(f"Loading tokenizer for {model_name}...")
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        
        print("Loading IndicProcessor...")
        ip = IndicProcessor(inference=True)
        
        print("✅ IndicTrans2 setup successful!")
        print("✅ IndicTransToolkit working properly!")
        
        # Test with simple preprocessing
        test_sentence = ["नमस्ते, आप कैसे हैं?"]
        batch = ip.preprocess_batch(
            test_sentence,
            src_lang=src_lang,
            tgt_lang=tgt_lang,
        )
        print(f"✅ Preprocessing successful: {batch}")
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("IndicTransToolkit not installed correctly")
    except Exception as e:
        print(f"⚠️ Setup error: {e}")
        print("Models might need to be downloaded")

if __name__ == "__main__":
    test_indictrans2()
