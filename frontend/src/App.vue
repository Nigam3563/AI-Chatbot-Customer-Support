<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { MessageCircle, Plus, Send, Bot, User, LoaderCircle } from 'lucide-vue-next'

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

const conversations = ref([])
const activeConversationId = ref(null)
const messages = ref([])
const input = ref('')
const loading = ref(false)
const error = ref('')
const messagesContainer = ref(null)

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  })

  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body.detail || `Request failed (${response.status})`)
  }

  return response.json()
}

async function loadConversations() {
  conversations.value = await request('/api/conversations')
}

async function createConversation() {
  error.value = ''

  try {
    const conversation = await request('/api/conversations', {
      method: 'POST',
      body: JSON.stringify({ title: 'New conversation' }),
    })

    conversations.value.unshift(conversation)
    activeConversationId.value = conversation.id
    messages.value = []
  } catch (e) {
    error.value = e.message
  }
}

async function selectConversation(conversation) {
  activeConversationId.value = conversation.id
  error.value = ''

  try {
    messages.value = await request(
      `/api/conversations/${conversation.id}/messages`,
    )
    await scrollToBottom()
  } catch (e) {
    error.value = e.message
  }
}

async function sendMessage() {
  const content = input.value.trim()

  if (!content || loading.value) return

  error.value = ''

  if (!activeConversationId.value) {
    await createConversation()
    if (!activeConversationId.value) return
  }

  input.value = ''
  loading.value = true

  try {
    const result = await request(
      `/api/conversations/${activeConversationId.value}/messages`,
      {
        method: 'POST',
        body: JSON.stringify({ content }),
      },
    )

    messages.value.push(...result)
    await loadConversations()
    await scrollToBottom()
  } catch (e) {
    error.value = e.message
    input.value = content
  } finally {
    loading.value = false
  }
}

async function scrollToBottom() {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop =
      messagesContainer.value.scrollHeight
  }
}

onMounted(async () => {
  try {
    await loadConversations()

    if (conversations.value.length) {
      await selectConversation(conversations.value[0])
    } else {
      await createConversation()
    }
  } catch (e) {
    error.value = e.message
  }
})
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-icon">
          <Bot :size="24" />
        </div>
        <div>
          <h2>Support AI</h2>
          <p>Customer assistant</p>
        </div>
      </div>

      <button class="new-chat" @click="createConversation">
        <Plus :size="18" />
        New conversation
      </button>

      <p class="section-label">YOUR CONVERSATIONS</p>

      <div class="conversation-list">
        <button v-for="conversation in conversations" :key="conversation.id" class="conversation-item"
          :class="{ active: activeConversationId === conversation.id }" @click="selectConversation(conversation)">
          <MessageCircle :size="17" />
          <span>{{ conversation.title }}</span>
        </button>
      </div>

      <div class="sidebar-footer">
        <span class="status-dot"></span>
        AI assistant ready
      </div>
    </aside>

    <main class="main-panel">
      <header class="topbar">
        <div>
          <h1>AI Customer Support</h1>
          <p>Ask a question and get help instantly.</p>
        </div>
        <div class="online-status">
          <span class="status-dot"></span>
          Online
        </div>
      </header>

      <section ref="messagesContainer" class="messages-area">
        <div v-if="messages.length === 0" class="welcome">
          <div class="welcome-icon">
            <Bot :size="34" />
          </div>
          <h2>How can I help you today?</h2>
          <p>Ask me about deliveries, orders, or customer support.</p>
          <button class="suggestion" @click="input = 'I need help with a delivery.'">
            I need help with a delivery
          </button>
          <button class="suggestion" @click="input = 'How can I track my order?'">
            How can I track my order?
          </button>
        </div>

        <div v-for="message in messages" :key="message.id" class="message-row" :class="message.role">
          <div class="avatar">
            <User v-if="message.role === 'user'" :size="18" />
            <Bot v-else :size="18" />
          </div>
          <div class="message-content">
            <span class="message-author">
              {{ message.role === 'user' ? 'You' : 'Support AI' }}
            </span>
            <div class="message-bubble">{{ message.content }}</div>
          </div>
        </div>

        <div v-if="loading" class="message-row assistant">
          <div class="avatar">
            <Bot :size="18" />
          </div>
          <div class="message-content">
            <span class="message-author">Support AI</span>
            <div class="message-bubble thinking">
              <LoaderCircle :size="17" class="spin" />
              Thinking...
            </div>
          </div>
        </div>
      </section>

      <div v-if="error" class="error-message">{{ error }}</div>

      <form class="composer" @submit.prevent="sendMessage">
        <input v-model="input" placeholder="Type your message..." aria-label="Your message" :disabled="loading" />
        <button type="submit" class="send-button" :disabled="!input.trim() || loading" aria-label="Send message">
          <Send :size="18" />
        </button>
      </form>

      <p class="disclaimer">
        AI-generated responses may not always be accurate.
      </p>
    </main>
  </div>
</template>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
  font-family: 'Inter', sans-serif;
  color: #202b3c;
  background: #f5f7fb;
  font-synthesis: none;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  min-width: 320px;
  min-height: 100vh;
}

button,
input {
  font: inherit;
}

button {
  cursor: pointer;
}

.app-shell {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: 280px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  padding: 26px 18px 18px;
  color: #e8eef8;
  background: #172338;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 8px 30px;
}

.brand-icon {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border-radius: 13px;
  color: white;
  background: #5367e8;
}

