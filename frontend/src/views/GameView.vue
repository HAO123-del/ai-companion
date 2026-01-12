<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { API_URL } from '@/config'

const router = useRouter()
const appStore = useAppStore()

// Types
interface Game {
  id: string
  name: string
  type: string
  description: string
}

interface GameSession {
  id: string
  game_id: string
  state: any
  is_active: boolean
}

interface GameStats {
  total_games: number
  wins: number
  losses: number
  ties: number
}

// State
const games = ref<Game[]>([])
const currentGame = ref<Game | null>(null)
const currentSession = ref<GameSession | null>(null)
const stats = ref<GameStats | null>(null)
const isPlaying = ref(false)
const message = ref('')
const userInput = ref('')

const API_BASE = API_URL

// Computed
const companionId = computed(() => appStore.currentCompanionId || 'default')

// API calls
async function fetchGames() {
  try {
    const res = await fetch(`${API_BASE}/games/`)
    if (res.ok) {
      games.value = await res.json()
    }
  } catch (e) {
    console.error('Failed to fetch games:', e)
  }
}

async function fetchStats() {
  try {
    const res = await fetch(`${API_BASE}/games/stats?companion_id=${companionId.value}`)
    if (res.ok) {
      stats.value = await res.json()
    }
  } catch (e) {
    console.error('Failed to fetch stats:', e)
  }
}

async function startGame(game: Game) {
  currentGame.value = game
  
  try {
    const res = await fetch(`${API_BASE}/games/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        game_id: game.id,
        companion_id: companionId.value
      })
    })
    
    if (res.ok) {
      currentSession.value = await res.json()
      isPlaying.value = true
      message.value = getGameStartMessage(game.id)
    }
  } catch (e) {
    console.error('Failed to start game:', e)
  }
}

function getGameStartMessage(gameId: string): string {
  switch (gameId) {
    case 'word_chain':
      return '成语接龙开始！请输入一个成语'
    case 'trivia':
      return '知识问答开始！准备好了吗？'
    case 'guess_number':
      return '我想了一个1-100的数字，猜猜看！'
    default:
      return '游戏开始！'
  }
}

async function submitPlay() {
  if (!currentSession.value || !userInput.value.trim()) return
  
  const gameId = currentSession.value.game_id
  let endpoint = ''
  let body: any = {}
  
  switch (gameId) {
    case 'word_chain':
      endpoint = 'word-chain'
      body = { word: userInput.value.trim() }
      break
    case 'trivia':
      endpoint = 'trivia'
      body = { answer: userInput.value.trim() }
      break
    case 'guess_number':
      endpoint = 'guess-number'
      body = { guess: parseInt(userInput.value) }
      break
  }
  
  try {
    const res = await fetch(`${API_BASE}/games/sessions/${currentSession.value.id}/${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    })
    
    const result = await res.json()
    handleGameResult(gameId, result)
    userInput.value = ''
  } catch (e) {
    console.error('Failed to submit play:', e)
  }
}

function handleGameResult(gameId: string, result: any) {
  if (result.error) {
    message.value = result.error
    return
  }
  
  switch (gameId) {
    case 'word_chain':
      if (result.valid) {
        message.value = `好！"${result.word}" 有效。轮到AI了...`
        // Simulate AI response
        setTimeout(() => {
          message.value = '你的回合，请继续接龙'
        }, 1000)
      } else {
        message.value = result.error || '无效的词语'
      }
      break
      
    case 'trivia':
      if (result.correct) {
        message.value = '✓ 回答正确！'
      } else {
        message.value = `✗ 错误，正确答案是：${result.correct_answer}`
      }
      if (result.finished) {
        setTimeout(() => endGame(), 2000)
      }
      break
      
    case 'guess_number':
      if (result.won) {
        message.value = `🎉 恭喜！猜对了，答案就是 ${result.target}！`
        setTimeout(() => endGame(), 2000)
      } else if (result.hint === 'higher') {
        message.value = '太小了，再大一点'
      } else if (result.hint === 'lower') {
        message.value = '太大了，再小一点'
      }
      if (result.finished && !result.won) {
        message.value = `游戏结束，答案是 ${result.target}`
        setTimeout(() => endGame(), 2000)
      }
      break
  }
  
  if (result.state) {
    currentSession.value = { ...currentSession.value!, state: result.state }
  }
}

async function endGame() {
  if (!currentSession.value) return
  
  try {
    await fetch(`${API_BASE}/games/sessions/${currentSession.value.id}/end`, {
      method: 'POST'
    })
  } catch (e) {
    console.error('Failed to end game:', e)
  }
  
  isPlaying.value = false
  currentSession.value = null
  currentGame.value = null
  message.value = ''
  fetchStats()
}

function goBack() {
  if (isPlaying.value) {
    if (confirm('确定要退出游戏吗？')) {
      endGame()
    }
  } else {
    router.back()
  }
}

onMounted(() => {
  fetchGames()
  fetchStats()
})
</script>

