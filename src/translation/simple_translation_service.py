import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from langdetect import detect

class SimpleTranslationService:
    def __init__(self):

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Lazy loading: Initialize as None, load when needed
        self.model = None
        self.tokenizer = None
        
        # Language mapping: langdetect codes → IndicTrans2 codes
        self.language_codes = {
            'hi': 'hin_Deva',      # Hindi - Devanagari script
            'bn': 'ben_Beng',      # Bengali - Bengali script
            'mr': 'mar_Deva',      # Marathi - Devanagari script
            'ta': 'tam_Taml',      # Tamil - Tamil script
            'te': 'tel_Telu',      # Telugu - Telugu script
            'gu': 'guj_Gujr',      # Gujarati - Gujarati script
            'kn': 'kan_Knda',      # Kannada - Kannada script
            'ml': 'mal_Mlym',      # Malayalam - Malayalam script
            'ur': 'urd_Arab',      # Urdu - Arabic script
            'or': 'ory_Orya'       # Odia - Oriya script
        }
    
    def detect_language(self, text):
        """
        Detect the language of input text and map to IndicTrans2 format.
        
        Args:
            text (str): Input text to analyze
            
        Returns:
            str: IndicTrans2 language code or 'english' if detection fails
        """
        try:
            # Use langdetect to identify language (returns ISO codes like 'hi', 'bn')
            detected = detect(text)
            
            # Map to IndicTrans2 format, default to 'english' if not found
            return self.language_codes.get(detected, 'english')
        except Exception:
            # Fallback to English if detection fails (empty text, special chars, etc.)
            return 'english'
        
    def load_translation_model(self):
        """load AI4Bharat IndicTrans2 translation model- heavy model"""
        if self.model is None:
            print("Loading IndicTrans2 model...")
            print("this may take some time to load 800mb model...")
            model_name = "ai4bharat/indictrans2-en-indic-dist-200M"
            self.tokenizer=AutoTokenizer.from_pretrained(
                model_name,trust_remote_code=True
            )
            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                model_name,trust_remote_code=True,
                torch_dtype=torch.float16).to(self.device)
            print(" AI4Bharat Model loaded successfully!")
        else:
            print("Model already loaded, skipping...")

    def _get_language_code(self, language):
        """convert human readable text into IndicTrans2 code"""
        if language.lower()=='english':
            return 'eng_Latn'
        language_mapping={
            'hindi': 'hin_Deva',
            'hin_deva': 'hin_Deva',  
            'bengali': 'ben_Beng',
            'marathi': 'mar_Deva',
            'tamil': 'tam_Taml',
            'telugu': 'tel_Telu',
            'gujarati': 'guj_Gujr',
            'kannada': 'kan_Knda',
            'malayalam': 'mal_Mlym',
            'urdu': 'urd_Arab',
            'odia': 'ory_Orya'
        }
        return language_mapping.get(language.lower(),'eng_Latn')
    def translate_text(self,text,source_lang, target_lang):
        
        self.load_translation_model()
        src_code=self._get_language_code(source_lang)
        tgt_code=self._get_language_code(target_lang)

        input_text=f"{src_code} {tgt_code} {text}"
        inputs = self.tokenizer(input_text,return_tensors="pt",padding=True,
                     max_length=512,truncation=True).to(self.device)
        with torch.no_grad():
            outputs=self.model.generate(**inputs,max_length=256,
                        num_beams=3,early_stopping=True,do_sample=False)
            translation=self.tokenizer.decode(outputs[0],skip_special_tokens=True,
                                              clean_up_tokenization_spaces=True)
        return translation.strip()
            


    
    def debug_gpu_info(self):
        """Debug method to display GPU availability and system information"""
        print("=== GPU Debug Information ===")
        print(f"PyTorch version: {torch.__version__}")
        print(f"CUDA available: {torch.cuda.is_available()}")
        
        if torch.cuda.is_available():
            print(f"CUDA version: {torch.version.cuda}")
            print(f"Number of GPUs: {torch.cuda.device_count()}")
            print(f"GPU name: {torch.cuda.get_device_name(0)}")
        else:
            print(" CUDA not available - possible reasons:")
            print("  1. PyTorch CPU-only version installed")
            print("  2. NVIDIA drivers not installed") 
            print("  3. GPU not CUDA-compatible")
        print("=========================")

# Test code - only runs when script is executed directly
if __name__ == "__main__":
    print(" Translation Service - Development Testing")
    print("=" * 60)
    
    # Initialize the service
    service = SimpleTranslationService()
    
    # Display system information
    service.debug_gpu_info()
    
    # Test language detection first
    print(f"\n Language Detection Tests:")
    test_cases = [
        "Hello, how are you?",
        "नमस्ते, आप कैसे हैं?",
        "হ্যালো, আপনি কেমন আছেন?",
    ]
    
    for text in test_cases:
        detected = service.detect_language(text)
        print(f"   '{text}' → {detected}")
    
    # Test AI Translation 
    print(f"\n AI Translation Tests:")
    print("   Loading AI4Bharat IndicTrans2 model...")
    
    translation_tests = [
        ("Hello, how are you?", "english", "hindi"),
        ("What is your name?", "english", "tamil"),
        ("I need loan information", "english", "bengali"),
        ("Thank you very much", "english", "gujarati")
    ]
    
    for text, src_lang, tgt_lang in translation_tests:
        try:
            print(f"\n    Translating: '{text}'")
            print(f"      From: {src_lang} → To: {tgt_lang}")
            
            translation = service.translate_text(text, src_lang, tgt_lang)
            print(f"      Result: '{translation}'")
            print("       Translation successful!")
            
        except Exception as e:
            print(f"       Translation failed: {e}")
    
    print(f"\n Final Service Status:")
    print(f"   Device: {service.device}")
    print(f"   Model loaded: {service.model is not None}")
    print(f"   Ready for production!")
    
    print("\n AI Translation Service Test Complete!")
