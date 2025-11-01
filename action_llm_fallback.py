# actions/action_llm_fallback.py
"""
Simple LLM Fallback Action - Just routes to configured system
"""
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

# Import config
from .fallback_config import ACTIVE_FALLBACK, FALLBACK_ENABLED

# Global variables for lazy loading (avoid startup delay)
_llm_only_system = None
_static_rag_system = None
_dynamic_rag_system = None
_dynamic_llm_system = None

def get_llm_only():
    """Lazy load LLM-only system"""
    global _llm_only_system
    if _llm_only_system is None:
        print("🔄 Loading LLM-only system...")
        from .llm_only_fallback import llm_only_fallback
        _llm_only_system = llm_only_fallback
        print("✅ LLM-only ready")
    return _llm_only_system

def get_static_rag():
    """Lazy load Static RAG"""
    global _static_rag_system
    if _static_rag_system is None:
        print("🔄 Loading Static RAG system...")
        from .llm_fallback import BillMartRAGFallback
        _static_rag_system = BillMartRAGFallback()
        print("✅ Static RAG ready")
    return _static_rag_system

def get_dynamic_rag():
    """Lazy load Dynamic RAG"""
    global _dynamic_rag_system
    if _dynamic_rag_system is None:
        print("🔄 Loading Dynamic RAG system...")
        from .dynamic_rag_fallback import DynamicRAGSystem
        _dynamic_rag_system = DynamicRAGSystem()
        print("✅ Dynamic RAG ready")
    return _dynamic_rag_system

def get_dynamic_llm():
    """Lazy load Dynamic LLM"""
    global _dynamic_llm_system
    if _dynamic_llm_system is None:
        print("🔄 Loading Dynamic LLM system...")
        from .dynamic_llm_fallback import DynamicLLMSystem
        _dynamic_llm_system = DynamicLLMSystem()
        print("✅ Dynamic LLM ready")
    return _dynamic_llm_system


class ActionLLMFallback(Action):
    """
    Main fallback action - automatically triggered by Rasa when confidence is low
    Routes to system configured in fallback_config.py
    """
    
    def name(self) -> Text:
        return "action_llm_fallback"
    
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        # Get user's query
        user_message = tracker.latest_message.get('text', '')
        intent = tracker.latest_message.get('intent', {}).get('name', 'unknown')
        confidence = tracker.latest_message.get('intent', {}).get('confidence', 0.0)
        
        print(f"\n{'='*60}")
        print(f"🤖 LLM FALLBACK TRIGGERED")
        print(f"Query: {user_message}")
        print(f"Intent: {intent} (confidence: {confidence:.2f})")
        print(f"Active System: {ACTIVE_FALLBACK}")
        print(f"{'='*60}\n")
        
        # Check if fallback is enabled
        if not FALLBACK_ENABLED:
            dispatcher.utter_message(
                text="I'm not sure about that. Could you rephrase or ask something else about BillMart?"
            )
            return []
        
        # Route to configured system
        try:
            if ACTIVE_FALLBACK == 'llm_only':
                self._handle_llm_only(dispatcher, user_message)
                
            elif ACTIVE_FALLBACK == 'static_rag':
                self._handle_static_rag(dispatcher, user_message)
                
            elif ACTIVE_FALLBACK == 'dynamic_rag':
                self._handle_dynamic_rag(dispatcher, user_message)
                
            elif ACTIVE_FALLBACK == 'dynamic_llm':
                self._handle_dynamic_llm(dispatcher, user_message)
                
            else:  # 'none' or invalid
                dispatcher.utter_message(
                    text="I'm not sure about that. Could you rephrase or ask something else about BillMart?"
                )
        
        except Exception as e:
            print(f"❌ Fallback error: {e}")
            import traceback
            traceback.print_exc()
            dispatcher.utter_message(
                text="I apologize, I'm experiencing technical difficulties. Please try rephrasing your question or contact BillMart support."
            )
        
        return [
            SlotSet("last_fallback_mode", ACTIVE_FALLBACK),
            SlotSet("last_confidence", confidence)
        ]
    
    def _handle_llm_only(self, dispatcher, query):
        """Handle LLM-only fallback"""
        llm_func = get_llm_only()
        answer = llm_func(query)
        dispatcher.utter_message(text=answer)
    
    def _handle_static_rag(self, dispatcher, query):
        """Handle Static RAG fallback"""
        rag = get_static_rag()
        answer = rag.generate_fallback_response(query)
        dispatcher.utter_message(text=answer)
    
    def _handle_dynamic_rag(self, dispatcher, query):
        """Handle Dynamic RAG fallback"""
        rag = get_dynamic_rag()
        result = rag.generate_response_with_citations(query)
        
        # Send main answer
        dispatcher.utter_message(text=result['answer'])
        
        # Send sources if available
        if result.get('sources') and len(result['sources']) > 0:
            sources_text = "\n\n📚 **Sources:**\n"
            for src in result['sources'][:3]:  # Top 3 sources
                sources_text += f"• {src.get('title', 'Source')}\n"
            dispatcher.utter_message(text=sources_text)
    
    def _handle_dynamic_llm(self, dispatcher, query):
        """Handle Dynamic LLM fallback"""
        llm = get_dynamic_llm()
        result = llm.generate_response_with_live_sources(query)
        
        # Send main answer
        dispatcher.utter_message(text=result['answer'])
        
        # Send sources if available
        if result.get('sources') and len(result['sources']) > 0:
            sources_text = "\n\n📚 **Regulatory Sources:**\n"
            for src in result['sources'][:3]:
                regulator = src.get('regulator', 'N/A')
                title = src.get('title', 'Source')
                sources_text += f"• {title} ({regulator})\n"
            dispatcher.utter_message(text=sources_text)
