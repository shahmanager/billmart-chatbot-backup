#!/usr/bin/env python3
"""
PRODUCTION MULTILINGUAL RASA WRAPPER
Complete implementation with AI4Bharat translation and proper main method
"""
import asyncio
import argparse
import sys
import os
from typing import Dict, List, Optional
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from rasa.core.agent import Agent
    import uvicorn
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    
    # Translation services - AI4Bharat + langdetect
    from langdetect import detect
    from ai4bharat.transliteration import XlitEngine
    
    # AI4Bharat imports
    import torch
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("💡 Install with: pip install fastapi uvicorn langdetect torch transformers")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger(__name__)

class MessageRequest(BaseModel):
    sender: str
    message: str
    metadata: dict = {}

class AI4BharatTranslator:
    """AI4Bharat-based translation service for Indian languages"""
    
    def __init__(self):
        """Initialize AI4Bharat translation models"""
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"🔧 Using device: {self.device}")
        
        # Initialize models
        self.model_name = "ai4bharat/indictrans2-indic-en-1B"
        self.reverse_model_name = "ai4bharat/indictrans2-en-indic-1B"
        
        try:
            # Load tokenizers and models
            logger.info("🔄 Loading AI4Bharat models...")
            
            # Indic to English
            self.tokenizer_indic_en = AutoTokenizer.from_pretrained(self.model_name, trust_remote_code=True)
            self.model_indic_en = AutoModelForSeq2SeqLM.from_pretrained(self.model_name, trust_remote_code=True)
            self.model_indic_en.to(self.device)
            
            # English to Indic  
            self.tokenizer_en_indic = AutoTokenizer.from_pretrained(self.reverse_model_name, trust_remote_code=True)
            self.model_en_indic = AutoModelForSeq2SeqLM.from_pretrained(self.reverse_model_name, trust_remote_code=True)
            self.model_en_indic.to(self.device)
            
            logger.info("✅ AI4Bharat models loaded successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to load AI4Bharat models: {e}")
            self.model_indic_en = None
            self.model_en_indic = None
    
    def detect_language(self, text: str) -> str:
        """Detect language using langdetect"""
        try:
            detected = detect(text.strip())
            logger.info(f"🌍 Detected language: {detected}")
            return detected
        except Exception as e:
            logger.warning(f"⚠️ Language detection failed: {e}, defaulting to English")
            return 'en'
    
    def translate_indic_to_english(self, text: str, source_lang: str) -> str:
        """Translate from Indian language to English using AI4Bharat"""
        if not self.model_indic_en or source_lang == 'en':
            return text
            
        try:
            # Prepare input with language code
            input_text = f"{source_lang}: {text}"
            
            # Tokenize
            inputs = self.tokenizer_indic_en(input_text, return_tensors="pt", padding=True, truncation=True, max_length=512)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate translation
            with torch.no_grad():
                generated_tokens = self.model_indic_en.generate(
                    **inputs,
                    max_length=512,
                    num_beams=5,
                    num_return_sequences=1,
                    temperature=1.0,
                    do_sample=False
                )
            
            # Decode result
            translated = self.tokenizer_indic_en.decode(generated_tokens[0], skip_special_tokens=True)
            
            logger.info(f"🔄 AI4Bharat translation: '{text}' ({source_lang}) -> '{translated}' (en)")
            return translated.strip()
            
        except Exception as e:
            logger.error(f"❌ AI4Bharat Indic->EN translation failed: {e}")
            return text
    
    def translate_english_to_indic(self, text: str, target_lang: str) -> str:
        """Translate from English to Indian language using AI4Bharat"""
        if not self.model_en_indic or target_lang == 'en':
            return text
            
        try:
            # Prepare input with target language code
            input_text = f"en: {text}"
            
            # Tokenize
            inputs = self.tokenizer_en_indic(input_text, return_tensors="pt", padding=True, truncation=True, max_length=512)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate translation
            with torch.no_grad():
                generated_tokens = self.model_en_indic.generate(
                    **inputs,
                    max_length=512,
                    num_beams=5,
                    num_return_sequences=1,
                    temperature=1.0,
                    do_sample=False,
                    forced_bos_token_id=self.tokenizer_en_indic.lang_code_to_id[target_lang]
                )
            
            # Decode result
            translated = self.tokenizer_en_indic.decode(generated_tokens[0], skip_special_tokens=True)
            
            logger.info(f"🔄 AI4Bharat translation: '{text}' (en) -> '{translated}' ({target_lang})")
            return translated.strip()
            
        except Exception as e:
            logger.error(f"❌ AI4Bharat EN->Indic translation failed: {e}")
            return text

