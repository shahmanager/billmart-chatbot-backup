# tests/test_minimal_state.py
import pytest
from actions.minimal_state import ConversationStateManager, UserType, ConversationPhase

class TestMinimalState:
    
    def setup_method(self):
        """Run before each test method."""
        self.state_manager = ConversationStateManager()
    
    def test_gig_worker_detection_from_platforms(self):
        """Test that platform mentions detect gig worker context."""
        test_cases = [
            ("I drive for uber", "gigcash"),
            ("Zomato delivery partner here", "gigcash"),
            ("Freelance developer", "gigcash"),
            ("Regular office job", None)  # Should not match gig work
        ]
        
        for message, expected_product in test_cases:
            result = self.state_manager._detect_product_from_message(message)
            assert result == expected_product, f"Failed for: {message}"
    
    def test_business_detection(self):
        """Test business context detection."""
        test_cases = [
            ("Our MSME needs working capital", "scf"),
            ("Invoice financing for our company", "scf"),
            ("Hospital insurance claim", "icf")
        ]
        
        for message, expected_product in test_cases:
            result = self.state_manager._detect_product_from_message(message)
            assert result == expected_product, f"Failed for: {message}"
    
    def test_state_transitions(self):
        """Test that state transitions work correctly."""
        
        # Initial state
        assert self.state_manager.current_state.user_type == UserType.UNKNOWN
        
        # Declare as gig worker
        updated_state = self.state_manager.update_from_intent(
            "declare_gig_worker", [], "I'm a freelancer"
        )
        
        assert updated_state.user_type == UserType.INDIVIDUAL
        assert updated_state.product_focus == "gigcash"
    
    def test_clarification_logic(self):
        """Test when clarification questions are needed."""
        
        # Should ask for clarification when user type unknown
        assert self.state_manager.should_ask_for_clarification() == True
        
        # Set user type
        self.state_manager.current_state.user_type = UserType.INDIVIDUAL
        
        # Should still ask for product clarification
        assert self.state_manager.should_ask_for_clarification() == True
        
        # Set product focus
        self.state_manager.current_state.product_focus = "gigcash"
        
        # Should not need clarification anymore
        assert self.state_manager.should_ask_for_clarification() == False
