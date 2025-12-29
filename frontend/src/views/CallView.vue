<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import Avatar from '@/components/Avatar.vue'
import { audioAnalyzer } from '@/utils/audioAnalyzer'

import { API_BASE, WS_BASE } from '@/config'

const router = useRouter()
const store = useAppStore()

// Call state
const callStatus = ref<'idle' | 'connecting' | 'active' | 'ended'>('idle')
const sessionId = ref<string | null>(null)
const duration = ref(0)
const isRecording = ref(false)
const isSpeaking = ref(false)
const responseText = ref('')
const currentExpression = ref<'neutral' | 'happy' | 'sad' | 'thinking' | 'surprised'>('neutral')
const lipSyncData = ref<number[]>([])
const manualInput = ref('')
const isProcessing = ref(false)

// WebSocket
let ws: WebSocket | null = null
let durationTimer: number | null = null
// Speech recognition (Web Speech API)
let recognition: any = null

const formattedDuration = computed(() => {
  const mins = Math.floor(duration.value / 60)
  const secs = duration.value % 60
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
})

onMounted(() => {
  // Initialize speech recognition if available
  if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition
    recognition = new SpeechRecognition()
    recognition.continuous = true
    recognition.interimResults = false
    recognition.lang = 'zh-CN'
    
    recognition.onresult = (event: any) => {
      console.log('Speech recognition result:', event)
      const last = event.results.length - 1
      const text = event.results[last][0].transcript
      console.log('Recognized text:', text)
      if (text && ws && callStatus.value === 'active') {
        sendSpeech(text)
      }
    }
    
    recognition.onerror = (event: any) => {
      console.error('Speech recognition error:', event.error)
      // Show error to user
      if (event.error === 'not-allowed') {
        store.setError('请允许麦克风权限')
      } else if (event.error === 'no-speech') {
        // Restart recognition
        if (callStatus.value === 'active' && isRecording.value) {
          try { recognition.start() } catch(e) {}
        }
      } else {
        store.setError(`语音识别错误: ${event.error}`)
      }
    }
    
    recognition.onend = () => {
      console.log('Speech recognition ended, restarting...')
      // Restart if still in call
      if (callStatus.value === 'active' && isRecording.value) {
        try {
          recognition.start()
        } catch(e) {
          console.error('Failed to restart recognition:', e)
        }
      }
    }
    
    recognition.onstart = () => {
      console.log('Speech recognition started')
    }
  } else {
    console.error('Speech recognition not supported')
    store.setError('您的浏览器不支持语音识别，请使用 Chrome 浏览器')
  }
})

onUnmounted(() => {
  endCall()
})

