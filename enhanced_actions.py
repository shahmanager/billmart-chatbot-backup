# actions/enhanced_actions.py
from typing import Dict, Text, Any, List, Optional
import logging
import time
import os
import sys

# Add parent directory to path for imports (Windows compatibility)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction

from .minimal_state import ConversationStateManager, MinimalConversationState

# Initialize logger
logger = logging.getLogger(__name__)

class ActionSessionStart(Action):
    def name(self) -> Text:
        return "action_session_start"

    def run(self, dispatcher, tracker, domain):
        # Initialize any session-specific data here
        return [SlotSet("session_started_metadata", {"started_at": time.time()})]


class ActionProcessWithMinimalState(Action):
    """Production-ready action with context awareness and error handling."""
    
    def name(self) -> Text:
        return "action_process_with_minimal_state"
    
    def __init__(self):
        self.state_manager = ConversationStateManager()
    
    # actions/enhanced_actions.py
    def run(self, dispatcher: CollectingDispatcher, 
       tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        """Nuclear option: Force fresh state for problematic intents."""
        
        try:
            # Extract conversation data
            latest_message = tracker.latest_message
            intent_name = latest_message.get("intent", {}).get("name", "")
            entities = latest_message.get("entities", [])
            user_message = latest_message.get("text", "")
            
            print(f"🔥 NUCLEAR DEBUG: Intent={intent_name}, Message='{user_message}'")
            
            # NUCLEAR OPTION: Reset state for loan requests (ignore old state completely)
            if intent_name == "ask_loan_need":
                print("🔥 NUCLEAR RESET: Forcing fresh state for loan request")
                
                # Don't load ANY old state, start completely fresh
                self.state_manager.current_state = MinimalConversationState()
                
                # Direct response bypass all logic
                dispatcher.utter_message(text="""I'd love to help you find the perfect funding solution! 💡

                To guide you to the right product, please tell me:

                👤 **Individual** - Personal funding needs (salary advance, gig work funding)
                🏢 **Business** - Company funding needs (working capital, growth funding)  
                🏦 **Lender/NBFC** - Investment opportunities

                Which category describes you best? 🎯""")
                                
                        # Return completely fresh state
                fresh_state = {
                    "user_type": "unknown",
                    "product_focus": None,
                    "conversation_phase": "initial",
                    "last_intent": intent_name
                }
                
                print(f"🔥 NUCLEAR RESULT: Fresh state = {fresh_state}")
                return [SlotSet("conversation_state", fresh_state)]
            
            # For other intents, proceed normally but with debugging
            existing_state_data = tracker.get_slot("conversation_state") or {}
            print(f"🔥 NORMAL FLOW: Loaded state = {existing_state_data}")
            
            if existing_state_data:
                self.state_manager.current_state = MinimalConversationState.from_dict(existing_state_data)
            
            # Update state
            updated_state = self.state_manager.update_from_intent(
                intent_name, entities, user_message
            )
            
            print(f"🔥 NORMAL RESULT: Updated state = {updated_state.to_dict()}")
            
            # Generate response
            response_text = self._generate_contextual_response(
                intent_name, updated_state, user_message
            )
            
            dispatcher.utter_message(text=response_text)
            
            
            events_to_return = [SlotSet("conversation_state", updated_state.to_dict())]

            # Dynamic product detection - NO HARDCODING
            PRODUCT_INTENT_MAPPING = {
                "ask_empcash_info": "empcash",
                "ask_gigcash_info": "gigcash", 
                "ask_supply_chain_finance": "scf",
                "ask_insurance_claim_finance": "icf",
                "ask_imark_info": "imark",
                "ask_lease_rental_discounting": "lrd",
                "ask_short_term_loan": "short_term_loan",
                "ask_term_loan": "term_loan"
            }

            # Set product_focus slot dynamically
            detected_product = PRODUCT_INTENT_MAPPING.get(intent_name)
            if detected_product:
                events_to_return.append(SlotSet("product_focus", detected_product))

            return events_to_return
            
        except Exception as e:
            print(f"🔥 ERROR: {str(e)}")
            dispatcher.utter_message(text="I'm having technical difficulties. Please try again!")
            return []


        
    def _generate_contextual_response(self, intent_name: str, 
                                    state: MinimalConversationState,
                                    user_message: str) -> str:
        """Generate context-aware responses."""
        
        try:
            # Context-aware response routing
            if intent_name == "ask_process":
                return self._get_process_response(state)
            elif intent_name == "ask_eligibility":
                return self._get_eligibility_response(state)
            elif intent_name in ["ask_gigcash_info", "ask_empcash_info", "ask_supply_chain_finance"]:
                return self._get_product_info_response(intent_name, state)
            elif intent_name.startswith("declare_"):
                return self._get_declaration_response(state)
            elif intent_name == "ask_loan_need":
                return self._get_loan_need_response(state)
            else:
                return self._get_smart_fallback_response(state, user_message)
                
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "I'm here to help! What would you like to know about our financial services?"
    
    def _get_process_response(self, state: MinimalConversationState) -> str:
        """Get process information based on product focus."""
        
        if state.product_focus == "gigcash":
            return """🎯 **GigCash Application Process:**

1. **Connect Platform** - Link your gig work account (Uber, Zomato, etc.)
2. **Verify Earnings** - We verify your last 3-6 months earnings
3. **Check Eligibility** - See your advance limit (up to 50% monthly earnings)
4. **Apply** - Request the amount you need
5. **Get Funded** - Money in your account within 2 hours
6. **Auto-Repay** - Deducted from your next platform earnings

Ready to get started? 🚀"""

        elif state.product_focus == "empcash":
            return """💰 **EmpCash Application Process:**

1. **Employee Verification** - Confirm your employer is a BillMart partner
2. **Salary Verification** - Link your salary account for verification
3. **Calculate Limit** - See your advance amount (up to 50% earned salary)
4. **Apply** - Request advance through our secure platform
5. **Instant Approval** - Get approved in minutes
6. **Receive Funds** - Money credited within 2 hours
7. **Auto-Deduction** - Repaid from your next salary automatically

Want to check if your employer is a partner? 📞"""

        elif state.product_focus == "scf":
            return """🔗 **Supply Chain Finance Process:**

1. **Anchor Evaluation** - The buyer company is evaluated and approved
2. **Vendor/Dealer Onboarding** - Suppliers are evaluated and approved  
3. **Limit Setup** - Credit limit is sanctioned for the anchor
4. **Transaction Initiation** - Either party uploads an invoice
5. **Verification & Approval** - GST and compliance checks
6. **Disbursement** - Funds disbursed directly to the supplier
7. **Repayment** - Buyer repays as per agreed terms

Which specific SCF service interests you? 💼"""

        elif state.product_focus == "icf":
            return """🏥 **Insurance Claim Finance Process:**

1. **Hospital Verification** - Confirm NABH/NABL certification
2. **Claim Documentation** - Submit pending insurance claims
3. **Verification** - We verify claim validity and amounts
4. **Quick Approval** - Fast approval based on claim strength
5. **Disbursement** - Funds transferred within 24-48 hours
6. **Claim Settlement** - Repayment when insurance pays

Ready to improve your hospital's cash flow? 🏥"""
        
        else:
            return """I'd be happy to explain our process! Which product interests you?

• **GigCash** 🎯 - For gig workers and freelancers
• **EmpCash** 💰 - For salaried employees  
• **Supply Chain Finance** 🔗 - For businesses
• **Insurance Claim Finance** 🏥 - For hospitals
• **Term Loans** 💼 - For business expansion
• **iMark** 📊 - AI credit rating

Just let me know which one! 😊"""
    
    def _get_eligibility_response(self, state: MinimalConversationState) -> str:
        """Get eligibility information based on product focus."""
        
        if state.product_focus == "gigcash":
            return """🎯 **GigCash Eligibility Requirements:**

✅ **Basic Requirements:**
• Active on gig platforms (Uber, Ola, Zomato, Swiggy, Dunzo, etc.)
• Minimum 3 months consistent earnings history
• Valid KYC documents (Aadhar, PAN)
• Active bank account linked to platforms

✅ **Earnings Criteria:**
• Consistent monthly earnings of ₹15,000+
• Regular activity on platforms (not dormant accounts)
• Good platform ratings (4+ stars typically)
• Verifiable payment history

📊 **Advance Details:**
• Up to 50% of average monthly earnings
• Maximum ₹50,000 per advance
• Can combine multiple platform earnings

Ready to check your specific eligibility? 🚀"""
        
        elif state.product_focus == "empcash":
            return """💰 **EmpCash Eligibility Requirements:**

✅ **Employment Requirements:**
• Salaried employee at BillMart partner company
• Minimum 3 months employment with current employer
• Regular salary credits to bank account
• No pending disciplinary issues

✅ **Financial Criteria:**
• Monthly salary of ₹15,000+
• Consistent salary payments
• Valid bank account with salary credits
• Good repayment history (if applicable)

📊 **Advance Details:**
• Up to 50% of earned salary
• Maximum ₹1,00,000 per advance
• Multiple advances allowed per month

Want to check if your employer is a partner? 📞 +91 93269 46663"""

        elif state.product_focus == "scf":
            return """🔗 **Supply Chain Finance Eligibility:**

✅ **Business Requirements:**
• GST-registered business entity
• Minimum 1 year of operations
• Valid trade licenses and registrations
• Established buyer-supplier relationships

✅ **Financial Criteria:**
• Annual turnover of ₹1 crore+
• Regular business transactions
• Good credit history
• Valid financial statements

📊 **Financing Details:**
• Up to 80-95% of invoice value
• Invoice amount minimum ₹50,000
• Quick processing and disbursement

Ready to check your business eligibility? 💼"""

        elif state.product_focus == "icf":
            return """🏥 **Insurance Claim Finance Eligibility:**

✅ **Hospital Requirements:**
• NABH/NABL certified hospital
• Valid insurance empanelment
• Minimum 2 years operational
• Good claim settlement history

✅ **Claim Criteria:**
• Pending insurance claims ≥30 days
• Valid claim documentation
• TPA/Insurance company acknowledgment
• Claim amount minimum ₹1 lakh

📊 **Financing Details:**
• Up to 80% of claim value
• Quick disbursement within 24-48 hours
• Flexible repayment options

Want to improve your hospital's cash flow? 🏥"""
        
        else:
            return f"Let me check eligibility requirements for you! Which product are you interested in? I can provide specific requirements for {state.product_focus or 'any of our services'}."
    
    def _get_product_info_response(self, intent_name: str, state: MinimalConversationState) -> str:
        """Get detailed product information."""
        
        if "gigcash" in intent_name or state.product_focus == "gigcash":
            return """🎯 **GigCash - Fast, Flexible Funding for Gig Workers**

**What is GigCash?**
Quick financial support for freelancers and gig workers facing irregular income flows. Perfect for covering urgent expenses or bridging payment gaps.

**Key Benefits:**
• 💰 Up to 50% of monthly earnings
• ⚡ Funds credited within 2 hours
• 📱 100% digital application process
• 🔄 Auto-repay from platform earnings
• ✅ No traditional credit score required

**Supported Platforms:**
🚗 Uber, Ola | 🍕 Zomato, Swiggy | 📦 Dunzo, Amazon | 💻 Freelance platforms

Want to know about **eligibility**, **process**, or **fees**? 🤔"""

        elif ("short_term_loan" in intent_name or "ask_short_term_loan" == intent_name or 
        state.product_focus == "short_term_loan"): 
            return """⚡ **Short Term Loan - Quick Business Financing**

**What is Short Term Loan?**
Fast, flexible financing solution for immediate business needs. Perfect for inventory purchases, operational expenses, or bridging cash flow gaps.

**Key Benefits:**
• 💰 ₹50,000 to ₹10 lakhs funding
• ⚡ Quick approval within 24 hours
• 📱 100% digital application process
• 🔄 Flexible repayment (3-12 months)
• 💳 Minimal documentation required

**Perfect For:**
🏪 Inventory purchase | 💼 Working capital | ⚡ Emergency funding

**What would you like to know about Short Term Loan?**
• **"eligibility"** - Requirements and criteria
• **"process"** - Application steps
• **"fees"** - Transparent pricing"""
        elif "empcash" in intent_name or state.product_focus == "empcash":
            return """💰 **EmpCash - Your Salary, When You Need It Most**

**What is EmpCash?**
Salary advance solution for employees to access their earnings before payday. Perfect for emergency expenses without long-term debt.

**Key Benefits:**
• 💵 Up to 50% of earned salary
• ⚡ Instant approval in minutes
• 🏦 Funds credited within 2 hours
• 🔄 Auto-deducted from next paycheck
• 📈 No impact on credit score

**Perfect For:**
🚑 Medical emergencies | 💡 Bill payments | 👨‍👩‍👧‍👦 Family needs | 📚 Education expenses

Want to know about **eligibility**, **process**? 💼"""
        elif "lease rental" in intent_name or "lrd" in intent_name or state.product_focus == "lrd":
            return """🏠 **LRD - Lease Rental Discounting**

**What is LRD?**
Property-backed financing solution that allows commercial property owners to unlock liquidity against their rental income streams.

**Key Benefits:**
• 🏢 Finance up to 70% of annual rental income
• 💰 Competitive rates for property-backed financing
• ⏰ Flexible tenure based on lease period
• 🔒 Secured financing with property collateral
• 📈 No prepayment penalties

**Perfect For:**
🏢 Commercial property owners | 💼 Business expansion | 💰 Working capital

**What would you like to know about LRD?**
• **eligibility** - Property and income requirements
• **process** - Application steps
• **fees** - Transparent pricing"""
        elif (("term_loan" in intent_name and "short_term" not in intent_name) or 
          ("ask_term_loan" == intent_name) or 
          (state.product_focus == "term_loan")):
            return """💼 **Term Loan - Long-Term Business Financing**

**What is Term Loan?**
Comprehensive business financing solution for substantial capital requirements, expansion projects, and long-term growth initiatives.

**Key Benefits:**
• 💰 ₹5 lakhs to ₹5 crores funding
• ⏰ Flexible tenure from 1-5 years
• 📈 Competitive EMI options
• 🏢 Suitable for established businesses
• 💳 No prepayment penalties

**Perfect For:**
🏭 Business expansion | 🏢 Equipment purchase | 📈 Working capital

**What would you like to know about Term Loan?**
• **eligibility** - Business requirements
• **process** - Application steps
• **fees** - Transparent pricing"""

        elif "supply_chain_finance" in intent_name or state.product_focus == "scf":
            return """🔗 **Supply Chain Finance - Complete Business Funding Suite**

**What is SCF?**
Comprehensive financing solutions for your entire supply chain. From vendor payments to dealer funding, we've got your business covered.

**Our SCF Services:**
• 📋 **Sales Bill Discounting** - Get cash against sales invoices
• 🛒 **Purchase Bill Discounting** - Pay suppliers early
• 🏭 **Vendor Finance** - Support your suppliers
• 🏪 **Dealer Finance** - Fund your dealers
• ⚡ **Early Payment Finance** - Optimize payment cycles

**Key Benefits:**
• 💰 Up to 95% of invoice value
• ⚡ Quick processing (24-48 hours)
• 📊 Flexible repayment terms
• 🔒 Secure and compliant

Which SCF service interests you most? 💼"""

        elif "imark" in intent_name or state.product_focus == "imark":
            return """📊 **iMark - AI-Powered Credit Rating for MSMEs**

**What is iMark?**
Advanced AI-driven credit rating system specifically designed for MSMEs. Get comprehensive creditworthiness assessment to improve your access to finance.

**Key Benefits:**
• 🤖 AI-powered analysis of multiple data points
• 📈 Industry-standard credit rating scale
• 📊 Detailed credit assessment report
• 💼 Improves access to better financing terms
• ⚡ Quick turnaround time

**Perfect For:**
🏢 MSME businesses | 📈 Credit improvement | 💰 Better loan terms

**What would you like to know about iMark?**
• **"eligibility"** - Who can apply
• **"process"** - How it works
• **"fees"** - Pricing details"""

        
        elif "insurance_claim" in intent_name or "icf" in intent_name.lower() or state.product_focus =="icf":            return """🏥 **ICF - Insurance Claim Finance**

**What is ICF?**
Healthcare financing solution that provides immediate cash flow to hospitals against pending insurance claims.

**Key Benefits:**
• 💰 Finance up to 80% of claim value
• ⚡ Funds transferred within 24-48 hours
• 🏥 For NABH/NABL certified hospitals
• 📋 No collateral required
• 🔄 Flexible terms based on claim settlement

**What would you like to know about ICF?**
• **"eligibility"** - Hospital requirements
• **"process"** - Application steps
• **"fees"** - Transparent pricing"""
        else:
            return "I'd be happy to provide detailed information! Which product would you like to know about?"
    
    def _get_declaration_response(self, state: MinimalConversationState) -> str:
        """Handle user type declarations."""
        
        if state.user_type.value == "individual":
            return """Perfect! 👤 **Individual Financial Solutions**

I can help you with:
💰 **EmpCash** - Salary advance for salaried employees (up to 50% salary)
🎯 **GigCash** - Funding for gig workers & freelancers (up to 50% earnings)

Both offer:
• ⚡ Quick approval (minutes)
• 💸 Fast funding (2 hours)
• 🔄 Automatic repayment
• 📱 100% digital process

Which solution fits your situation better? 🤔"""

        elif state.user_type.value == "business":
            return """Excellent! 🏢 **Business Financial Solutions**

We offer comprehensive funding for your business:

🔗 **Supply Chain Finance** - Invoice financing, bill discounting
🏥 **Insurance Claim Finance** - Quick cash for hospitals  
🏠 **Lease Rental Discounting** - Property-backed financing
📊 **iMark** - AI-powered credit rating for MSMEs
💼 **Term Loans** - Long-term business expansion funding
⚡ **Short-term Loans** - Quick working capital solutions

Which type of funding does your business need? 💼"""

        elif state.user_type.value == "lender":
            return """Welcome! 🏦 **Lender Partnership Opportunities**

**BillMart Lender Advantages:**
• 📊 Deal flow from 23,000+ screened invoices
• 🤖 API integration for automated bidding
• 📈 Granular risk data for informed decisions
• 🔒 ISO-27001 & SOC-2 compliant infrastructure
• 💰 Consistent deal flow across multiple sectors

**Next Steps:**
📄 View our **deal-flow presentation**
☎️ Speak with our **capital markets team**
🤝 Discuss **partnership terms**

Which would you prefer? 💼"""
        
        else:
            return "Thanks for that information! How can I assist you today? 😊"
    
    def _get_loan_need_response(self, state: MinimalConversationState) -> str:
        """Handle general loan inquiries - ALWAYS ask for clarification."""
        
        return """I'd love to help you find the perfect funding solution! 💡

To guide you to the right product, please tell me:

👤 **Individual** - Personal funding needs (salary advance, gig work funding)
🏢 **Business** - Company funding needs (working capital, growth funding)  
🏦 **Lender/NBFC** - Investment opportunities

Which category describes you best? 🎯"""
    
    def _get_smart_fallback_response(self, state: MinimalConversationState, user_message: str) -> str:
        """Context-aware fallback that prioritizes PRODUCT context over USER TYPE."""
        
        user_lower = user_message.lower()
        
        # PRIORITY 1: Product-focused queries (regardless of user type)
        if state.product_focus and state.product_focus != "lender_services":
            
            # Product eligibility questions
            if any(word in user_lower for word in ["eligibility", "eligible", "qualify", "requirement"]):
                return self._get_eligibility_response(state)
            
            # Product process questions  
            if any(word in user_lower for word in ["process", "steps", "how", "procedure"]):
                return self._get_process_response(state)
            
            # Product information questions
            if any(word in user_lower for word in ["what is", "what's", "tell me about", "info", "details"]):
                return self._get_product_info_response(f"ask_{state.product_focus}_info", state)
        
        # PRIORITY 2: Affirmation handling with context
        if any(word in user_lower for word in ["yes", "yeah", "ok", "sure", "proceed"]):
            return self._handle_affirmation_with_context(state)
        
        # PRIORITY 3: Lender-specific queries (only for actual lender services)
        if state.user_type.value == "lender" and (state.product_focus == "lender_services" or not state.product_focus):
            if any(word in user_lower for word in ["deal", "flow", "partnership", "invest"]):
                return """📊 **BillMart Deal Flow Information:**

    We provide:
    • **Verified deal pipeline** from 23k+ invoices
    • **Real-time bidding** opportunities  
    • **Risk assessment** data
    • **API integration** for automation

    📞 **Next Steps:** Contact our capital markets team at partnerships@billmart.com

    What specific aspect would you like to know more about?"""
        
        # PRIORITY 4: Generic contextual help
        return f"""I'm here to help! Based on our conversation, I can provide more details about:

    • **{state.product_focus or 'Our Products'}** - Features and benefits
    • **Eligibility** - Requirements and criteria
    • **Process** - Application steps
    • **Fees** - Transparent pricing

    📞 **Direct Contact:** +91 93269 46663 | care@billmart.com

    What would you like to know? 😊"""

    def _handle_affirmation_with_context(self, state: MinimalConversationState) -> str:
        """Handle 'yes' responses based on conversation context."""
        
        if state.product_focus == "gigcash":
            return self._get_eligibility_response(state)
        elif state.product_focus == "empcash":
            return self._get_eligibility_response(state)
        elif state.user_type.value == "lender":
            return """Perfect! Let me connect you with our team:

    📞 **Capital Markets:** partnerships@billmart.com
    📱 **Direct Line:** +91 93269 46663
    📄 **Deal Flow Deck:** Available upon request

    Would you prefer a call or email introduction?"""
        else:
            return "Great! How can I help you proceed? Please let me know what specific information you need."

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from typing import Text, Dict, Any, List

# === FEES ===
class ActionProvideFeesInfo(Action):
    def name(self) -> Text:
        return "action_provide_fees_info"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Get product from conversation state or slot
        product = tracker.get_slot("product_name")
        if not product:
            state = tracker.get_slot("conversation_state") or {}
            product = state.get("product_focus") if isinstance(state, dict) else None
        
        fees_map = {
            "empcash": (
                "💰 **EmpCash Fees:**\n"
                "• Transparent processing fee (shown before you confirm)\n"
                "• Fair interest rate based on employer and salary profile\n"
                "• No hidden charges\n"
                "• Auto-deduction from salary\n"
                "• Interest rates vary by employer partnership and your profile\n"
                "• All fees disclosed upfront during application\n"
                "Contact us for your exact fee structure based on your employer."
            ),
            "gigcash": (
                "🎯 **GigCash Fees:**\n"
                "• Upfront interest rate and minimal processing fee\n"
                "• All charges are shown before you confirm\n"
                "• No hidden fees or surprise charges\n"
                "• Auto-repay from platform earnings\n"
                "• Competitive rates for gig workers\n"
                "• Flexible repayment aligned with your earning cycles\n"
                "Apply to see your personalized rate based on platform performance."
            ),
            "scf": (
                "🔗 **SCF Fees:**\n"
                "• Discounting fee based on invoice amount and tenor\n"
                "• Processing fee (one-time, minimal)\n"
                "• No hidden charges\n"
                "• GST applicable as per law\n"
                "• Competitive rates for invoice financing\n"
                "• Fees vary by anchor strength and invoice quality\n"
                "• Transparent pricing with no surprise costs\n"
                "Contact us for rate quotes based on your specific invoices."
            ),
            "icf": (
                "🏥 **ICF Fees:**\n"
                "• Processing fee based on claim value\n"
                "• Interest charged until claim is settled\n"
                "• No prepayment penalty\n"
                "• All fees disclosed upfront\n"
                "• Competitive rates for healthcare financing\n"
                "• Flexible terms based on claim settlement timeline\n"
                "• No hidden charges or administrative fees\n"
                "Contact us for pricing based on your pending claims."
            ),
            "short_term_loan": (
                "⚡ **Short Term Loan Fees:**\n"
                "• Processing fee (one-time, competitive)\n"
                "• Interest charged on reducing balance\n"
                "• No hidden charges\n"
                "• Quick approval and disbursement\n"
                "• Flexible repayment options\n"
                "• Transparent pricing structure\n"
                "Contact us for detailed fee structure based on your requirements."
            ),
            "term_loan": (
                "💼 **Term Loan Fees:**\n"
                "• Processing fee (one-time)\n"
                "• Interest rate based on tenure and risk assessment\n"
                "• No hidden charges\n"
                "• Competitive EMI options\n"
                "• Flexible tenure up to 5 years\n"
                "• No prepayment penalties\n"
                "Contact us for detailed pricing based on your business profile."
            ),
            "imark": (
                "📊 **iMark Fees:**\n"
                "• Nominal fee for comprehensive credit rating report\n"
                "• AI-powered analysis at competitive rates\n"
                "• Detailed credit assessment and recommendations\n"
                "• One-time fee, no recurring charges\n"
                "• Industry-standard pricing for MSME credit rating\n"
                "Contact us for latest pricing and package details."
            ),
            "lrd": (
                "🏠 **LRD Fees:**\n"
                "• Processing fee based on loan amount\n"
                "• Interest rate based on lease value and property assessment\n"
                "• No hidden charges\n"
                "• Competitive rates for property-backed financing\n"
                "• Flexible tenure based on lease period\n"
                "• No prepayment penalties\n"
                "Contact us for detailed pricing based on your property portfolio."
            ),
            "lender_services": (
                "🏦 **Lender Services Fees:**\n"
                "• No onboarding fee for verified institutions\n"
                "• Platform usage fee as per deal volume\n"
                "• Transparent fee structure with no hidden costs\n"
                "• API integration and technical support included\n"
                "• Competitive rates for deal flow access\n"
                "• Volume-based discounts available\n"
                "Contact our capital markets team for detailed partnership fees."
            )
        }
        
        if product and product.lower() in fees_map:
            dispatcher.utter_message(text=fees_map[product.lower()])
        else:
            dispatcher.utter_message(text="Please specify which product's fees you want to know about (e.g., EmpCash, GigCash, SCF, ICF, Short Term Loan, Term Loan, iMark, LRD).")
        return []

# === ELIGIBILITY ===
class ActionProvideEligibilityInfo(Action):
    def name(self) -> Text:
        return "action_provide_eligibility_info"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        product = tracker.get_slot("product_name")
        if not product:
            state = tracker.get_slot("conversation_state") or {}
            product = state.get("product_focus") if isinstance(state, dict) else None
        
        eligibility_map = {
            "empcash": (
                "💰 **EmpCash Eligibility:**\n"
                "👔 Salaried employee at a BillMart partner company\n"
                "🏢 Company must meet BillMart's sector and size criteria\n"
                "⏰ Minimum 3 months continuous employment preferred\n"
                "📄 Valid KYC documents (Aadhar, PAN)\n"
                "🏦 Active salary account with regular credits\n"
                "💳 No existing salary advances or pending dues\n"
                "📈 Good credit history and repayment track record\n"
                "💰 Minimum monthly salary of ₹15,000\n"
                "🎯 Access up to 50% of earned salary\n"
                "Want to check if your company is registered with us?"
            ),
            "gigcash": (
                "🎯 **GigCash Eligibility:**\n"
                "🚗 Active gig worker on platforms like Uber, Ola, Zomato, Swiggy, Dunzo\n"
                "⏳ Minimum 3 months consistent earnings history\n"
                "📊 Verified platform ratings (typically 4+ stars)\n"
                "📄 Valid KYC documents (Aadhar, PAN)\n"
                "🏦 Active bank account linked to gig platform payouts\n"
                "💰 Minimum average monthly earnings of ₹15,000\n"
                "📈 No history of default or fraud\n"
                "🎯 Access up to 50% of monthly earnings\n"
                "🔄 Flexible repayment options aligned with platform payouts\n"
                "Want to check your specific eligibility based on your platform?"
            ),
            "scf": (
                "🔗 **Supply Chain Finance (SCF) Eligibility:**\n"
                "🏢 GST-registered business with valid registration documents\n"
                "📄 Valid GST invoices not older than 3 months\n"
                "💰 Minimum invoice amount of ₹50,000\n"
                "⏳ Business operational for at least 1 year\n"
                "📊 Positive credit history and financial statements\n"
                "🤝 Established buyer-supplier relationships\n"
                "📈 No ongoing legal or financial disputes\n"
                "💼 Annual turnover of ₹1 crore+\n"
                "🎯 Finance up to 95% of invoice value\n"
                "Want to check your business eligibility for invoice financing?"
            ),
            "icf": (
                "🏥 **Insurance Claim Finance (ICF) Eligibility:**\n"
                "🏥 NABH/NABL certified hospital or healthcare provider\n"
                "📄 Valid insurance empanelment and claim documentation\n"
                "⏳ Minimum 2 years of operational history\n"
                "💰 Pending insurance claims of at least 30 days\n"
                "📊 Good claim settlement history and TPA approvals\n"
                "🤝 No ongoing insurance disputes or litigation\n"
                "💼 Minimum claim value of ₹1 lakh\n"
                "🎯 Finance up to 80% of claim value\n"
                "🔄 Flexible financing options based on claim value\n"
                "Want to improve your hospital's cash flow with claim financing?"
            ),
            "short_term_loan": (
                "⚡ **Short Term Loan Eligibility:**\n"
                "👤 Individuals, MSMEs, and small businesses with urgent financial needs\n"
                "📄 Valid KYC and business registration documents\n"
                "💳 Demonstrated ability to repay within short tenure (3-12 months)\n"
                "📈 Positive credit history or guarantor support\n"
                "⏳ Clear loan purpose that is verifiable\n"
                "🏢 For businesses: Minimum 1 year operations\n"
                "💰 Loan amount from ₹50,000 to ₹10 lakhs\n"
                "🎯 Quick approval and disbursement within 24-48 hours\n"
                "Contact us for detailed eligibility assessment."
            ),
            "term_loan": (
                "💼 **Term Loan Eligibility:**\n"
                "🏢 Established business with at least 2 years of operations\n"
                "📄 Complete financial statements and tax returns\n"
                "💳 Good credit score (CIBIL 650+) and repayment history\n"
                "📈 Clear business plan and loan utilization strategy\n"
                "🤝 Collateral or security as per loan amount\n"
                "💰 Annual turnover of ₹50 lakhs+\n"
                "🎯 Loan amount from ₹5 lakhs to ₹5 crores\n"
                "⏰ Flexible tenure from 1-5 years\n"
                "📊 Detailed business projections and cash flow statements\n"
                "Contact us for comprehensive eligibility evaluation."
            ),
            "imark": (
                "📊 **iMark Eligibility:**\n"
                "🏢 MSME business with valid registration (Udyog Aadhar/MSME)\n"
                "📄 Submission of financial statements and business documents\n"
                "📊 Credit history and payment behavior analysis\n"
                "🤝 No ongoing legal or financial disputes\n"
                "⏳ Minimum 1 year business operations\n"
                "💼 Annual turnover between ₹1 crore to ₹250 crores\n"
                "🎯 AI-powered credit rating based on multiple data points\n"
                "📈 Comprehensive business and financial analysis\n"
                "Contact us to initiate your credit rating process."
            ),
            "lrd": (
                "🏠 **Lease Rental Discounting (LRD) Eligibility:**\n"
                "🏢 Ownership of commercial property with valid lease agreements\n"
                "📄 Lease rental income documentation (minimum 6 months)\n"
                "💳 Good credit history and repayment capacity\n"
                "📈 Property valuation and legal clearances\n"
                "🤝 Established tenants with good credit profiles\n"
                "💰 Minimum monthly rental income of ₹50,000\n"
                "⏰ Lease tenure of at least 3 years remaining\n"
                "🎯 Finance up to 70% of annual rental income\n"
                "📊 Property in prime commercial locations\n"
                "Contact us for property-specific eligibility assessment."
            ),
            "lender_services": (
                "🏦 **Lender Services Eligibility:**\n"
                "🏦 Registered NBFC, bank, or financial institution\n"
                "📄 Valid regulatory approvals and licenses (RBI/SEBI)\n"
                "🤝 Willingness to participate in deal flow and automated bidding\n"
                "📈 Access to capital and robust risk management capabilities\n"
                "💰 Minimum investable corpus of ₹10 crores\n"
                "📊 Strong credit evaluation and underwriting processes\n"
                "🎯 API integration capabilities for seamless operations\n"
                "⚡ Quick decision-making and fund disbursement abilities\n"
                "🔒 Compliance with data security and regulatory requirements\n"
                "Contact our capital markets team to explore partnership opportunities."
            )
        }

        if product and product.lower() in eligibility_map:
            dispatcher.utter_message(text=eligibility_map[product.lower()])
        else:
            dispatcher.utter_message(text="Please specify which product's eligibility you want to know about (e.g., EmpCash, GigCash, SCF, ICF, Short Term Loan, Term Loan, iMark, LRD).")
        return []

# === PROCESS ===
class ActionProvideProcessInfo(Action):
    def name(self) -> Text:
        return "action_provide_process_info"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        product = tracker.get_slot("product_name")
        if not product:
            state = tracker.get_slot("conversation_state") or {}
            product = state.get("product_focus") if isinstance(state, dict) else None
        
        process_map = {
            "empcash": (
                "💰 **EmpCash Application Process:**\n"
                "1. **Employee Verification** - Confirm your employer is a BillMart partner\n"
                "2. **Salary Verification** - Link your salary account for verification\n"
                "3. **Calculate Limit** - See your advance amount (up to 50% earned salary)\n"
                "4. **Apply** - Request advance through our secure platform\n"
                "5. **Instant Approval** - Get approved in minutes with AI-powered assessment\n"
                "6. **Receive Funds** - Money credited within 2 hours to your account\n"
                "7. **Auto-Deduction** - Repaid automatically from your next salary\n"
                "8. **Track Status** - Monitor your application and repayment through the app\n"
                "Want to check if your employer is a partner? 📞 +91 93269 46663"
            ),
            "gigcash": (
                "🎯 **GigCash Application Process:**\n"
                "1. **Connect Platform** - Link your gig work account (Uber, Zomato, etc.)\n"
                "2. **Verify Earnings** - We verify your last 3-6 months earnings history\n"
                "3. **Check Eligibility** - See your advance limit (up to 50% monthly earnings)\n"
                "4. **Apply** - Request the amount you need through our digital platform\n"
                "5. **AI Assessment** - Quick eligibility check based on platform performance\n"
                "6. **Get Funded** - Money in your account within 2 hours of approval\n"
                "7. **Auto-Repay** - Deducted automatically from your next platform earnings\n"
                "8. **Flexible Options** - Multiple repayment cycles aligned with your work\n"
                "Ready to get started? 🚀 Apply now for instant funding."
            ),
            "scf": (
                "🔗 **Supply Chain Finance Process:**\n"
                "1. **Anchor Evaluation** - The buyer company is evaluated and approved\n"
                "2. **Vendor/Dealer Onboarding** - Suppliers are evaluated and approved\n"
                "3. **Limit Setup** - Credit limit is sanctioned for the anchor relationship\n"
                "4. **Transaction Initiation** - Either party uploads invoice to our platform\n"
                "5. **Verification & Approval** - GST validation and compliance checks\n"
                "6. **Disbursement** - Funds disbursed directly to the supplier\n"
                "7. **Repayment** - Buyer repays as per agreed payment terms\n"
                "8. **Ongoing Monitoring** - Continuous risk assessment and limit management\n"
                "Which specific SCF service interests you? 💼 Sales/Purchase Bill Discounting, Vendor Finance, or Dealer Finance?"
            ),
            "icf": (
                "🏥 **Insurance Claim Finance Process:**\n"
                "1. **Hospital Verification** - Confirm NABH/NABL certification and empanelment\n"
                "2. **Claim Documentation** - Submit pending insurance claims with TPA acknowledgment\n"
                "3. **Verification** - We verify claim validity, amounts, and settlement probability\n"
                "4. **Quick Approval** - Fast approval based on claim strength and hospital profile\n"
                "5. **Disbursement** - Funds transferred within 24-48 hours to hospital account\n"
                "6. **Claim Settlement** - Repayment when insurance company settles the claim\n"
                "7. **Ongoing Support** - Assistance with claim follow-up and documentation\n"
                "8. **Flexible Terms** - Customized financing based on claim settlement timeline\n"
                "Ready to improve your hospital's cash flow? 🏥 Contact us for assessment."
            ),
            "short_term_loan": (
                "⚡ **Short Term Loan Process:**\n"
                "1. **Application** - Submit loan application with required documents\n"
                "2. **Quick Assessment** - Fast eligibility and creditworthiness evaluation\n"
                "3. **Verification** - KYC verification and credit checks\n"
                "4. **Approval** - Quick approval process within 24 hours\n"
                "5. **Documentation** - Minimal paperwork and digital agreement\n"
                "6. **Disbursement** - Funds transferred promptly to your account\n"
                "7. **Repayment** - Flexible repayment options (3-12 months)\n"
                "8. **Support** - Ongoing customer support throughout loan tenure\n"
                "Contact us for immediate funding solutions with competitive rates."
            ),
            "term_loan": (
                "💼 **Term Loan Process:**\n"
                "1. **Application** - Submit detailed business plan and financial documents\n"
                "2. **Credit Evaluation** - Comprehensive credit and business assessment\n"
                "3. **Due Diligence** - Detailed verification of business and financials\n"
                "4. **Approval** - Loan amount, tenure, and terms finalized\n"
                "5. **Documentation** - Comprehensive loan agreement and security documentation\n"
                "6. **Disbursement** - Funds transferred as per agreement and milestones\n"
                "7. **Monitoring** - Ongoing relationship management and periodic reviews\n"
                "8. **Repayment** - Structured EMI payments with flexible prepayment options\n"
                "Contact us for long-term business financing solutions."
            ),
            "imark": (
                "📊 **iMark Credit Rating Process:**\n"
                "1. **Application** - Submit business and financial documents\n"
                "2. **Data Collection** - Comprehensive business and financial data gathering\n"
                "3. **AI Analysis** - Advanced algorithms analyze multiple data points\n"
                "4. **Risk Assessment** - Detailed creditworthiness and risk evaluation\n"
                "5. **Rating Generation** - AI-powered credit rating on industry-standard scale\n"
                "6. **Report Preparation** - Detailed credit rating report with recommendations\n"
                "7. **Report Delivery** - Comprehensive credit rating report provided\n"
                "8. **Ongoing Monitoring** - Optional periodic rating updates and alerts\n"
                "Contact us to initiate your comprehensive credit rating process."
            ),
            "lrd": (
                "🏠 **Lease Rental Discounting Process:**\n"
                "1. **Property Evaluation** - Comprehensive property and location assessment\n"
                "2. **Lease Verification** - Detailed verification of lease agreements and tenants\n"
                "3. **Legal Due Diligence** - Property title verification and legal clearances\n"
                "4. **Credit Assessment** - Evaluation of property owner's repayment capacity\n"
                "5. **Valuation** - Professional property valuation and rental assessment\n"
                "6. **Approval** - Loan terms and amount finalized based on rental income\n"
                "7. **Documentation** - Comprehensive loan and security documentation\n"
                "8. **Disbursement** - Funds transferred against property and rental security\n"
                "Contact us for property-backed financing solutions."
            ),
            "lender_services": (
                "🏦 **Lender Partnership Process:**\n"
                "1. **Partner Onboarding** - Complete registration and regulatory compliance verification\n"
                "2. **Due Diligence** - Comprehensive evaluation of lending capabilities and track record\n"
                "3. **API Integration** - Technical integration for seamless deal flow access\n"
                "4. **Deal Flow Access** - Access to verified invoices and lending opportunities\n"
                "5. **Automated Bidding** - Participate in real-time bidding for deals\n"
                "6. **Risk Assessment** - Access to detailed risk data and credit assessments\n"
                "7. **Funding** - Disburse funds directly to borrowers as per agreements\n"
                "8. **Ongoing Support** - Continuous partnership support and deal flow management\n"
                "Contact our capital markets team for detailed partnership onboarding."
            )
        }
        
        if product and product.lower() in process_map:
            dispatcher.utter_message(text=process_map[product.lower()])
        else:
            dispatcher.utter_message(text="Please specify which product's process you want to know about (e.g., EmpCash, GigCash, SCF, ICF, Short Term Loan, Term Loan, iMark, LRD).")
        return []

# === REQUIREMENTS ===
class ActionProvideRequirementsInfo(Action):
    def name(self) -> Text:
        return "action_provide_requirements_info"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        product = tracker.get_slot("product_name")
        if not product:
            state = tracker.get_slot("conversation_state") or {}
            product = state.get("product_focus") if isinstance(state, dict) else None
        
        requirements_map = {
            "empcash": (
                "💰 **EmpCash Requirements:**\n"
                "📄 **Documents:** Last 3 payslips, 3 months bank statements, Aadhaar, PAN\n"
                "🏢 **Employment:** Salaried at BillMart partner company, 3+ months tenure\n"
                "💰 **Income:** Minimum ₹15,000 monthly salary\n"
                "🏦 **Banking:** Active salary account with regular credits\n"
                "📱 **Digital:** Smartphone with active mobile number\n"
                "🆔 **KYC:** Valid Aadhaar and PAN documents\n"
                "All documentation is 100% digital - no physical paperwork needed!"
            ),
            "gigcash": (
                "🎯 **GigCash Requirements:**\n"
                "📄 **Documents:** Platform earnings screenshots, 3 months bank statements, Aadhaar, PAN\n"
                "🚗 **Platform:** Active on Uber, Ola, Zomato, Swiggy, Dunzo, or similar platforms\n"
                "💰 **Earnings:** Minimum ₹15,000 monthly earnings, 3+ months history\n"
                "⭐ **Performance:** Good platform ratings (typically 4+ stars)\n"
                "🏦 **Banking:** Bank account linked to gig platform payouts\n"
                "📱 **Digital:** Smartphone with active mobile number\n"
                "Everything is digital - upload documents through our secure platform!"
            ),
            "scf": (
                "🔗 **SCF Requirements:**\n"
                "📄 **Documents:** GST registration, 6 months bank statements, invoices ≤3 months old, business registration\n"
                "🏢 **Business:** GST-registered, 1+ year operations, ₹1 crore+ annual turnover\n"
                "💰 **Invoice:** Minimum ₹50,000 invoice value, valid GST invoices\n"
                "🤝 **Relationships:** Established buyer-supplier relationships\n"
                "📊 **Financials:** Positive credit history, clean financial statements\n"
                "⚖️ **Legal:** No ongoing disputes or litigation\n"
                "Complete digital onboarding with API integration available!"
            ),
            "icf": (
                "🏥 **ICF Requirements:**\n"
                "📄 **Documents:** Hospital license, insurance empanelment certificates, pending claim documentation\n"
                "🏥 **Certification:** NABH/NABL certified hospital or healthcare provider\n"
                "⏳ **Operations:** Minimum 2 years operational history\n"
                "💰 **Claims:** Pending insurance claims ≥30 days, minimum ₹1 lakh value\n"
                "📊 **History:** Good claim settlement track record with TPAs\n"
                "🤝 **Empanelment:** Valid insurance company empanelment\n"
                "Digital claim verification and fast processing available!"
            ),
            "short_term_loan": (
                "⚡ **Short Term Loan Requirements:**\n"
                "📄 **Documents:** KYC documents, bank statements, income proof, business registration (if applicable)\n"
                "👤 **Eligibility:** Individuals, MSMEs, small businesses\n"
                "💰 **Amount:** ₹50,000 to ₹10 lakhs\n"
                "⏰ **Tenure:** 3-12 months repayment period\n"
                "📊 **Credit:** Positive credit history or guarantor support\n"
                "💼 **Purpose:** Clear and verifiable loan purpose\n"
                "Quick approval process with minimal documentation!"
            ),
            "term_loan": (
                "💼 **Term Loan Requirements:**\n"
                "📄 **Documents:** Complete financial statements, tax returns, business plan, collateral documents\n"
                "🏢 **Business:** 2+ years operations, ₹50 lakhs+ annual turnover\n"
                "💰 **Amount:** ₹5 lakhs to ₹5 crores\n"
                "⏰ **Tenure:** 1-5 years flexible repayment\n"
                "📊 **Credit:** CIBIL 650+, strong repayment capacity\n"
                "🤝 **Security:** Collateral as per loan amount\n"
                "Comprehensive business financing with competitive rates!"
            ),
            "imark": (
                "📊 **iMark Requirements:**\n"
                "📄 **Documents:** Financial statements, business registration, GST returns, bank statements\n"
                "🏢 **Business:** Valid MSME registration, 1+ year operations\n"
                "💰 **Turnover:** ₹1 crore to ₹250 crores annual turnover\n"
                "📊 **Data:** Complete business and financial data\n"
                "🤝 **Compliance:** No ongoing legal or financial disputes\n"
                "📈 **Analysis:** Comprehensive business performance data\n"
                "AI-powered credit rating with detailed analysis and recommendations!"
            ),
            "lrd": (
                "🏠 **LRD Requirements:**\n"
                "📄 **Documents:** Property papers, lease agreements, rental income proof, valuation report\n"
                "🏢 **Property:** Commercial property ownership with valid titles\n"
                "💰 **Rental:** Minimum ₹50,000 monthly rental income\n"
                "⏰ **Lease:** Minimum 3 years remaining lease tenure\n"
                "🤝 **Tenants:** Established tenants with good credit profiles\n"
                "📊 **Location:** Prime commercial locations preferred\n"
                "Property-backed financing up to 70% of annual rental income!"
            ),
            "lender_services": (
                "🏦 **Lender Services Requirements:**\n"
                "📄 **Documents:** Regulatory licenses, compliance certificates, financial statements\n"
                "🏦 **Registration:** Valid NBFC/bank registration with RBI/SEBI approvals\n"
                "💰 **Capital:** Minimum ₹10 crores investable corpus\n"
                "🤝 **Commitment:** Active participation in deal flow and bidding\n"
                "📊 **Capabilities:** Strong credit evaluation and risk management\n"
                "⚡ **Technology:** API integration capabilities for seamless operations\n"
                "Join India's leading digital lending marketplace with verified deal flow!"
            )
        }
        
        if product and product.lower() in requirements_map:
            dispatcher.utter_message(text=requirements_map[product.lower()])
        else:
            dispatcher.utter_message(text="Please specify which product's requirements you want to know about (e.g., EmpCash, GigCash, SCF, ICF, Short Term Loan, Term Loan, iMark, LRD).")
        return []

# === DOCUMENTS ===
class ActionProvideDocumentsInfo(Action):
    def name(self) -> Text:
        return "action_provide_documents_info"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        product = tracker.get_slot("product_name")
        if not product:
            state = tracker.get_slot("conversation_state") or {}
            product = state.get("product_focus") if isinstance(state, dict) else None
        
        documents_map = {
            "empcash": (
                "💰 **EmpCash Documents:**\n"
                "🆔 **Identity:** Aadhaar Card, PAN Card\n"
                "💼 **Employment:** Last 3 payslips, employment letter\n"
                "🏦 **Banking:** 3 months bank statements (salary account)\n"
                "📱 **Digital:** All documents uploaded through secure app\n"
                "✅ **Verification:** Employer registration with BillMart\n"
                "📄 **Format:** PDF/JPEG format, clear and readable\n"
                "Everything is 100% digital - no physical paperwork required!"
            ),
            "gigcash": (
                "🎯 **GigCash Documents:**\n"
                "🆔 **Identity:** Aadhaar Card, PAN Card\n"
                "📱 **Platform:** Earnings screenshots from gig platforms\n"
                "🏦 **Banking:** 3 months bank statements (platform-linked account)\n"
                "⭐ **Performance:** Platform rating screenshots\n"
                "🚗 **Registration:** Vehicle registration (for delivery partners)\n"
                "📄 **Format:** PDF/JPEG format, clear and readable\n"
                "Digital upload through our secure platform - quick and easy!"
            ),
            "scf": (
                "🔗 **SCF Documents:**\n"
                "🆔 **Business:** GST certificate, business registration, PAN\n"
                "🏦 **Financial:** 6 months bank statements, financial statements\n"
                "📄 **Invoices:** Valid GST invoices ≤3 months old\n"
                "🤝 **Agreements:** Purchase orders, supply agreements\n"
                "📊 **Compliance:** GST returns, audit reports\n"
                "⚖️ **Legal:** No objection certificates, legal clearances\n"
                "API integration available for bulk document processing!"
            ),
            "icf": (
                "🏥 **ICF Documents:**\n"
                "🆔 **Hospital:** NABH/NABL certificates, hospital license\n"
                "🏥 **Insurance:** Empanelment certificates from insurance companies\n"
                "📄 **Claims:** Pending claim documentation, TPA acknowledgments\n"
                "🏦 **Financial:** Bank statements, financial statements\n"
                "📊 **Operations:** Hospital registration, operational licenses\n"
                "💼 **Management:** Board resolutions, authorized signatory list\n"
                "Digital claim verification process for faster approvals!"
            ),
            "short_term_loan": (
                "⚡ **Short Term Loan Documents:**\n"
                "🆔 **Identity:** Aadhaar, PAN, address proof\n"
                "🏦 **Financial:** Bank statements, income proof\n"
                "💼 **Business:** Registration certificates (if applicable)\n"
                "📊 **Credit:** Credit bureau reports, existing loan statements\n"
                "🤝 **Guarantor:** Guarantor documents (if required)\n"
                "📄 **Purpose:** Loan utilization documents\n"
                "Minimal documentation for quick processing and approval!"
            ),
            "term_loan": (
                "💼 **Term Loan Documents:**\n"
                "🆔 **Business:** Registration certificates, MOA/AOA, partnership deed\n"
                "🏦 **Financial:** 3 years financial statements, tax returns, bank statements\n"
                "📊 **Project:** Detailed business plan, project reports\n"
                "🤝 **Collateral:** Property documents, security papers\n"
                "⚖️ **Legal:** Legal clearances, board resolutions\n"
                "💼 **Management:** KYC of directors/partners, experience certificates\n"
                "Comprehensive documentation for substantial business financing!"
            ),
            "imark": (
                "📊 **iMark Documents:**\n"
                "🆔 **Business:** MSME registration, GST certificate, PAN\n"
                "🏦 **Financial:** 2-3 years financial statements, bank statements\n"
                "📊 **Operations:** GST returns, audit reports, tax returns\n"
                "🤝 **Management:** KYC of directors/proprietors\n"
                "📈 **Performance:** Business performance data, client references\n"
                "⚖️ **Legal:** Legal clearances, compliance certificates\n"
                "AI analyzes comprehensive data for accurate credit rating!"
            ),
            "lrd": (
                "🏠 **LRD Documents:**\n"
                "🏢 **Property:** Sale deed, title documents, survey documents\n"
                "📄 **Lease:** Lease agreements, rental receipts\n"
                "🏦 **Financial:** Bank statements, income tax returns\n"
                "📊 **Valuation:** Property valuation report, approved plans\n"
                "⚖️ **Legal:** Legal opinion, encumbrance certificate\n"
                "🤝 **Tenants:** Tenant agreements, tenant financial profiles\n"
                "Property-backed financing with thorough due diligence!"
            ),
            "lender_services": (
                "🏦 **Lender Services Documents:**\n"
                "📄 **Registration:** RBI/SEBI registration certificates\n"
                "⚖️ **Compliance:** Regulatory compliance certificates\n"
                "🏦 **Financial:** Audited financial statements, capital adequacy ratios\n"
                "💼 **Management:** Board resolutions, authorized signatory list\n"
                "🤝 **Agreement:** Partnership agreement with BillMart\n"
                "📊 **Track Record:** Lending portfolio details, performance metrics\n"
                "Join our verified lender network with comprehensive onboarding!"
            )
        }
        
        if product and product.lower() in documents_map:
            dispatcher.utter_message(text=documents_map[product.lower()])
        else:
            dispatcher.utter_message(text="Please specify which product's documents you want to know about (e.g., EmpCash, GigCash, SCF, ICF, Short Term Loan, Term Loan, iMark, LRD).")
        return []

# === COLLATERAL ===
class ActionProvideCollateralInfo(Action):
    def name(self) -> Text:
        return "action_provide_collateral_info"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        product = tracker.get_slot("product_name")
        if not product:
            state = tracker.get_slot("conversation_state") or {}
            product = state.get("product_focus") if isinstance(state, dict) else None
        
        collateral_map = {
            "empcash": "💰 **EmpCash:** No collateral required. Financing is based on salary and employer partnership.",
            "gigcash": "🎯 **GigCash:** No collateral required. Financing is based on platform earnings and performance.",
            "scf": "🔗 **SCF:** Usually unsecured financing based on invoice strength and anchor creditworthiness. Some cases may require corporate guarantee.",
            "icf": "🏥 **ICF:** No collateral required. Financing is unsecured and based on pending insurance claims and hospital credentials.",
            "short_term_loan": "⚡ **Short Term Loan:** May require collateral or guarantor depending on loan amount and credit profile. Personal guarantee typically sufficient.",
            "term_loan": "💼 **Term Loan:** Collateral required for larger amounts. Acceptable security includes property, equipment, or corporate guarantee.",
            "imark": "📊 **iMark:** No collateral required. This is a credit rating service, not a financing product.",
            "lrd": "🏠 **LRD:** Commercial property serves as primary collateral. Loan secured against rental income and property value.",
            "lender_services": "🏦 **Lender Services:** No collateral required from lenders. Platform participation based on regulatory compliance and capital adequacy."
        }
        
        if product and product.lower() in collateral_map:
            dispatcher.utter_message(text=collateral_map[product.lower()])
        else:
            dispatcher.utter_message(text="Please specify which product's collateral requirements you want to know about (e.g., EmpCash, GigCash, SCF, ICF, Short Term Loan, Term Loan, iMark, LRD).")
        return []

# === DISBURSEMENT SPEED ===
class ActionProvideDisbursementSpeedInfo(Action):
    def name(self) -> Text:
        return "action_provide_disbursement_speed_info"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        product = tracker.get_slot("product_name")
        if not product:
            state = tracker.get_slot("conversation_state") or {}
            product = state.get("product_focus") if isinstance(state, dict) else None
        
        speed_map = {
            "empcash": "💰 **EmpCash:** Funds credited within 2 hours after approval. Instant approval for eligible employees.",
            "gigcash": "🎯 **GigCash:** Money in your account within 2 hours of approval. Quick processing for active gig workers.",
            "scf": "🔗 **SCF:** Disbursement in 24-48 hours after invoice approval and verification. API integration enables faster processing.",
            "icf": "🏥 **ICF:** Funds transferred within 24-48 hours after claim verification and approval.",
            "short_term_loan": "⚡ **Short Term Loan:** Quick disbursement within 24 hours of approval. Fast-track processing for urgent needs.",
            "term_loan": "💼 **Term Loan:** Disbursement within 3-5 working days after completion of documentation and legal formalities.",
            "imark": "📊 **iMark:** Credit rating report delivered within 3-5 working days of complete document submission.",
            "lrd": "🏠 **LRD:** Disbursement within 5-7 working days after property verification and legal clearances.",
            "lender_services": "🏦 **Lender Services:** Immediate access to deal flow upon completion of onboarding and API integration."
        }
        
        if product and product.lower() in speed_map:
            dispatcher.utter_message(text=speed_map[product.lower()])
        else:
            dispatcher.utter_message(text="Please specify which product's disbursement speed you want to know about (e.g., EmpCash, GigCash, SCF, ICF, Short Term Loan, Term Loan, iMark, LRD).")
        return []

class ActionHandleAffirm(Action):
    def name(self) -> Text:
        return "action_handle_affirm"
    
    def run(self, dispatcher, tracker, domain):
        # Get product context
        product_focus = tracker.get_slot("product_focus")
        state = tracker.get_slot("conversation_state") or {}
        conversation_phase = state.get("conversation_phase") if isinstance(state, dict) else None
        
        if product_focus and conversation_phase == "process":
            # User affirmed after seeing process info
            response = f"Perfect! Ready to apply for {product_focus.upper()}? I can also help you with:\n"
            response += "• **Eligibility** - Check if you qualify\n"
            response += "• **Documents** - What you'll need\n"
            response += "• **Fees** - Transparent pricing\n\n"
            response += "What would you like to know next?"
            dispatcher.utter_message(text=response)
        elif product_focus:
            # Generic affirmation with product context
            dispatcher.utter_message(text=f"Great! What else would you like to know about {product_focus.upper()}?")
        else:
            # No context - generic response
            dispatcher.utter_message(text="Great! Is there anything else I can help you with?")
        return []

class ActionSmartSessionHandler(Action):
    def name(self) -> Text:
        return "action_smart_session_handler"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get the latest user message
        latest_message = tracker.latest_message.get('text', '').lower()
        
        # Check if this is a direct user message or a session start
        if latest_message == '/session_start':
            # This is a technical session initialization - don't greet
            print("🔧 Frontend session start- send greeting")
            dispatcher.utter_message(response="utter_greet")
            dispatcher.utter_message(response="utter_services_brief")
            return []
        
        # Check if user's first message is a greeting
        greeting_intents = ['greet', 'hello', 'hi']
        user_intent = tracker.latest_message.get('intent', {}).get('name', '')
        
        if user_intent in greeting_intents:
            # User greeted first - respond with greeting
            dispatcher.utter_message(response="utter_greet")
            dispatcher.utter_message(response="utter_services_brief")
        else:
            # User asked something specific - handle it directly without greeting
            print(f"🎯 User asked '{latest_message}' - handling directly")
        
        return []

class ActionSessionStart(Action):
    def name(self) -> Text:
        return "action_session_start"
    
    async def run(self, dispatcher , tracker, domain):
        session_data= self.initialize_session(tracker)
        greeting_tasks= [self.send_greeting(dispatcher), self.send_services_brief(dispatcher)]
        
        await asyncio.gather(*greeting_tasks)
        return [SlotSet("session_initlaized",True)]