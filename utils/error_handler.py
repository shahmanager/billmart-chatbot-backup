# utils/error_handler.py
from typing import Optional, Dict, Any
from rasa_sdk.executor import CollectingDispatcher

class ChatbotErrorHandler:
    """Centralized error handling for production chatbot."""
    
    @staticmethod
    def handle_intent_classification_error(dispatcher: CollectingDispatcher, 
                                         user_message: str) -> str:
        """Handle when NLU fails to classify intent."""
        
        # Try to extract keywords for partial matching
        keywords = user_message.lower().split()
        
        # Smart fallback based on keywords
        if any(word in keywords for word in ["loan", "money", "cash", "funding"]):
            return """I understand you're looking for funding. Let me help you find the right solution!

Are you:
👤 **Individual** - Personal advance needs
🏢 **Business** - Working capital needs
🏦 **Lender** - Investment opportunities"""
        
        elif any(word in keywords for word in ["process", "apply", "how"]):
            return """I'd be happy to explain our process! Which product are you interested in?

• **GigCash** - Gig worker funding
• **EmpCash** - Salary advance
• **SCF** - Supply chain finance
• **ICF** - Insurance claim finance"""
        
        else:
            return """I want to help you find the right information. You can ask me about:

💰 **Our Products** - Funding solutions we offer
📋 **Application Process** - How to apply
✅ **Eligibility** - Who can apply
📞 **Contact Us** - How to reach our team

What would you like to know?"""
    
    @staticmethod
    def handle_state_corruption(dispatcher: CollectingDispatcher) -> str:
        """Handle when conversation state gets corrupted."""
        
        return """Let me start fresh to help you better. 

Are you looking for:
👤 **Personal funding** (salary advance, gig worker funding)
🏢 **Business funding** (working capital, supply chain finance)
🏦 **Investment opportunities** (for lenders and NBFCs)

Please let me know which category interests you!"""
    
    @staticmethod
    def handle_timeout_error(dispatcher: CollectingDispatcher) -> str:
        """Handle system timeout errors."""
        
        return """I'm experiencing some delays. Let me connect you directly with our team:

📞 **Call us:** +91 93269 46663
✉️ **Email:** care@billmart.com

Or you can try asking your question again!"""
