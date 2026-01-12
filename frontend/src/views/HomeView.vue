<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const currentTime = ref('')
const showMoreMenu = ref(false)

function updateTime() {
  const now = new Date()
  currentTime.value = now.toLocaleTimeString('en-US', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit'
  })
}

let timeInterval: number

onMounted(() => {
  updateTime()
  timeInterval = window.setInterval(updateTime, 1000)
})

onUnmounted(() => {
  clearInterval(timeInterval)
})

// Simple navigation without lock - Vue Router handles duplicate navigation
function navigate(path: string) {
  showMoreMenu.value = false
  router.push(path)
}

function goToChat() { navigate('/chat') }
function goToSettings() { navigate('/settings') }
function goToReminder() { navigate('/reminder') }
function goToMusic() { navigate('/music') }
function goToBook() { navigate('/book') }
function goToGame() { navigate('/game') }
function goToDiary() { navigate('/diary') }
function goToMemory() { navigate('/memory') }
function goToCompanion() { navigate('/companion') }
function toggleMoreMenu() { showMoreMenu.value = !showMoreMenu.value }
</script>

<template>
  <div class="flex flex-col h-full bg-black">
    <!-- Header with time -->
    <header class="text-center pt-8">
      <div class="text-6xl font-extralight">{{ currentTime }}</div>
    </header>

    <!-- Avatar area -->
    <div class="flex-1 flex justify-center items-center">
      <div 
        class="w-36 h-36 rounded-full border-2 border-dark-300 overflow-hidden cursor-pointer transition-all duration-300 hover:border-primary hover:shadow-lg hover:shadow-primary/30"
        @click="goToChat"
      >
        <img 
          src="https://api.dicebear.com/7.x/bottts/svg?seed=EVE" 
          alt="AI Companion"
          class="w-full h-full object-cover"
        />
      </div>
    </div>

    <!-- Status -->
    <div class="text-center h-16">
      <div class="text-primary text-base font-bold">AI Companion</div>
      <div class="text-dark-500 text-xs mt-1">点击头像开始对话</div>
    </div>

    <!-- Action button -->
    <div class="h-44 flex flex-col items-center justify-start mb-20">
      <button 
        class="touch-btn w-20 h-20 bg-dark-100 rounded-full border-2 border-dark-300 text-4xl"
        @click="goToChat"
      >
        🎤
      </button>
      <div class="mt-4 text-dark-400 text-xs">点击开始对话</div>
    </div>

    <!-- Bottom dock -->
    <nav class="fixed bottom-0 left-0 right-0 h-[70px] bg-dark-900/95 backdrop-blur-lg border-t border-dark-200 flex justify-around items-center safe-area-bottom max-w-mobile mx-auto">
      <button class="touch-btn flex flex-col items-center gap-1 text-primary" @click="goToChat">
        <span class="text-xl">💬</span>
        <span class="text-[10px]">聊天</span>
      </button>
      <button class="touch-btn flex flex-col items-center gap-1 text-dark-500" @click="goToReminder">
        <span class="text-xl">⏰</span>
        <span class="text-[10px]">提醒</span>
      </button>
      <button class="touch-btn flex flex-col items-center gap-1 text-dark-500" @click="goToMusic">
        <span class="text-xl">🎵</span>
        <span class="text-[10px]">听歌</span>
      </button>
      <button class="touch-btn flex flex-col items-center gap-1 text-dark-500" @click="goToBook">
        <span class="text-xl">📖</span>
        <span class="text-[10px]">共读</span>
      </button>
      <button class="touch-btn flex flex-col items-center gap-1 text-dark-500 relative" @click="toggleMoreMenu">
        <span class="text-xl">📋</span>
        <span class="text-[10px]">更多</span>
      </button>
    </nav>

    <!-- More Menu Popup -->
    <div v-if="showMoreMenu" class="fixed inset-0 z-50" @click="showMoreMenu = false">
      <div class="absolute bottom-[80px] right-4 bg-dark-100 rounded-xl shadow-xl border border-dark-200 overflow-hidden" @click.stop>
        <button class="flex items-center gap-3 w-full px-4 py-3 hover:bg-dark-200 transition-colors" @click="goToDiary">
          <span class="text-xl">📔</span>
          <span>日记心情</span>
        </button>
        <button class="flex items-center gap-3 w-full px-4 py-3 hover:bg-dark-200 transition-colors border-t border-dark-200" @click="goToGame">
          <span class="text-xl">🎮</span>
          <span>互动游戏</span>
        </button>
        <button class="flex items-center gap-3 w-full px-4 py-3 hover:bg-dark-200 transition-colors border-t border-dark-200" @click="goToMemory">
          <span class="text-xl">🧠</span>
          <span>记忆管理</span>
        </button>
        <button class="flex items-center gap-3 w-full px-4 py-3 hover:bg-dark-200 transition-colors border-t border-dark-200" @click="goToCompanion">
          <span class="text-xl">👤</span>
          <span>智能体管理</span>
        </button>
        <button class="flex items-center gap-3 w-full px-4 py-3 hover:bg-dark-200 transition-colors border-t border-dark-200" @click="goToSettings">
          <span class="text-xl">⚙️</span>
          <span>设置</span>
        </button>
      </div>
    </div>
  </div>
</template>
