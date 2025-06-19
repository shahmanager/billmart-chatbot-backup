// Show/hide logic
document.getElementById('billmart-chatbot-launcher').onclick = function() {
  document.getElementById('billmart-chatbot-window').style.display = 'block';
  showFAQ();
};

function closeChatbot() {
  document.getElementById('billmart-chatbot-window').style.display = 'none';
}

// FAQ choices
const faqs = [
  { title: "What is GigCash?", payload: "/ask_gigcash_info" },
  { title: "How to apply for EmpCash?", payload: "/ask_empcash_info" },
  { title: "What documents are needed?", payload: "/ask_documents" }
  // Add more as needed
];

// Show FAQ options
function showFAQ() {
  const content = document.getElementById('billmart-chatbot-content');
  content.innerHTML = `
    <div style="margin-bottom:12px;font-weight:bold;">What do you want to know?</div>
    ${faqs.map(faq => `<button onclick="sendFAQ('${faq.payload}')" style="margin:4px 0;width:100%;padding:10px;border-radius:8px;border:1px solid #eee;background:#fff;cursor:pointer;">${faq.title}</button>`).join('')}
    <div style="margin-top:16px;"><button onclick="showChatInput()" style="width:100%;padding:10px;border-radius:8px;background:#f5f5f5;border:1px solid #eee;">Talk with Chatbot</button></div>
  `;
  document.getElementById('billmart-chatbot-input-area').style.display = 'none';
}

function showChatInput() {
  document.getElementById('billmart-chatbot-content').innerHTML = '';
  document.getElementById('billmart-chatbot-input-area').style.display = '';
}

// Send FAQ or quick reply
function sendFAQ(payload) {
  addUserMessage(faqs.find(f => f.payload === payload).title);
  sendToRasa(payload);
}

// Send user-typed message
function sendUserMessage() {
  const input = document.getElementById('billmart-chatbot-input');
  const message = input.value.trim();
  if (!message) return;
  addUserMessage(message);
  sendToRasa(message);
  input.value = '';
}

// Render user message
function addUserMessage(text) {
  const content = document.getElementById('billmart-chatbot-content');
  content.innerHTML += `<div style="text-align:right;margin:8px 0;"><span style="display:inline-block;background:#ff9100;color:#fff;padding:8px 12px;border-radius:12px;">${text}</span></div>`;
  content.scrollTop = content.scrollHeight;
}

// Render bot message and quick replies
function addBotMessage(text, buttons) {
  const content = document.getElementById('billmart-chatbot-content');
  content.innerHTML += `<div style="text-align:left;margin:8px 0;"><span style="display:inline-block;background:#eee;color:#222;padding:8px 12px;border-radius:12px;">${text}</span></div>`;
  if (buttons && buttons.length) {
    content.innerHTML += `<div style="margin:8px 0;">${buttons.map(b =>
      `<button onclick="sendFAQ('${b.payload}')" style="margin:2px 4px 0 0;padding:6px 12px;border-radius:8px;border:1px solid #ddd;background:#fff;cursor:pointer;">${b.title}</button>`
    ).join('')}</div>`;
  }
  content.scrollTop = content.scrollHeight;
}

// Send message to Rasa REST API
function sendToRasa(message) {
  fetch("http://localhost:5005/webhooks/rest/webhook", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      sender: "user_" + getSessionId(),
      message: message
    })
  })
  .then(res => res.json())
  .then(data => {
    data.forEach(msg => {
      addBotMessage(msg.text || "", msg.buttons || []);
    });
  });
}

// Simple session id for user
function getSessionId() {
  if (!window._billmartChatSession) {
    window._billmartChatSession = Math.random().toString(36).substring(2, 10);
  }
  return window._billmartChatSession;
}
