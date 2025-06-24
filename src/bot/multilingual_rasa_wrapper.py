import asyncio
import os
import sys
from typing import Dict, Optional, List
from datetime import datetime

# Rasa imports  
from rasa.core.agent import Agent

# Your existing translation service
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from translation.simple_translation_service import SimpleTranslationService

class MultilingualRasaWrapper:
    """
    Senior Developer Implementation:
    - Non-invasive wrapper around existing Rasa bot
    - Maintains all existing functionality
    - Adds multilingual support without breaking anything
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize wrapper around your EXISTING working Rasa bot
        
        Args:
            model_path: Path to your trained Rasa model (auto-detects if None)
        """
        print("🔧 Initializing Multilingual Wrapper...")
        
        # Step 1: Initialize translation service
        try:
            self.translator = SimpleTranslationService()
            print("✅ Translation service loaded")
        except Exception as e:
            print(f"❌ Translation service failed: {e}")
            self.translator = None
        
        # Step 2: Load your existing Rasa agent (unchanged)
        self.model_path = model_path or self._find_latest_model()
        try:
            self.rasa_agent = Agent.load(self.model_path)
            print(f"✅ Rasa agent loaded: {self.model_path}")
        except Exception as e:
            print(f"❌ Rasa agent failed: {e}")
            self.rasa_agent = None
            
        # Step 3: Conversation tracking (for debug and analytics)
        self.conversations = {}
        
        print("🚀 Multilingual wrapper ready!")
    
    def _find_latest_model(self) -> str:
        """Auto-detect your latest trained model"""
        models_dir = "models"
        if not os.path.exists(models_dir):
            raise FileNotFoundError(
                "No models directory found. Train your Rasa model first with 'rasa train'"
            )
        
        model_files = [f for f in os.listdir(models_dir) if f.endswith('.tar.gz')]
        if not model_files:
            raise FileNotFoundError(
                "No trained models found. Run 'rasa train' to create a model first"
            )
        
        # Get most recent model
        latest_model = max(
            model_files, 
            key=lambda f: os.path.getmtime(os.path.join(models_dir, f))
        )
        return os.path.join(models_dir, latest_model)
    
    async def process_message_async(self, user_id: str, message: str, 
                                   include_debug: bool = False) -> Dict:
        """
        MAIN PROCESSING PIPELINE (Async)
        
        This is the core method that handles multilingual conversation
        while keeping your existing Rasa bot completely unchanged.
        """
        
        if not self.rasa_agent:
            return self._create_error_response("Rasa agent not available")
        
        if not self.translator:
            # Fallback to English-only mode
            return await self._process_english_only(user_id, message, include_debug)
        
        try:
            
            # STEP 1: Language Detection
            detected_language = self.translator.detect_language(message)
            debug_info = {'original_message': message, 'detected_language': detected_language}
            
            # STEP 2: Translation to English (if needed)
            if detected_language != 'english':
                english_message = self.translator.translate_text(
                    message, detected_language, 'english'
                )
                debug_info['english_translation'] = english_message
            else:
                english_message = message
                debug_info['english_translation'] = 'No translation needed'
            
            # STEP 3: Process with YOUR EXISTING RASA BOT (unchanged)
            rasa_response = await self.rasa_agent.handle_text(
                english_message, sender_id=user_id
            )
            debug_info['rasa_response'] = rasa_response
            
            # STEP 4: Extract response text from Rasa
            english_response_text = self._extract_text_from_rasa_response(rasa_response)
            debug_info['english_response'] = english_response_text
            
            # STEP 5: Translate response back to user's language
            if detected_language != 'english':
                final_response = self.translator.translate_text(
                    english_response_text, 'english', detected_language
                )
                debug_info['final_translation'] = final_response
            else:
                final_response = english_response_text
                debug_info['final_translation'] = 'No translation needed'
            
            # STEP 6: Store conversation for analytics
            self._store_conversation_entry(user_id, message, final_response, 
                                         detected_language, rasa_response)
            
            # STEP 7: Return structured response
            response = {
                'response': final_response,
                'language': detected_language,
                'intent': self._extract_intent_from_rasa(rasa_response),
                'confidence': self._extract_confidence_from_rasa(rasa_response),
                'success': True
            }
            
            if include_debug:
                response['debug'] = debug_info
            
            return response
            
        except Exception as e:
            error_msg = f"Translation processing error: {str(e)}"
            print(f"❌ {error_msg}")
            return self._create_error_response(error_msg, include_debug)
    
    def _extract_text_from_rasa_response(self, rasa_response: List) -> str:
        """
        Extract text from your Rasa bot's response
        
        Senior Dev Note: This handles different Rasa response formats
        """
        if not rasa_response:
            return "I'm not sure how to help with that. Could you please rephrase your question?"
        
        # Get first response (most common case)
        first_response = rasa_response[0]
        
        # Handle different response formats from Rasa
        if isinstance(first_response, dict):
            if 'text' in first_response:
                return first_response['text']
            elif 'response' in first_response and isinstance(first_response['response'], dict):
                if 'text' in first_response['response']:
                    return first_response['response']['text']
        
        # Fallback for unexpected formats
        return "I understand your question, but I'm having trouble generating a response. Please contact our support team."
    
    def _extract_intent_from_rasa(self, rasa_response: List) -> Optional[str]:
        """Extract intent classification from Rasa response"""
        if rasa_response and isinstance(rasa_response[0], dict):
            intent_data = rasa_response[0].get('intent', {})
            return intent_data.get('name') if isinstance(intent_data, dict) else None
        return None
    
    def _extract_confidence_from_rasa(self, rasa_response: List) -> Optional[float]:
        """Extract confidence score from Rasa response"""
        if rasa_response and isinstance(rasa_response[0], dict):
            intent_data = rasa_response[0].get('intent', {})
            return intent_data.get('confidence') if isinstance(intent_data, dict) else None
        return None
    
    async def _process_english_only(self, user_id: str, message: str, 
                                  include_debug: bool = False) -> Dict:
        """Fallback to English-only processing if translation unavailable"""
        try:
            rasa_response = await self.rasa_agent.handle_text(message, sender_id=user_id)
            response_text = self._extract_text_from_rasa_response(rasa_response)
            
            return {
                'response': response_text,
                'language': 'english',
                'intent': self._extract_intent_from_rasa(rasa_response),
                'confidence': self._extract_confidence_from_rasa(rasa_response),
                'success': True,
                'debug': {'note': 'Translation service unavailable, English-only mode'} if include_debug else None
            }
        except Exception as e:
            return self._create_error_response(f"English processing error: {str(e)}", include_debug)
    
    def _create_error_response(self, error_message: str, include_debug: bool = False) -> Dict:
        """Create standardized error response"""
        response = {
            'response': 'I apologize, but I encountered an error. Please try again or contact our support team.',
            'language': 'english',
            'intent': None,
            'confidence': None,
            'success': False
        }
        
        if include_debug:
            response['debug'] = {'error': error_message}
        
        return response
    
    def _store_conversation_entry(self, user_id: str, user_message: str, 
                                bot_response: str, language: str, rasa_data: List):
        """Store conversation for analytics and debugging"""
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'user_message': user_message,
            'bot_response': bot_response,
            'language': language,
            'intent': self._extract_intent_from_rasa(rasa_data),
            'confidence': self._extract_confidence_from_rasa(rasa_data)
        }
        
        self.conversations[user_id].append(entry)
        
        # Keep only last 50 exchanges per user
        if len(self.conversations[user_id]) > 50:
            self.conversations[user_id] = self.conversations[user_id][-50:]
    
    # SYNCHRONOUS WRAPPER for easier integration
    def process_message(self, user_id: str, message: str, 
                       include_debug: bool = False) -> Dict:
        """
        Synchronous wrapper for async processing
        
        Use this method for easy integration with existing systems
        """
        # Inside process_message() after translation
        print(f"🌍 Detected Language: {detected_language}")
        print(f"📤 Translated Response: {translated_response}")

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(
                self.process_message_async(user_id, message, include_debug)
            )
        except Exception as e:
            return self._create_error_response(f"Async processing error: {str(e)}", include_debug)
        finally:
            loop.close()
    
    def get_conversation_history(self, user_id: str) -> List[Dict]:
        """Get conversation history for a user"""
        return self.conversations.get(user_id, [])
    
    def get_system_status(self) -> Dict:
        """System health check"""
        return {
            'rasa_agent_status': 'loaded' if self.rasa_agent else 'failed',
            'translation_service_status': 'available' if self.translator else 'unavailable',
            'model_path': self.model_path,
            'active_conversations': len(self.conversations),
            'total_exchanges': sum(len(convs) for convs in self.conversations.values())
        }