class MultilingualRasaWrapper:
    """Production-grade multilingual wrapper with AI4Bharat translation"""
    
    def __init__(self, model_path: str = None):
        """Initialize with AI4Bharat translation services"""
        self.model_path = model_path or self._find_latest_model()
        self.rasa_agent = None
        
        # Initialize AI4Bharat translator
        self.translator = AI4BharatTranslator()
        
        # Supported language mappings
        self.supported_languages = {
            'hi': 'hi',  # Hindi
            'gu': 'gu',  # Gujarati  
            'ta': 'ta',  # Tamil
            'te': 'te',  # Telugu
            'bn': 'bn',  # Bengali
            'mr': 'mr',  # Marathi
            'en': 'en'   # English
        }
        
        self.load_agent()
        
    def _find_latest_model(self):
        """Find latest model file"""
        models_dir = "models"
        if not os.path.exists(models_dir):
            raise FileNotFoundError("Models directory not found")
            
        model_files = [f for f in os.listdir(models_dir) if f.endswith('.tar.gz')]
        if not model_files:
            raise FileNotFoundError("No model files found")
            
        latest_model = max(model_files, key=lambda f: os.path.getctime(os.path.join(models_dir, f)))
        return os.path.join(models_dir, latest_model)
    
    def load_agent(self):
        """Load Rasa agent"""
        try:
            logger.info(f"🤖 Loading Rasa model: {self.model_path}")
            self.rasa_agent = Agent.load(self.model_path)
            logger.info("✅ Rasa agent loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load agent: {e}")
            raise
    
    async def process_message(self, sender_id: str, message: str) -> Dict:
        """Complete multilingual processing pipeline with AI4Bharat"""
        try:
            # Step 1: Detect language
            detected_lang = self.translator.detect_language(message)
            logger.info(f"👂 Original message: '{message}' (Language: {detected_lang})")
            
            # Step 2: Translate to English for Rasa processing
            english_input = message
            if detected_lang != 'en' and detected_lang in self.supported_languages:
                english_input = self.translator.translate_indic_to_english(message, detected_lang)
                logger.info(f"📝 English input for Rasa: '{english_input}'")
            
            # Step 3: Get Rasa response
            rasa_responses = await self.rasa_agent.handle_text(english_input, sender_id=sender_id)
            
            # Step 4: Extract response text
            response_text = self._extract_response_text(rasa_responses)
            logger.info(f"🤖 Rasa response (English): '{response_text}'")
            
            # Step 5: Translate back to user's language
            final_response = response_text
            if detected_lang != 'en' and detected_lang in self.supported_languages:
                final_response = self.translator.translate_english_to_indic(response_text, detected_lang)
                logger.info(f"🌍 Final response ({detected_lang}): '{final_response}'")
            
            return {
                "recipient_id": sender_id,
                "text": final_response,
                "language": detected_lang,
                "original_message": message,
                "english_processed": english_input,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"❌ Processing error: {e}")
            return {
                "recipient_id": sender_id,
                "text": "Sorry, I'm having technical difficulties. Please try again.",
                "language": "en",
                "success": False,
                "error": str(e)
            }
    
    def _extract_response_text(self, responses: List) -> str:
        """Extract text from Rasa responses"""
        if not responses:
            return "I'm not sure how to respond to that."
        
        texts = []
        for response in responses:
            if isinstance(response, dict) and 'text' in response:
                texts.append(response['text'])
            elif hasattr(response, 'text'):
                texts.append(response.text)
        
        return ' '.join(texts) if texts else "I'm not sure how to respond to that."

# FastAPI app setup
app = FastAPI(title="BillMart Multilingual Assistant with AI4Bharat")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global wrapper instance
wrapper = None

@app.on_event("startup")
async def startup_event():
    global wrapper
    logger.info("🚀 Starting BillMart Multilingual Assistant with AI4Bharat...")
    try:
        wrapper = MultilingualRasaWrapper()
        logger.info("✅ Multilingual wrapper with AI4Bharat initialized successfully")
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

@app.post("/webhooks/rest/webhook")
async def webhook(request: MessageRequest):
    """Main webhook endpoint with AI4Bharat translation"""
    if not wrapper:
        raise HTTPException(status_code=500, detail="Wrapper not initialized")
    
    try:
        response = await wrapper.process_message(request.sender, request.message)
        return [response]  # Rasa expects array format
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "running",
        "service": "BillMart Multilingual Assistant",
        "translation_service": "AI4Bharat IndicTrans2",
        "agent_loaded": wrapper and wrapper.rasa_agent is not None,
        "supported_languages": ["Hindi", "English", "Gujarati", "Tamil", "Telugu", "Bengali", "Marathi"]
    }

def main():
    """Main entry point - THE MISSING PIECE!"""
    parser = argparse.ArgumentParser(description="BillMart Multilingual Rasa Assistant with AI4Bharat")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--port", type=int, default=5005, help="Port to run on")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("🚀 BILLMART MULTILINGUAL ASSISTANT")
    logger.info("=" * 70)
    logger.info(f"🌐 Server: http://{args.host}:{args.port}")
    logger.info(f"🔧 Debug: {'ON' if args.debug else 'OFF'}")
    logger.info(f"🌍 Translation: AI4Bharat IndicTrans2")
    logger.info(f"🔤 Languages: Hindi, English, Gujarati, Tamil, Telugu, Bengali, Marathi")
    logger.info("=" * 70)
    
    try:
        uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    except KeyboardInterrupt:
        logger.info("👋 Shutting down...")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")

if __name__ == "__main__":
    main()  # THE MISSING MAIN METHOD THAT WAS CAUSING THE ISSUE!
