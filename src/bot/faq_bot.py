import json
from datetime import datetime
from typing import Dict, List
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from translation.simple_translation_service import SimpleTranslationService

class SimpleFAQBot:
    def __init__(self):
        self.translator = SimpleTranslationService()
        self.conversations = {}
        
        # Load comprehensive BillMart knowledge base from JSON
        self.knowledge_base = self.load_knowledge_base()
        self.faq_database = self.create_faq_database()
        
        print(f"✅ BillMart FAQ Bot initialized with comprehensive knowledge base")

    def load_knowledge_base(self):
        """Load BillMart knowledge base from JSON file"""
        try:
            json_path = os.path.join("data", "billmart_complete_knowledge.json")
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print("❌ BillMart knowledge base file not found")
            return self.get_fallback_knowledge()
        except Exception as e:
            print(f"❌ Error loading knowledge base: {e}")
            return self.get_fallback_knowledge()

    def get_fallback_knowledge(self):
        """Fallback knowledge if JSON file not available"""
        return {
            "company_info": {
                "basic": {
                    "name": "BillMart FinTech Private Limited",
                    "business_model": "Digital marketplace connecting borrowers with financers",
                }
            },
            "general_responses": {
                "default": "I can help you with BillMart's services. Please ask about our products or company information."
            },
        }

    def create_faq_database(self):
        """Create searchable FAQ database from knowledge base - NO HARDCODING"""
        faq_db = {}

        try:
            # Company information - Safe access with .get()
            if "company_info" in self.knowledge_base:
                company = self.knowledge_base["company_info"]
                if "basic" in company:
                    basic = company["basic"]
                    faq_db["company information"] = (
                        f"{basic.get('name', 'BillMart')} - {basic.get('business_model', 'Fintech platform')}"
                    )
                    faq_db["billmart"] = basic.get(
                        "description",
                        basic.get("business_model", "Digital lending platform"),
                    )
                    faq_db["about billmart"] = basic.get(
                        "description",
                        basic.get("business_model", "Digital lending platform"),
                    )

                # Contact information
                if "contact" in company:
                    contact = company["contact"]
                    phone = contact.get("phone", "+91 93269 46663")
                    email = contact.get("email", {}).get("support", "care@billmart.com")
                    faq_db["contact information"] = f"Call {phone} or email {email}"

            # Products - Safe access
            if "products" in self.knowledge_base:
                products = self.knowledge_base["products"]

                # Business products
                if "business_products" in products:
                    bp = products["business_products"]

                    if "supply_chain_finance" in bp:
                        scf = bp["supply_chain_finance"]
                        desc = scf.get("description", "Supply Chain Finance")
                        min_amt = scf.get("minimum_amount", "Rs. 50,000")
                        req = scf.get(
                            "requirements", "GST bills not older than 3 months"
                        )
                        faq_db["supply chain finance"] = (
                            f"{desc}. Minimum: {min_amt}, Requirements: {req}"
                        )

                # Individual products
                if "individual_products" in products:
                    ip = products["individual_products"]

                    if "empcash" in ip:
                        emp = ip["empcash"]
                        desc = emp.get("description", "Employee salary advance")
                        target = emp.get("target", "Salaried employees")
                        limit = emp.get("amount_limit", "Up to 50% of salary")
                        faq_db["empcash"] = f"{desc}. Target: {target}, Limit: {limit}"

                    if "gigcash" in ip:
                        gig = ip["gigcash"]
                        desc = gig.get("description", "Gig worker financing")
                        target = gig.get("target", "Gig workers")
                        limit = gig.get("amount_limit", "Up to 50% of earnings")
                        faq_db["gigcash"] = f"{desc}. Target: {target}, Limit: {limit}"

            # Detailed FAQs - Direct mapping from JSON
            if "detailed_faqs" in self.knowledge_base:
                detailed = self.knowledge_base["detailed_faqs"]

                for category, faqs in detailed.items():
                    if isinstance(faqs, dict):
                        for faq_key, faq_answer in faqs.items():
                            # Convert underscore keys to searchable phrases
                            search_key = faq_key.replace("_", " ")
                            faq_db[search_key] = faq_answer

            # General responses
            if "general_responses" in self.knowledge_base:
                faq_db.update(self.knowledge_base["general_responses"])

            print(
                f"📚 Created FAQ database with {len(faq_db)} entries from JSON knowledge base"
            )
            return faq_db

        except Exception as e:
            print(f"❌ Error creating FAQ database: {e}")
            return {
                "default": "I can help you with BillMart's services. What would you like to know?"
            }

    def get_conversation_context(self, user_id: str, limit: int = 3) -> str:
        """Get recent conversation context for better responses"""
        if user_id not in self.conversations:
            return ""
        recent_messages = self.conversations[user_id][-limit * 2 :]
        context_parts = []
        for msg in recent_messages:
            if msg["type"] == "user":
                user_message = msg.get("original", msg.get("message", "Unknown"))
                context_parts.append(f"User previously asked: {user_message}")
            else:
                bot_message = msg.get(
                    "translated", msg.get("english", msg.get("message", "Unknown"))
                )
                context_parts.append(f"Bot responded: {bot_message[:100]}...")
        return " | ".join(context_parts)

    def find_faq_response(self, question: str, context: str = "") -> str:
        """Enhanced FAQ response with better intent recognition"""
        question_lower = question.lower()

        # Check for special commands first
        if any(
            word in question_lower for word in ["end chat", "goodbye", "bye", "finish"]
        ):
            return "END_CHAT_TRIGGER"

        if any(
            word in question_lower
            for word in ["demo", "connect", "talk to someone", "human", "executive"]
        ):
            return "REQUEST_DEMO_TRIGGER"

        # Enhanced intent recognition with scoring
        intent_scores = {}

        # Define intent keyword groups with priorities
        intent_keywords = {
            "supply_chain_finance": {
                "keywords": [
                    "supply chain finance",
                    "scf",
                    "b-scf", 
                    "invoice financing",
                    "bill discounting",
                    "vendor financing",
                ],
                "response_key": "supply chain finance",
            },
            "insurance_claim_finance": {
                "keywords": [
                    "insurance claim finance",
                    "icf",
                    "hospital financing",
                    "medical financing",
                    "claim delay",
                ],
                "response_key": "insurance claim finance",
            },
            "empcash": {
                "keywords": [
                    "empcash",
                    "emp cash",
                    "employee cash",
                    "salary advance",
                    "employee advance",
                ],
                "response_key": "empcash",
            },
            "gigcash": {
                "keywords": [
                    "gigcash",
                    "gig cash",
                    "freelancer financing",
                    "gig worker",
                    "uber",
                    "zomato",
                    "swiggy",
                ],
                "response_key": "gigcash",
            },
            "imark": {
                "keywords": [
                    "imark",
                    "ai rating",
                    "msme rating",
                    "credit rating",
                    "business rating",
                ],
                "response_key": "imark",
            },
            "company_info": {
                "keywords": ["billmart", "company", "about", "who are you"],
                "response_key": "company information",
            },
            "services": {
                "keywords": [
                    "services",
                    "products",
                    "offerings",
                    "what do you offer",
                    "solutions",
                ],
                "response_key": "services offered",
            },
            "contact": {
                "keywords": ["contact", "phone", "email", "address", "office"],
                "response_key": "contact information",
            },
        }

        # Score each intent based on keyword matches
        for intent_name, intent_data in intent_keywords.items():
            score = 0
            for keyword in intent_data["keywords"]:
                if keyword in question_lower:
                    # Longer matches get higher scores
                    score += len(keyword) * 2
                    # Exact matches get bonus points
                    if question_lower.strip() == keyword:
                        score += 10

            if score > 0:
                intent_scores[intent_name] = {
                    "score": score,
                    "response_key": intent_data["response_key"],
                }

        # Return highest scoring intent
        if intent_scores:
            best_intent = max(
                intent_scores, key=lambda x: intent_scores[x]["score"]
            )
            response_key = intent_scores[best_intent]["response_key"]

            # Get response from your JSON knowledge base
            if response_key in self.faq_database:
                return self.faq_database[response_key]

        # Fallback to original keyword matching for other intents
        for keyword, answer in self.faq_database.items():
            if keyword in question_lower:
                return answer

        # Context-aware responses
        if context:
            if "billmart" in context.lower() and any(
                word in question_lower
                for word in ["document", "paper", "need", "require"]
            ):
                reg_info = self.faq_database.get(
                    "how to register",
                    "KYC, GSTIN, CIN, Bank Details, MSME Registration and required documents",
                )
                return f"For BillMart registration: {reg_info}"

            if "empcash" in context.lower() and any(
                word in question_lower for word in ["how", "process", "work"]
            ):
                return "EmpCash process: Login → KYC → Apply for advance → Instant approval → Receive funds → Auto-repayment from paycheck."

        # Default response
        return self.faq_database.get(
            "default",
            "I can help you with BillMart's products and services including Supply Chain Finance, EmpCash, GigCash, company information, and registration process. What would you like to know?",
        )

    def handle_end_chat(self, user_id: str) -> str:
        """Clear conversation when user ends the chat"""
        if user_id in self.conversations:
            del self.conversations[user_id]
            print(f"🔄 Conversation cleared for user: {user_id}")
        return (
            "Thank you for chatting with BillMart! Feel free to reach out anytime at "
            "+91 93269 46663 or care@billmart.com. Have a great day!"
        )

    def handle_request_demo(self, user_id: str, user_message: str = "") -> str:
        """Handle demo request and notify team"""
        demo_request = {
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "user_message": user_message,
            "conversation_history": self.conversations.get(user_id, []),
        }

        self.save_demo_request(demo_request)

        return (
            "I'll connect you with our BillMart team for a personalized demo! "
            "Please call +91 93269 46663 or email care@billmart.com. "
            "Our team has been notified and will reach out to you shortly."
        )

    def save_demo_request(self, demo_request: dict):
        """Save demo request for team follow-up"""
        try:
            demo_file = "data/demo_requests.json"

            try:
                with open(demo_file, "r", encoding="utf-8") as f:
                    requests = json.load(f)
            except FileNotFoundError:
                requests = []

            requests.append(demo_request)

            os.makedirs(os.path.dirname(demo_file), exist_ok=True)
            with open(demo_file, "w", encoding="utf-8") as f:
                json.dump(requests, f, indent=2, ensure_ascii=False)

            print(f"📝 Demo request saved for user: {demo_request['user_id']}")

        except Exception as e:
            print(f"❌ Error saving demo request: {e}")

    def handle_message(self, user_id: str, message: str) -> str:
        """Process user message with translation and conversation memory"""
        try:
            if user_id not in self.conversations:
                self.conversations[user_id] = []

            detected_lang = self.translator.detect_language(message)

            if detected_lang != "english":
                english_message = self.translator.translate_text(
                    message, detected_lang, "english"
                )
            else:
                english_message = message

            self.conversations[user_id].append(
                {
                    "type": "user",
                    "original": message,
                    "english": english_message,
                    "language": detected_lang,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            context = self.get_conversation_context(user_id)
            english_response = self.find_faq_response(english_message, context)

            if english_response == "END_CHAT_TRIGGER":
                return self.handle_end_chat(user_id)
            elif english_response == "REQUEST_DEMO_TRIGGER":
                return self.handle_request_demo(user_id, message)

            if detected_lang != "english":
                final_response = self.translator.translate_text(
                    english_response, "english", detected_lang
                )
            else:
                final_response = english_response

            self.conversations[user_id].append(
                {
                    "type": "bot",
                    "english": english_response,
                    "translated": final_response,
                    "language": detected_lang,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            if len(self.conversations[user_id]) > 20:
                self.conversations[user_id] = self.conversations[user_id][-20:]

            return final_response

        except Exception as e:
            print(f"❌ Error processing message: {e}")
            return "I'm having trouble processing your request. Please try again."


# =====================================================
# COMPREHENSIVE TEST CODE (AT MODULE LEVEL - NOT INSIDE CLASS)
# =====================================================

if __name__ == "__main__":
    print("🚀 TESTING BILLMART FAQ BOT - JSON KNOWLEDGE BASE")
    print("=" * 70)

    # Initialize bot
    try:
        bot = SimpleFAQBot()
        print(f"✅ Bot initialization successful")
    except Exception as e:
        print(f"❌ Bot initialization failed: {e}")
        exit(1)

    # Test 1: Knowledge Base Loading
    print(f"\n📊 Knowledge Base Analysis:")
    print(f"   Knowledge loaded: {'✅ YES' if bot.knowledge_base else '❌ NO'}")
    print(f"   FAQ entries created: {len(bot.faq_database)}")

    # Show some FAQ entries
    print(f"   Sample FAQ keys: {list(bot.faq_database.keys())[:5]}")

    if "company_info" in bot.knowledge_base:
        print(f"   Company data: ✅ Loaded")
    if "products" in bot.knowledge_base:
        print(f"   Product data: ✅ Loaded")
    if "detailed_faqs" in bot.knowledge_base:
        print(f"   Detailed FAQs: ✅ Loaded")

    # Test 2: FAQ Response Tests (Multiple questions)
    print(f"\n💬 FAQ Response Tests:")
    print("-" * 50)

    test_questions = [
        "What is BillMart?",
        "Tell me about EmpCash",
        "What is supply chain finance?",
        "How do I contact you?",
        "What are your charges?",
        "Tell me about registration",
        "What is GigCash?",
        "How much can I borrow?",
    ]

    test_user = "test_user_123"

    for i, question in enumerate(test_questions, 1):
        print(f"\n{i}. 👤 User: {question}")
        try:
            response = bot.handle_message(test_user, question)
            print(
                f"   🤖 Bot: {response[:150]}{'...' if len(response) > 150 else ''}"
            )
        except Exception as e:
            print(f"   ❌ Error: {e}")

    # Test 3: Special Commands
    print(f"\n🎯 Special Commands Test:")
    print("-" * 30)

    print(f"\n👤 User: I want a demo")
    demo_response = bot.handle_message(test_user, "I want a demo")
    print(f"🤖 Bot: {demo_response[:100]}...")

    print(f"\n👤 User: End chat")
    end_response = bot.handle_message(test_user, "End chat")
    print(f"🤖 Bot: {end_response[:100]}...")

    # Test 4: Multilingual Test (if translation works)
    print(f"\n🌍 Multilingual Test:")
    print("-" * 25)

    try:
        hindi_question = "बिलमार्ट क्या है?"
        print(f"\n👤 User (Hindi): {hindi_question}")
        hindi_response = bot.handle_message("hindi_user", hindi_question)
        print(f"🤖 Bot (Hindi): {hindi_response[:100]}...")
    except Exception as e:
        print(f"❌ Multilingual test failed: {e}")

    # Test 5: Context Test
    print(f"\n🧠 Context Memory Test:")
    print("-" * 25)

    context_user = "context_test_user"

    print(f"\n👤 User: What is BillMart?")
    response1 = bot.handle_message(context_user, "What is BillMart?")
    print(f"🤖 Bot: {response1[:100]}...")

    print(f"\n👤 User: What documents do I need for that?")
    response2 = bot.handle_message(
        context_user, "What documents do I need for that?"
    )
    print(f"🤖 Bot: {response2[:100]}...")

    # Test 6: System Statistics
    print(f"\n📊 System Statistics:")
    print("-" * 20)
    print(f"   Active conversations: {len(bot.conversations)}")
    print(f"   FAQ database size: {len(bot.faq_database)} entries")

    # Check demo requests
    if os.path.exists("data/demo_requests.json"):
        try:
            with open("data/demo_requests.json", "r") as f:
                demo_requests = json.load(f)
            print(f"   Demo requests logged: {len(demo_requests)}")
        except:
            print(f"   Demo requests: File exists but couldn't read")
    else:
        print(f"   Demo requests: No file created yet")

    print(f"\n✅ COMPREHENSIVE TESTING COMPLETE!")
    print(f"🎯 Ready for Rasa integration next!")
    print("=" * 70)