<template>
  <div class="flex flex-col h-full bg-black">
    <!-- Header -->
    <header class="flex items-center justify-between px-4 py-3 border-b border-dark-200">
      <button class="touch-btn text-2xl" @click="goBack">←</button>
      <h1 class="text-lg font-medium">
        {{ isPlaying && currentGame ? currentGame.name : '游戏中心' }}
      </h1>
      <div class="w-8"></div>
    </header>

    <!-- Game list view -->
    <div v-if="!isPlaying" class="flex-1 overflow-y-auto p-4">
      <!-- Stats -->
      <div v-if="stats" class="bg-dark-100 rounded-lg p-4 mb-4">
        <h2 class="text-sm text-dark-500 mb-2">游戏统计</h2>
        <div class="grid grid-cols-4 gap-2 text-center">
          <div>
            <div class="text-xl font-bold">{{ stats.total_games }}</div>
            <div class="text-xs text-dark-500">总场次</div>
          </div>
          <div>
            <div class="text-xl font-bold text-green-500">{{ stats.wins }}</div>
            <div class="text-xs text-dark-500">胜利</div>
          </div>
          <div>
            <div class="text-xl font-bold text-red-500">{{ stats.losses }}</div>
            <div class="text-xs text-dark-500">失败</div>
          </div>
          <div>
            <div class="text-xl font-bold text-yellow-500">{{ stats.ties }}</div>
            <div class="text-xs text-dark-500">平局</div>
          </div>
        </div>
      </div>

      <!-- Game list -->
      <h2 class="text-sm text-dark-500 mb-2">选择游戏</h2>
      <div class="space-y-3">
        <div 
          v-for="game in games" 
          :key="game.id"
          class="bg-dark-100 rounded-lg p-4 cursor-pointer hover:bg-dark-200 transition-colors"
          @click="startGame(game)"
        >
          <div class="flex items-center gap-3">
            <div class="w-12 h-12 bg-dark-300 rounded-lg flex items-center justify-center text-2xl">
              {{ game.id === 'word_chain' ? '📝' : game.id === 'trivia' ? '❓' : '🔢' }}
            </div>
            <div class="flex-1">
              <div class="font-medium">{{ game.name }}</div>
              <div class="text-sm text-dark-500">{{ game.description }}</div>
            </div>
            <span class="text-dark-500">▶</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Game play view -->
    <div v-else class="flex-1 flex flex-col">
      <!-- Game state display -->
      <div class="flex-1 p-4 flex flex-col items-center justify-center">
        <!-- Score display -->
        <div v-if="currentSession?.state" class="mb-4 text-center">
          <div class="text-sm text-dark-500">得分</div>
          <div class="text-3xl font-bold">{{ currentSession.state.user_score || 0 }}</div>
        </div>

        <!-- Trivia question -->
        <div v-if="currentGame?.id === 'trivia' && currentSession?.state?.questions" class="w-full max-w-sm">
          <div class="bg-dark-100 rounded-lg p-4 mb-4">
            <div class="text-sm text-dark-500 mb-2">
              问题 {{ (currentSession.state.current_index || 0) + 1 }} / {{ currentSession.state.questions.length }}
            </div>
            <div class="text-lg">
              {{ currentSession.state.questions[currentSession.state.current_index]?.question }}
            </div>
          </div>
          
          <!-- Options -->
          <div class="space-y-2">
            <button
              v-for="option in currentSession.state.questions[currentSession.state.current_index]?.options"
              :key="option"
              class="w-full py-3 px-4 bg-dark-100 rounded-lg text-left hover:bg-dark-200"
              @click="userInput = option; submitPlay()"
            >
              {{ option }}
            </button>
          </div>
        </div>

        <!-- Guess number range -->
        <div v-if="currentGame?.id === 'guess_number' && currentSession?.state" class="text-center">
          <div class="text-sm text-dark-500 mb-2">范围</div>
          <div class="text-2xl">
            {{ currentSession.state.min_range }} - {{ currentSession.state.max_range }}
          </div>
          <div class="text-sm text-dark-500 mt-2">
            已猜 {{ currentSession.state.guesses?.length || 0 }} / {{ currentSession.state.max_guesses }} 次
          </div>
        </div>

        <!-- Message -->
        <div class="mt-4 text-center text-lg">{{ message }}</div>
      </div>

      <!-- Input area (for word chain and guess number) -->
      <div v-if="currentGame?.id !== 'trivia'" class="p-4 border-t border-dark-200">
        <div class="flex gap-2">
          <input
            v-model="userInput"
            :type="currentGame?.id === 'guess_number' ? 'number' : 'text'"
            :placeholder="currentGame?.id === 'guess_number' ? '输入数字' : '输入成语'"
            class="flex-1 px-4 py-3 bg-dark-100 rounded-lg border border-dark-300 focus:border-primary focus:outline-none"
            @keyup.enter="submitPlay"
          />
          <button 
            class="px-6 py-3 bg-primary rounded-lg font-medium"
            @click="submitPlay"
          >
            确定
          </button>
        </div>
      </div>

      <!-- End game button -->
      <div class="p-4 pt-0">
        <button 
          class="w-full py-3 bg-dark-300 rounded-lg"
          @click="endGame"
        >
          结束游戏
        </button>
      </div>
    </div>
  </div>
</template>