async function startCall() {
  if (!store.currentCompanionId) {
    store.setError('请先选择一个智能体')
    return
  }
  
  callStatus.value = 'connecting'
  
  try {
    // Create call session
    const response = await fetch(`${API_BASE}/api/call/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ companion_id: store.currentCompanionId })
    })
    
    if (!response.ok) throw new Error('Failed to start call')
    
    const data = await response.json()
    sessionId.value = data.id
    
    // Connect WebSocket
    connectWebSocket(data.id)
    
  } catch (err) {
    console.error('Failed to start call:', err)
    store.setError('无法开始通话，请重试')
    callStatus.value = 'idle'
  }
}

function connectWebSocket(sid: string) {
  ws = new WebSocket(`${WS_BASE}/api/call/ws/${sid}`)
  
  ws.onopen = () => {
    // Get API credentials from localStorage
    const apiKey = localStorage.getItem('minimax_api_key') || ''
    const groupId = localStorage.getItem('minimax_group_id') || ''
    
    // Activate the call with API credentials
    ws?.send(JSON.stringify({ 
      type: 'activate',
      api_key: apiKey,
      group_id: groupId
    }))
  }
  
  ws.onmessage = async (event) => {
    const data = JSON.parse(event.data)
    console.log('WebSocket message received:', data)
    
    if (data.type === 'status') {
      if (data.status === 'active') {
        callStatus.value = 'active'
        startDurationTimer()
        startRecording()
      } else if (data.status === 'ended') {
        callStatus.value = 'ended'
      }
    } else if (data.type === 'response') {
      isProcessing.value = false
      responseText.value = data.text
      isSpeaking.value = true
      
      // Update expression based on response
      updateExpression(data.text)
      
      // Play audio if available
      if (data.audio) {
        console.log('Audio received, length:', data.audio.length)
        // Analyze audio for lip-sync
        lipSyncData.value = await audioAnalyzer.analyzeBase64Audio(data.audio)
        await playAudio(data.audio, data.audio_format || 'mp3')
      } else {
        console.log('No audio in response')
      }
      
      isSpeaking.value = false
      lipSyncData.value = []
      currentExpression.value = 'neutral'
    } else if (data.type === 'error') {
      isProcessing.value = false
      store.setError(data.message)
    }
  }
  
  ws.onerror = () => {
    store.setError('连接错误')
    endCall()
  }
  
  ws.onclose = () => {
    if (callStatus.value === 'active') {
      callStatus.value = 'ended'
    }
  }
}

function sendSpeech(text: string) {
  if (ws && ws.readyState === WebSocket.OPEN && !isProcessing.value) {
    console.log('Sending speech to server:', text)
    isProcessing.value = true
    ws.send(JSON.stringify({ type: 'speech', text }))
    currentExpression.value = 'thinking'
  } else {
    console.log('Cannot send speech - ws:', !!ws, 'readyState:', ws?.readyState, 'isProcessing:', isProcessing.value)
  }
}

function sendManualInput() {
  if (manualInput.value.trim() && callStatus.value === 'active') {
    sendSpeech(manualInput.value.trim())
    manualInput.value = ''
  }
}

function updateExpression(text: string) {
  // Simple sentiment analysis for expression
  const happyWords = ['开心', '高兴', '太好了', '哈哈', '棒', '喜欢', '爱', '好的', '当然']
  const sadWords = ['难过', '伤心', '抱歉', '对不起', '遗憾', '可惜']
  const surprisedWords = ['哇', '真的吗', '太棒了', '不可思议', '惊讶']
  
  const lowerText = text.toLowerCase()
  
  if (happyWords.some(word => lowerText.includes(word))) {
    currentExpression.value = 'happy'
  } else if (sadWords.some(word => lowerText.includes(word))) {
    currentExpression.value = 'sad'
  } else if (surprisedWords.some(word => lowerText.includes(word))) {
    currentExpression.value = 'surprised'
  } else {
    currentExpression.value = 'neutral'
  }
}

async function playAudio(base64Audio: string, _format: string) {
  try {
    const audioData = atob(base64Audio)
    const arrayBuffer = new ArrayBuffer(audioData.length)
    const view = new Uint8Array(arrayBuffer)
    for (let i = 0; i < audioData.length; i++) {
      view[i] = audioData.charCodeAt(i)
    }
    
    const audioContext = new AudioContext()
    
    const audioBuffer = await audioContext.decodeAudioData(arrayBuffer)
    const source = audioContext.createBufferSource()
    source.buffer = audioBuffer
    source.connect(audioContext.destination)
    source.start()
    
    // Wait for audio to finish
    await new Promise(resolve => {
      source.onended = resolve
    })
  } catch (err) {
    console.error('Failed to play audio:', err)
  }
}

function startDurationTimer() {
  duration.value = 0
  durationTimer = window.setInterval(() => {
    duration.value++
  }, 1000)
}

function stopDurationTimer() {
  if (durationTimer) {
    clearInterval(durationTimer)
    durationTimer = null
  }
}

function startRecording() {
  if (recognition) {
    isRecording.value = true
    try {
      recognition.start()
      console.log('Started recording')
    } catch(e) {
      console.error('Failed to start recording:', e)
      store.setError('无法启动语音识别')
    }
  } else {
    store.setError('语音识别不可用')
  }
}

function stopRecording() {
  isRecording.value = false
  if (recognition) {
    recognition.stop()
  }
}

function endCall() {
  stopRecording()
  stopDurationTimer()
  
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'end' }))
    ws.close()
  }
  ws = null
  
  callStatus.value = 'ended'
  
  // Reset after delay
  setTimeout(() => {
    callStatus.value = 'idle'
    sessionId.value = null
    duration.value = 0
    responseText.value = ''
  }, 2000)
}

function goBack() {
  if (callStatus.value === 'active') {
    endCall()
  }
  router.push('/chat')
}
</script>

<template>
  <div class="flex flex-col h-full bg-black">
    <!-- Header -->
    <header class="flex items-center justify-between px-4 py-3">
      <button class="touch-btn text-primary" @click="goBack">
        ← 返回
      </button>
      <div class="text-center font-medium">语音通话</div>
      <div class="w-16"></div>
    </header>

    <!-- Call content -->
    <div class="flex-1 flex flex-col items-center justify-center px-6">
      <!-- Avatar -->
      <div class="mb-8">
        <Avatar 
          :name="store.currentCompanion?.name || 'AI'"
          :expression="currentExpression"
          :is-speaking="isSpeaking"
          :lip-sync-data="lipSyncData"
          size="xl"
        />
      </div>
      
      <!-- Companion name -->
      <h2 class="text-2xl font-bold mb-2">
        {{ store.currentCompanion?.name || 'AI Companion' }}
      </h2>
      
      <!-- Call status -->
      <div class="text-dark-500 mb-4">
        <span v-if="callStatus === 'idle'">点击下方按钮开始通话</span>
        <span v-else-if="callStatus === 'connecting'" class="animate-pulse">正在连接...</span>
        <span v-else-if="callStatus === 'active'">{{ formattedDuration }}</span>
        <span v-else-if="callStatus === 'ended'">通话已结束</span>
      </div>
      
      <!-- Response text -->
      <div 
        v-if="responseText && callStatus === 'active'"
        class="max-w-full bg-dark-200 rounded-2xl px-4 py-3 mb-8 text-center"
      >
        <p class="text-sm text-dark-400 mb-1">AI 说:</p>
        <p>{{ responseText }}</p>
      </div>
      
      <!-- Recording indicator -->
      <div 
        v-if="isRecording && callStatus === 'active'"
        class="flex items-center gap-2 text-primary mb-4"
      >
        <span class="w-3 h-3 bg-red-500 rounded-full animate-pulse"></span>
        <span>正在聆听...</span>
      </div>
      
      <!-- Manual input for testing -->
      <div 
        v-if="callStatus === 'active'"
        class="w-full max-w-sm mb-4"
      >
        <div class="flex gap-2">
          <input 
            v-model="manualInput"
            type="text"
            placeholder="输入文字测试..."
            class="flex-1 bg-dark-200 rounded-xl px-4 py-2 text-white placeholder-dark-500 outline-none"
            :disabled="isProcessing"
            @keyup.enter="sendManualInput"
          />
          <button 
            class="bg-primary text-white px-4 py-2 rounded-xl disabled:opacity-50"
            :disabled="!manualInput.trim() || isProcessing"
            @click="sendManualInput"
          >
            {{ isProcessing ? '...' : '发送' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Call controls -->
    <div class="p-8 safe-area-bottom">
      <div class="flex justify-center gap-8">
        <!-- Start/End call button -->
        <button 
          v-if="callStatus === 'idle'"
          class="w-20 h-20 rounded-full bg-green-500 text-white text-3xl flex items-center justify-center shadow-lg active:scale-95 transition-transform"
          @click="startCall"
        >
          📞
        </button>
        
        <button 
          v-else-if="callStatus === 'connecting'"
          class="w-20 h-20 rounded-full bg-yellow-500 text-white text-3xl flex items-center justify-center shadow-lg animate-pulse"
          disabled
        >
          ⏳
        </button>
        
        <button 
          v-else-if="callStatus === 'active'"
          class="w-20 h-20 rounded-full bg-red-500 text-white text-3xl flex items-center justify-center shadow-lg active:scale-95 transition-transform"
          @click="endCall"
        >
          📵
        </button>
        
        <button 
          v-else
          class="w-20 h-20 rounded-full bg-dark-300 text-white text-3xl flex items-center justify-center shadow-lg"
          disabled
        >
          ✓
        </button>
      </div>
      
      <!-- Hint -->
      <p class="text-center text-dark-500 text-sm mt-4">
        <span v-if="callStatus === 'idle'">使用语音与 AI 实时对话</span>
        <span v-else-if="callStatus === 'active'">说话后 AI 会自动回复</span>
      </p>
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