.brand h2 {
  margin: 0;
  font-size: 17px;
}

.brand p {
  margin: 5px 0 0;
  color: #a7b5ca;
  font-size: 12px;
}

.new-chat {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 9px;
  width: 100%;
  padding: 12px;
  border: 1px solid #45536a;
  border-radius: 10px;
  color: white;
  background: #29374d;
}

.new-chat:hover {
  background: #34445c;
}

.section-label {
  margin: 30px 8px 12px;
  color: #8f9eb5;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 1.2px;
}

.conversation-list {
  display: grid;
  gap: 6px;
}

.conversation-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 12px 10px;
  overflow: hidden;
  border: 0;
  border-radius: 9px;
  color: #c3cddd;
  background: transparent;
  text-align: left;
}

.conversation-item span {
  overflow: hidden;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conversation-item.active,
.conversation-item:hover {
  color: white;
  background: #2c3b52;
}

.sidebar-footer {
  display: flex;
  align-items: center;
  gap: 9px;
  margin-top: auto;
  padding: 18px 8px 4px;
  color: #b5c2d5;
  font-size: 12px;
  border-top: 1px solid #344258;
}

.status-dot {
  width: 8px;
  height: 8px;
  flex-shrink: 0;
  border-radius: 50%;
  background: #28bd85;
}

.main-panel {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-width: 0;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 15px;
  padding: 24px 36px;
  border-bottom: 1px solid #e6eaf1;
  background: white;
}

.topbar h1 {
  margin: 0;
  font-size: 19px;
  font-weight: 700;
}

.topbar p {
  margin: 7px 0 0;
  color: #7c8798;
  font-size: 12px;
}

.online-status {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #627083;
  font-size: 12px;
}

.messages-area {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 25px;
  padding: 34px max(24px, calc((100% - 780px) / 2));
  overflow-y: auto;
}

.welcome {
  margin: auto 0;
  text-align: center;
}

.welcome-icon {
  display: grid;
  place-items: center;
  width: 66px;
  height: 66px;
  margin: 0 auto 20px;
  border-radius: 20px;
  color: #5367e8;
  background: #e9ecff;
}

.welcome h2 {
  margin: 0;
  font-size: 23px;
}

.welcome p {
  margin: 12px 0 25px;
  color: #7d8797;
  font-size: 13px;
}

.suggestion {
  display: block;
  margin: 8px auto;
  padding: 11px 16px;
  border: 1px solid #e0e5ee;
  border-radius: 10px;
  color: #48566c;
  background: white;
  font-size: 12px;
}

.suggestion:hover {
  border-color: #5367e8;
}

.message-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.message-row.user {
  flex-direction: row-reverse;
}

.avatar {
  display: grid;
  place-items: center;
  width: 35px;
  height: 35px;
  flex-shrink: 0;
  border-radius: 11px;
  color: #5367e8;
  background: #e7eaff;
}

.user .avatar {
  color: white;
  background: #5367e8;
}

.message-content {
  max-width: min(80%, 650px);
}

.message-author {
  display: block;
  margin: 1px 0 8px;
  color: #657186;
  font-size: 11px;
  font-weight: 600;
}

.user .message-author {
  text-align: right;
}

.message-bubble {
  padding: 14px 16px;
  border: 1px solid #e6eaf1;
  border-radius: 4px 14px 14px;
  background: white;
  color: #344055;
  font-size: 13px;
  line-height: 1.7;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.user .message-bubble {
  border-color: #5367e8;
  border-radius: 14px 4px 14px 14px;
  color: white;
  background: #5367e8;
}

.thinking {
  display: flex;
  align-items: center;
  gap: 9px;
  color: #68758a;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.error-message {
  margin: 0 28px 10px;
  padding: 11px 14px;
  border-radius: 8px;
  color: #a62c2c;
  background: #fff0f0;
  font-size: 12px;
}

.composer {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0 auto;
  padding: 10px;
  width: min(780px, calc(100% - 48px));
  border: 1px solid #dfe5ee;
  border-radius: 15px;
  background: white;
  box-shadow: 0 8px 25px #283c5a0a;
}

.composer input {
  flex: 1;
  min-width: 0;
  padding: 9px 12px;
  outline: none;
  border: 0;
  color: #344055;
  background: transparent;
  font-size: 13px;
}

.composer input::placeholder {
  color: #9aa4b3;
}

.send-button {
  display: grid;
  place-items: center;
  width: 42px;
  height: 42px;
  border: 0;
  border-radius: 11px;
  color: white;
  background: #5367e8;
}

.send-button:disabled {
  cursor: not-allowed;
  opacity: .45;
}

.disclaimer {
  margin: 12px 0 18px;
  color: #98a1af;
  font-size: 10px;
  text-align: center;
}

@media (max-width: 700px) {
  .sidebar {
    width: 76px;
    padding: 20px 10px;
  }

  .brand {
    justify-content: center;
    padding: 0 0 24px;
  }

  .brand>div:last-child,
  .new-chat,
  .section-label,
  .conversation-item span,
  .sidebar-footer {
    display: none;
  }

  .conversation-item {
    justify-content: center;
    padding: 12px 5px;
  }

  .topbar {
    padding: 20px;
  }

  .topbar h1 {
    font-size: 16px;
  }

  .online-status {
    font-size: 0;
  }

  .messages-area {
    padding: 24px 16px;
  }

  .message-content {
    max-width: 85%;
  }
}
</style>
