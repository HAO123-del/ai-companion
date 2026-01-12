import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Companion, Message, CallSession, MusicTrack, Book, ReadingPosition } from '@/types'

export const useAppStore = defineStore('app', () => {
  // Current companion
  const currentCompanionId = ref<string | null>(null)
  
  // Companions list
  const companions = ref<Companion[]>([])
  
  // Messages
  const messages = ref<Message[]>([])
  const isTyping = ref(false)
  
  // Call state
  const callSession = ref<CallSession | null>(null)
  
  function setCallSession(session: CallSession | null) {
    callSession.value = session
  }
  
  function updateCallStatus(status: CallSession['status']) {
    if (callSession.value) {
      callSession.value.status = status
    }
  }
  
  // Activity state
  const currentActivity = ref<'chat' | 'music' | 'reading' | 'game' | 'diary' | null>('chat')
  
  // Music player state
  const musicPlayer = ref({
    currentTrack: null as MusicTrack | null,
    isPlaying: false,
    progress: 0
  })
  
  // Reading state
  const readingState = ref({
    currentBook: null as Book | null,
    position: null as ReadingPosition | null
  })
  
  // UI state
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  
  // Computed
  const currentCompanion = computed(() => 
    companions.value.find(c => c.id === currentCompanionId.value) || null
  )
  
  // Actions
  function setCurrentCompanion(id: string | null) {
    currentCompanionId.value = id
  }
  
  function setCompanions(list: Companion[]) {
    companions.value = list
  }
  
  function addCompanion(companion: Companion) {
    companions.value.push(companion)
  }
  
  function updateCompanion(id: string, data: Partial<Companion>) {
    const index = companions.value.findIndex(c => c.id === id)
    if (index !== -1) {
      companions.value[index] = { ...companions.value[index], ...data }
    }
  }
  
  function removeCompanion(id: string) {
    companions.value = companions.value.filter(c => c.id !== id)
    if (currentCompanionId.value === id) {
      currentCompanionId.value = companions.value[0]?.id || null
    }
  }
  
  function setMessages(list: Message[]) {
    messages.value = list
  }
  
  function addMessage(message: Message) {
    messages.value.push(message)
  }
  
  function clearMessages() {
    messages.value = []
  }
  
  function setTyping(typing: boolean) {
    isTyping.value = typing
  }
  
  function setLoading(loading: boolean) {
    isLoading.value = loading
  }
  
  function setError(err: string | null) {
    error.value = err
  }
  
  function setActivity(activity: typeof currentActivity.value) {
    currentActivity.value = activity
  }
  
  return {
    // State
    currentCompanionId,
    companions,
    messages,
    isTyping,
    callSession,
    currentActivity,
    musicPlayer,
    readingState,
    isLoading,
    error,
    // Computed
    currentCompanion,
    // Actions
    setCurrentCompanion,
    setCompanions,
    addCompanion,
    updateCompanion,
    removeCompanion,
    setMessages,
    addMessage,
    clearMessages,
    setTyping,
    setCallSession,
    updateCallStatus,
    setLoading,
    setError,
    setActivity
  }
})
