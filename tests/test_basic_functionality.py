# tests/test_basic_functionality.py
import sys
import os

# Add project root to path (Windows compatibility)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from actions.minimal_state import ConversationStateManager, UserType

def test_product_detection():
    """Basic test for product detection."""
    
    state_manager = ConversationStateManager()
    
    # Test cases
    test_cases = [
        ("I'm a gig worker", "gigcash"),
        ("Need salary advance", "empcash"),
        ("Business invoice financing", "scf"),
        ("Hospital insurance claim", "icf"),
        ("We need credit rating", "imark"),  # Added more tests
        ("Quick loan needed", "short_term_loan")
    ]
    
    print("Testing product detection...")
    for message, expected in test_cases:
        result = state_manager._detect_product_from_message(message)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"{status}: '{message}' -> {result} (expected: {expected})")

def test_user_type_detection():
    """Test user type detection with debugging."""
    
    state_manager = ConversationStateManager()
    
    test_cases = [
        ("I'm a freelancer", "individual"),
        ("Our company needs funding", "business"),
        ("We are an NBFC", "lender"),
        ("I am a bank", "lender"),  # Additional test
        ("Financial institution here", "lender")  # Additional test
    ]
    
    print("\nTesting user type detection...")
    for message, expected in test_cases:
        result = state_manager._detect_user_type_from_message(message)
        
        # Debug information
        if result != expected:
            print(f"🔍 DEBUG: Testing '{message}'")
            message_lower = message.lower()
            
            # Check each user type's keywords
            for user_type, keywords in state_manager.USER_TYPE_KEYWORDS.items():
                matching_keywords = [kw for kw in keywords if kw.lower() in message_lower]
                if matching_keywords:
                    print(f"   {user_type}: matched keywords = {matching_keywords}")
        
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"{status}: '{message}' -> {result} (expected: {expected})")

def test_state_updates():
    """Test complete state update process."""
    
    print("\nTesting state updates...")
    state_manager = ConversationStateManager()
    
    # Test gig worker declaration
    updated_state = state_manager.update_from_intent(
        "declare_gig_worker", [], "I'm a freelancer"
    )
    
    print(f"After 'declare_gig_worker': user_type = {updated_state.user_type.value}")
    print(f"Product focus detected: {updated_state.product_focus}")
    
    # Test process inquiry
    updated_state = state_manager.update_from_intent(
        "ask_process", [], "what's the process"
    )
    
    print(f"After 'ask_process': conversation_phase = {updated_state.conversation_phase.value}")

if __name__ == "__main__":
    test_product_detection()
    test_user_type_detection()
    test_state_updates()
    print("\n🎉 Enhanced tests completed!")
