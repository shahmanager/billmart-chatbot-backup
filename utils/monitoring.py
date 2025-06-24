# utils/monitoring.py
import logging
import json
import os
from datetime import datetime
from typing import Dict, Any

class ConversationLogger:
    """Production-grade conversation logging for Windows environment."""
    
    def __init__(self):
        # Ensure logs directory exists (Windows path)
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        self.logger = logging.getLogger("billmart_chatbot")
        
        # Configure file handler for production logs
        log_file = os.path.join('logs', 'chatbot_conversations.log')
        handler = logging.FileHandler(log_file, encoding='utf-8')
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log_conversation_turn(self, user_id: str, intent: str, 
                            user_message: str, bot_response: str,
                            state_before: Dict, state_after: Dict,
                            processing_time: float):
        """Log each conversation turn for analytics."""
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "intent": intent,
            "user_message": user_message[:100],  # Truncate for privacy
            "bot_response_length": len(bot_response),
            "state_before": state_before,
            "state_after": state_after,
            "processing_time_ms": round(processing_time * 1000, 2),
            "success": True
        }
        
        self.logger.info(f"CONVERSATION_TURN: {json.dumps(log_entry, ensure_ascii=False)}")
    
    def log_error(self, user_id: str, error_type: str, error_message: str, context: Dict):
        """Log errors for debugging."""
        
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "error_type": error_type,
            "error_message": error_message,
            "context": context,
            "severity": "ERROR"
        }
        
        self.logger.error(f"CHATBOT_ERROR: {json.dumps(error_entry, ensure_ascii=False)}")
    
    def log_performance_metrics(self, metrics: Dict[str, Any]):
        """Log performance metrics for monitoring."""
        
        performance_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "PERFORMANCE_METRICS",
            "metrics": metrics
        }
        
        self.logger.info(f"PERFORMANCE: {json.dumps(performance_entry, ensure_ascii=False)}")