# TESTING AND CLI INTERFACE
def main():
    """
    Command-line interface for testing your multilingual wrapper
    """
    print("🚀 MULTILINGUAL RASA WRAPPER - TESTING INTERFACE")
    print("=" * 60)
    print("🎯 This wrapper integrates translation with your EXISTING Rasa bot")
    print("📚 Your Rasa training and responses remain completely unchanged")
    print("=" * 60)
    
    # Initialize wrapper
    try:
        bot = MultilingualRasaWrapper()
        status = bot.get_system_status()
        
        print(f"\n📊 System Status:")
        for key, value in status.items():
            print(f"   {key}: {value}")
        
        if status['rasa_agent_status'] != 'loaded':
            print("\n❌ Cannot proceed: Rasa agent not loaded")
            print("💡 Solution: Run 'rasa train' first to create a model")
            return
            
    except Exception as e:
        print(f"❌ Wrapper initialization failed: {e}")
        return
    
    print(f"\n💬 Test your multilingual BillMart bot:")
    print(f"🌍 Try: English, Hindi, Gujarati, Tamil, etc.")
    print(f"🔧 Debug mode: Add '--debug' to see translation steps")
    print(f"🚪 Type 'quit' to exit")
    print("-" * 60)
    
    user_id = "test_user_multilingual"
    debug_mode = '--debug' in sys.argv
    
    while True:
        try:
            user_input = input(f"\n👤 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye', 'q']:
                break
                
            if not user_input:
                continue
            
            # Process with wrapper
            result = bot.process_message(user_id, user_input, include_debug=debug_mode)
            
            # Display result
            print(f"🤖 Bot: {result['response']}")
            print(f"🌍 Language: {result['language']}")
            
            if result.get('intent'):
                confidence = result.get('confidence', 0)
                print(f"🎯 Intent: {result['intent']} (confidence: {confidence:.2f})")
            
            if debug_mode and result.get('debug'):
                print(f"🔧 Debug Info:")
                for key, value in result['debug'].items():
                    print(f"   {key}: {value}")
            
            if not result['success']:
                print(f"⚠️ Note: Error occurred during processing")
                
        except KeyboardInterrupt:
            print(f"\n\n👋 Interrupted by user")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
    
    # Show session summary
    history = bot.get_conversation_history(user_id)
    if history:
        print(f"\n📊 Session Summary:")
        print(f"   Total exchanges: {len(history)}")
        languages_used = set(entry['language'] for entry in history)
        print(f"   Languages used: {', '.join(sorted(languages_used))}")
        intents_used = set(entry['intent'] for entry in history if entry['intent'])
        print(f"   Intents triggered: {', '.join(sorted(intents_used))}")
    
    print(f"\n✅ Multilingual wrapper test completed!")
    print(f"🎯 Your Rasa bot now supports multilingual conversations!")

if __name__ == "__main__":
    main()
