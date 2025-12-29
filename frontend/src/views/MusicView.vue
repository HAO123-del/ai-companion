<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { API_URL } from '@/config'

const router = useRouter()
const appStore = useAppStore()

// Types
interface MusicTrack {
  id: string
  title: string
  artist: string
  cover_url: string | null
  audio_url: string | null
  duration: number
}

interface PlaybackState {
  is_playing: boolean
  progress: number
  current_track_id: string | null
  current_track?: MusicTrack
}

// State
const searchQuery = ref('')
const searchResults = ref<MusicTrack[]>([])
const isSearching = ref(false)
const tracks = ref<MusicTrack[]>([])
const playbackState = ref<PlaybackState>({
  is_playing: false,
  progress: 0,
  current_track_id: null
})
const currentTrack = ref<MusicTrack | null>(null)
const audioElement = ref<HTMLAudioElement | null>(null)
const showAddTrack = ref(false)
const newTrack = ref({
  title: '',
  artist: '',
  audio_url: ''
})

const API_BASE = API_URL

// Computed
const companionId = computed(() => appStore.currentCompanionId || 'default')

const progressPercent = computed(() => {
  if (!currentTrack.value || currentTrack.value.duration === 0) return 0
  return (playbackState.value.progress / currentTrack.value.duration) * 100
})

