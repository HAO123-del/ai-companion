<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import type { Message } from '@/types'
import { API_BASE } from '@/config'

const router = useRouter()
const store = useAppStore()

const inputText = ref('')
const messagesContainer = ref<HTMLElement | null>(null)
const isLoading = ref(false)

// Load message history on mount
onMounted(async () => {
  if (store.currentCompanionId) {
    await loadMessageHistory()
  }
})

// Watch for companion changes
watch(() => store.currentCompanionId, async (newId) => {
  if (newId) {
    store.clearMessages()
    await loadMessageHistory()
  }
})

async function loadMessageHistory() {
  if (!store.currentCompanionId) return
  
  try {
    const response = await fetch(
      `${API_BASE}/api/messages/?companion_id=${store.currentCompanionId}&limit=50`
    )
    if (response.ok) {
      const data = await response.json()
      const messages: Message[] = data.map((m: any) => ({
        id: m.id,
        companionId: m.companion_id,
        role: m.role,
        content: m.content,
        audioUrl: m.audio_url,
        timestamp: new Date(m.timestamp)
      }))
      store.setMessages(messages)
      await scrollToBottom()
    }
  } catch (err) {
    console.error('Failed to load message history:', err)
  }
}

function goBack() {
  router.push('/')
}

function startCall() {
  router.push('/call')
}

function goToMemory() {
  router.push('/memory')
}

async function scrollToBottom() {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

async function sendMessage() {
  if (!inputText.value.trim() || !store.currentCompanionId || isLoading.value) return
  
  const userContent = inputText.value.trim()
  inputText.value = ''
  
  // Add user message to UI immediately
  const userMessage: Message = {
    id: `temp-${Date.now()}`,
    companionId: store.currentCompanionId,
    role: 'user',
    content: userContent,
    timestamp: new Date()
  }
  store.addMessage(userMessage)
  await scrollToBottom()
  
  // Show typing indicator
  store.setTyping(true)
  isLoading.value = true
  
  try {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 30000) // 30s timeout
    
    // Get API key from localStorage
    const apiKey = localStorage.getItem('minimax_api_key') || ''
    const groupId = localStorage.getItem('minimax_group_id') || ''
    
    const response = await fetch(`${API_BASE}/api/messages/chat`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'X-API-Key': apiKey,
        'X-Group-Id': groupId
      },
      body: JSON.stringify({
        companion_id: store.currentCompanionId,
        content: userContent
      }),
      signal: controller.signal
    })
    
    clearTimeout(timeoutId)
    
    if (response.ok) {
      const data = await response.json()
      
      // Add AI response with typing animation
      const aiMessage: Message = {
        id: data.id,
        companionId: data.companion_id,
        role: 'companion',
        content: '',
        timestamp: new Date(data.timestamp)
      }
      store.addMessage(aiMessage)
      
      // Animate typing effect
      await typeMessage(data.id, data.content)
    } else {
      store.setError('发送失败，请重试')
    }
  } catch (err) {
    store.setError('网络错误，请检查连接')
  } finally {
    store.setTyping(false)
    isLoading.value = false
    await scrollToBottom()
  }
}

async function typeMessage(messageId: string, fullContent: string) {
  // Show full content immediately for better responsiveness
  const msgIndex = store.messages.findIndex(m => m.id === messageId)
  if (msgIndex !== -1) {
    store.messages[msgIndex].content = fullContent
  }
  await scrollToBottom()
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <div class="flex flex-col h-full bg-black">
    <!-- Header -->
    <header class="flex items-center justify-between px-4 py-3 border-b border-dark-200">
      <button class="touch-btn text-primary" @click="goBack">
        ← 返回
      </button>
      <div class="text-center">
        <div class="font-medium">{{ store.currentCompanion?.name || 'AI Companion' }}</div>
        <div class="text-xs text-dark-500">{{ store.isTyping ? '正在输入...' : '在线' }}</div>
      </div>
      <div class="flex gap-2">
        <button class="touch-btn text-primary text-lg" @click="goToMemory" title="记忆管理">
          🧠
        </button>
        <button class="touch-btn text-primary text-xl" @click="startCall">
          📞
        </button>
      </div>
    </header>

    <!-- Messages area -->
    <div ref="messagesContainer" class="flex-1 overflow-y-auto p-4 space-y-3">
      <!-- Empty state -->
      <div v-if="store.messages.length === 0 && !store.isTyping" class="flex flex-col items-center justify-center h-full text-dark-500">
        <div class="text-4xl mb-4">💬</div>
        <div>开始和 {{ store.currentCompanion?.name || 'AI' }} 聊天吧</div>
      </div>
      
      <!-- Messages -->
      <div 
        v-for="message in store.messages" 
        :key="message.id"
        :class="[
          'flex',
          message.role === 'user' ? 'justify-end' : 'justify-start'
        ]"
      >
        <div 
          :class="[
            'max-w-[80%] px-4 py-2.5 rounded-2xl',
            message.role === 'user' 
              ? 'bg-primary text-white rounded-br-sm' 
              : 'bg-dark-200 text-white rounded-bl-sm'
          ]"
        >
          <div class="whitespace-pre-wrap break-words">{{ message.content }}</div>
          <div 
            :class="[
              'text-xs mt-1 opacity-60',
              message.role === 'user' ? 'text-right' : 'text-left'
            ]"
          >
            {{ formatTime(message.timestamp) }}
          </div>
        </div>
      </div>
      
      <!-- Typing indicator -->
      <div v-if="store.isTyping && store.messages[store.messages.length - 1]?.role !== 'companion'" class="flex justify-start">
        <div class="bg-dark-200 text-white px-4 py-2.5 rounded-2xl rounded-bl-sm">
          <div class="flex gap-1">
            <span class="w-2 h-2 bg-dark-400 rounded-full animate-bounce" style="animation-delay: 0ms"></span>
            <span class="w-2 h-2 bg-dark-400 rounded-full animate-bounce" style="animation-delay: 150ms"></span>
            <span class="w-2 h-2 bg-dark-400 rounded-full animate-bounce" style="animation-delay: 300ms"></span>
          </div>
        </div>
      </div>
    </div>

    <!-- Input area -->
    <div class="p-4 border-t border-dark-200 safe-area-bottom">
      <div class="flex gap-2">
        <input 
          v-model="inputText"
          type="text"
          placeholder="输入消息..."
          :disabled="isLoading"
          class="flex-1 bg-dark-200 border border-dark-300 rounded-full px-4 py-3 text-white placeholder-dark-500 focus:outline-none focus:border-primary disabled:opacity-50"
          @keyup.enter="sendMessage"
        />
        <button 
          class="touch-btn w-12 h-12 bg-primary rounded-full text-white disabled:opacity-50"
          :disabled="isLoading || !inputText.trim()"
          @click="sendMessage"
        >
          <span v-if="isLoading" class="animate-spin">⏳</span>
          <span v-else>↑</span>
        </button>
      </div>
    </div>

    <!-- Error toast -->
    <div 
      v-if="store.error" 
      class="fixed bottom-24 left-4 right-4 bg-red-600 text-white px-4 py-3 rounded-xl text-center"
      @click="store.setError(null)"
    >
      {{ store.error }}
    </div>
  </div>
</template>