const formatTime = (seconds: number) => {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

// API calls
async function fetchTracks() {
  try {
    const res = await fetch(`${API_BASE}/music/tracks?limit=50`)
    if (res.ok) {
      tracks.value = await res.json()
    }
  } catch (e) {
    console.error('Failed to fetch tracks:', e)
  }
}

async function fetchPlaybackState() {
  try {
    const res = await fetch(`${API_BASE}/music/playback/${companionId.value}`)
    if (res.ok) {
      const data = await res.json()
      playbackState.value = data
      if (data.current_track) {
        currentTrack.value = data.current_track
      }
    }
  } catch (e) {
    console.error('Failed to fetch playback state:', e)
  }
}

async function searchTracks() {
  if (!searchQuery.value.trim()) {
    searchResults.value = []
    return
  }
  
  isSearching.value = true
  try {
    const res = await fetch(`${API_BASE}/music/tracks/search?q=${encodeURIComponent(searchQuery.value)}`)
    if (res.ok) {
      searchResults.value = await res.json()
    }
  } catch (e) {
    console.error('Search failed:', e)
  } finally {
    isSearching.value = false
  }
}

async function playTrack(track: MusicTrack) {
  try {
    const res = await fetch(`${API_BASE}/music/playback/${companionId.value}/play/${track.id}`, {
      method: 'POST'
    })
    if (res.ok) {
      const data = await res.json()
      playbackState.value = data.state
      currentTrack.value = data.track
      
      // Start audio playback if URL available
      if (track.audio_url && audioElement.value) {
        audioElement.value.src = track.audio_url
        audioElement.value.play()
      }
    }
  } catch (e) {
    console.error('Failed to play track:', e)
  }
}

async function togglePlayPause() {
  if (!currentTrack.value) return
  
  try {
    const endpoint = playbackState.value.is_playing ? 'pause' : 'resume'
    const res = await fetch(`${API_BASE}/music/playback/${companionId.value}/${endpoint}`, {
      method: 'POST'
    })
    if (res.ok) {
      const data = await res.json()
      playbackState.value = data.state
      
      // Control audio element
      if (audioElement.value) {
        if (playbackState.value.is_playing) {
          audioElement.value.play()
        } else {
          audioElement.value.pause()
        }
      }
    }
  } catch (e) {
    console.error('Failed to toggle playback:', e)
  }
}

async function stopPlayback() {
  try {
    const res = await fetch(`${API_BASE}/music/playback/${companionId.value}/stop`, {
      method: 'POST'
    })
    if (res.ok) {
      playbackState.value = { is_playing: false, progress: 0, current_track_id: null }
      currentTrack.value = null
      
      if (audioElement.value) {
        audioElement.value.pause()
        audioElement.value.currentTime = 0
      }
    }
  } catch (e) {
    console.error('Failed to stop playback:', e)
  }
}

async function addTrack() {
  if (!newTrack.value.title || !newTrack.value.artist) return
  
  try {
    const res = await fetch(`${API_BASE}/music/tracks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newTrack.value)
    })
    if (res.ok) {
      await fetchTracks()
      showAddTrack.value = false
      newTrack.value = { title: '', artist: '', audio_url: '' }
    }
  } catch (e) {
    console.error('Failed to add track:', e)
  }
}

// Audio element event handlers
function onTimeUpdate() {
  if (audioElement.value) {
    playbackState.value.progress = audioElement.value.currentTime
  }
}

function onEnded() {
  playbackState.value.is_playing = false
  playbackState.value.progress = 0
}

function seekTo(event: MouseEvent) {
  if (!currentTrack.value || !audioElement.value) return
  
  const target = event.currentTarget as HTMLElement
  const rect = target.getBoundingClientRect()
  const percent = (event.clientX - rect.left) / rect.width
  const newTime = percent * currentTrack.value.duration
  
  audioElement.value.currentTime = newTime
  playbackState.value.progress = newTime
}

// Lifecycle
onMounted(() => {
  fetchTracks()
  fetchPlaybackState()
  
  // Create audio element
  audioElement.value = new Audio()
  audioElement.value.addEventListener('timeupdate', onTimeUpdate)
  audioElement.value.addEventListener('ended', onEnded)
})

onUnmounted(() => {
  if (audioElement.value) {
    audioElement.value.pause()
    audioElement.value.removeEventListener('timeupdate', onTimeUpdate)
    audioElement.value.removeEventListener('ended', onEnded)
  }
})

// Watch search query
let searchTimeout: number
watch(searchQuery, () => {
  clearTimeout(searchTimeout)
  searchTimeout = window.setTimeout(searchTracks, 300)
})

function goBack() {
  router.back()
}
</script>

<template>
  <div class="flex flex-col h-full bg-black">
    <!-- Header -->
    <header class="flex items-center justify-between px-4 py-3 border-b border-dark-200">
      <button class="touch-btn text-2xl" @click="goBack">←</button>
      <h1 class="text-lg font-medium">一起听歌</h1>
      <button class="touch-btn text-2xl" @click="showAddTrack = true">+</button>
    </header>

    <!-- Search bar -->
    <div class="px-4 py-3">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="搜索歌曲或歌手..."
        class="w-full px-4 py-2 bg-dark-100 rounded-lg border border-dark-300 focus:border-primary focus:outline-none"
      />
    </div>

    <!-- Current playing -->
    <div v-if="currentTrack" class="px-4 py-3 bg-dark-100 mx-4 rounded-lg mb-3">
      <div class="flex items-center gap-3">
        <div class="w-12 h-12 bg-dark-300 rounded-lg flex items-center justify-center text-2xl">
          🎵
        </div>
        <div class="flex-1 min-w-0">
          <div class="font-medium truncate">{{ currentTrack.title }}</div>
          <div class="text-sm text-dark-500 truncate">{{ currentTrack.artist }}</div>
        </div>
        <button 
          class="touch-btn w-10 h-10 bg-primary rounded-full flex items-center justify-center"
          @click="togglePlayPause"
        >
          {{ playbackState.is_playing ? '⏸' : '▶️' }}
        </button>
        <button 
          class="touch-btn w-10 h-10 bg-dark-300 rounded-full flex items-center justify-center"
          @click="stopPlayback"
        >
          ⏹
        </button>
      </div>
      
      <!-- Progress bar -->
      <div class="mt-3">
        <div 
          class="h-1 bg-dark-300 rounded-full cursor-pointer"
          @click="seekTo"
        >
          <div 
            class="h-full bg-primary rounded-full transition-all"
            :style="{ width: `${progressPercent}%` }"
          ></div>
        </div>
        <div class="flex justify-between text-xs text-dark-500 mt-1">
          <span>{{ formatTime(playbackState.progress) }}</span>
          <span>{{ formatTime(currentTrack.duration) }}</span>
        </div>
      </div>
    </div>

    <!-- Track list -->
    <div class="flex-1 overflow-y-auto px-4">
      <!-- Search results -->
      <div v-if="searchQuery && searchResults.length > 0" class="mb-4">
        <h2 class="text-sm text-dark-500 mb-2">搜索结果</h2>
        <div 
          v-for="track in searchResults" 
          :key="track.id"
          class="flex items-center gap-3 py-3 border-b border-dark-200 cursor-pointer hover:bg-dark-100 -mx-2 px-2 rounded"
          @click="playTrack(track)"
        >
          <div class="w-10 h-10 bg-dark-300 rounded flex items-center justify-center">🎵</div>
          <div class="flex-1 min-w-0">
            <div class="font-medium truncate">{{ track.title }}</div>
            <div class="text-sm text-dark-500 truncate">{{ track.artist }}</div>
          </div>
          <span class="text-dark-500 text-sm">{{ formatTime(track.duration) }}</span>
        </div>
      </div>

      <!-- All tracks -->
      <div>
        <h2 class="text-sm text-dark-500 mb-2">全部歌曲 ({{ tracks.length }})</h2>
        <div v-if="tracks.length === 0" class="text-center py-8 text-dark-500">
          暂无歌曲，点击右上角添加
        </div>
        <div 
          v-for="track in tracks" 
          :key="track.id"
          class="flex items-center gap-3 py-3 border-b border-dark-200 cursor-pointer hover:bg-dark-100 -mx-2 px-2 rounded"
          :class="{ 'bg-dark-100': currentTrack?.id === track.id }"
          @click="playTrack(track)"
        >
          <div class="w-10 h-10 bg-dark-300 rounded flex items-center justify-center">
            {{ currentTrack?.id === track.id && playbackState.is_playing ? '🔊' : '🎵' }}
          </div>
          <div class="flex-1 min-w-0">
            <div class="font-medium truncate">{{ track.title }}</div>
            <div class="text-sm text-dark-500 truncate">{{ track.artist }}</div>
          </div>
          <span class="text-dark-500 text-sm">{{ formatTime(track.duration) }}</span>
        </div>
      </div>
    </div>

    <!-- Add track modal -->
    <div 
      v-if="showAddTrack" 
      class="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4"
      @click.self="showAddTrack = false"
    >
      <div class="bg-dark-100 rounded-xl p-4 w-full max-w-sm">
        <h2 class="text-lg font-medium mb-4">添加歌曲</h2>
        
        <div class="space-y-3">
          <input
            v-model="newTrack.title"
            type="text"
            placeholder="歌曲名称"
            class="w-full px-3 py-2 bg-dark-200 rounded-lg border border-dark-300 focus:border-primary focus:outline-none"
          />
          <input
            v-model="newTrack.artist"
            type="text"
            placeholder="歌手"
            class="w-full px-3 py-2 bg-dark-200 rounded-lg border border-dark-300 focus:border-primary focus:outline-none"
          />
          <input
            v-model="newTrack.audio_url"
            type="text"
            placeholder="音频URL (可选)"
            class="w-full px-3 py-2 bg-dark-200 rounded-lg border border-dark-300 focus:border-primary focus:outline-none"
          />
        </div>
        
        <div class="flex gap-3 mt-4">
          <button 
            class="flex-1 py-2 bg-dark-300 rounded-lg"
            @click="showAddTrack = false"
          >
            取消
          </button>
          <button 
            class="flex-1 py-2 bg-primary rounded-lg"
            @click="addTrack"
          >
            添加
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
