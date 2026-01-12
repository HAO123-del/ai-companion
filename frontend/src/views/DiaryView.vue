<template>
  <div class="diary-view h-full flex flex-col bg-gradient-to-b from-indigo-900 to-gray-900">
    <!-- Header -->
    <header class="flex items-center justify-between p-4 border-b border-indigo-800/30">
      <button @click="goBack" class="p-2 rounded-full hover:bg-indigo-800/30 transition-colors">
        <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <h1 class="text-lg font-semibold text-white">日记与心情</h1>
      <button @click="showAddModal = true" class="p-2 rounded-full hover:bg-indigo-800/30 transition-colors">
        <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
      </button>
    </header>

    <!-- Tab Navigation -->
    <div class="flex border-b border-indigo-800/30">
      <button
        @click="activeTab = 'entries'"
        :class="[
          'flex-1 py-3 text-sm font-medium transition-colors',
          activeTab === 'entries' ? 'text-white border-b-2 border-indigo-400' : 'text-indigo-300'
        ]"
      >
        日记列表
      </button>
      <button
        @click="activeTab = 'stats'"
        :class="[
          'flex-1 py-3 text-sm font-medium transition-colors',
          activeTab === 'stats' ? 'text-white border-b-2 border-indigo-400' : 'text-indigo-300'
        ]"
      >
        心情统计
      </button>
    </div>

    <!-- Mood Filter (for entries tab) -->
    <div v-if="activeTab === 'entries'" class="flex gap-2 p-4 overflow-x-auto">
      <button
        v-for="mood in moodFilters"
        :key="mood.value"
        @click="selectedMood = mood.value"
        :class="[
          'px-3 py-1.5 rounded-full text-sm font-medium transition-colors whitespace-nowrap flex items-center gap-1',
          selectedMood === mood.value
            ? 'bg-indigo-600 text-white'
            : 'bg-indigo-800/30 text-indigo-200 hover:bg-indigo-800/50'
        ]"
      >
        <span>{{ mood.emoji }}</span>
        <span>{{ mood.label }}</span>
      </button>
    </div>

    <!-- Content Area -->
    <div class="flex-1 overflow-y-auto p-4">
      <!-- Entries List -->
      <div v-if="activeTab === 'entries'" class="space-y-3">
        <div v-if="loading" class="flex justify-center py-8">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-400"></div>
        </div>
        
        <div v-else-if="filteredEntries.length === 0" class="text-center py-8 text-indigo-300">
          <svg class="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" 
              d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
          <p>暂无日记</p>
          <p class="text-sm mt-2">点击右上角开始记录</p>
        </div>

        <div
          v-else
          v-for="entry in filteredEntries"
          :key="entry.id"
          @click="viewEntry(entry)"
          class="bg-indigo-800/20 rounded-xl p-4 border border-indigo-700/30 cursor-pointer hover:bg-indigo-800/30 transition-colors"
        >
          <div class="flex items-start justify-between mb-2">
            <div class="flex items-center gap-2">
              <span class="text-2xl">{{ getMoodEmoji(entry.mood) }}</span>
              <span :class="getMoodClass(entry.mood)" class="px-2 py-0.5 rounded-full text-xs font-medium">
                {{ getMoodLabel(entry.mood) }}
              </span>
            </div>
            <span class="text-xs text-indigo-400">{{ formatDate(entry.createdAt) }}</span>
          </div>
          <p class="text-white text-sm line-clamp-3">{{ entry.content }}</p>
          <div v-if="entry.tags && entry.tags.length > 0" class="flex flex-wrap gap-1 mt-2">
            <span
              v-for="tag in entry.tags"
              :key="tag"
              class="px-2 py-0.5 bg-indigo-700/30 rounded-full text-xs text-indigo-300"
            >
              #{{ tag }}
            </span>
          </div>
        </div>
      </div>

      <!-- Stats View -->
      <div v-else class="space-y-6">
        <!-- Period Selector -->
        <div class="flex gap-2 justify-center">
          <button
            @click="statsPeriod = 'week'"
            :class="[
              'px-4 py-2 rounded-full text-sm font-medium transition-colors',
              statsPeriod === 'week' ? 'bg-indigo-600 text-white' : 'bg-indigo-800/30 text-indigo-200'
            ]"
          >
            本周
          </button>
          <button
            @click="statsPeriod = 'month'"
            :class="[
              'px-4 py-2 rounded-full text-sm font-medium transition-colors',
              statsPeriod === 'month' ? 'bg-indigo-600 text-white' : 'bg-indigo-800/30 text-indigo-200'
            ]"
          >
            本月
          </button>
        </div>

        <!-- Stats Cards -->
        <div v-if="moodStats" class="space-y-4">
          <!-- Average Score -->
          <div class="bg-indigo-800/20 rounded-xl p-4 border border-indigo-700/30">
            <h3 class="text-indigo-300 text-sm mb-2">平均心情分数</h3>
            <div class="flex items-center gap-3">
              <span class="text-4xl font-bold text-white">{{ moodStats.averageScore.toFixed(1) }}</span>
              <span class="text-2xl">{{ getScoreEmoji(moodStats.averageScore) }}</span>
            </div>
            <div class="mt-2 h-2 bg-indigo-900/50 rounded-full overflow-hidden">
              <div 
                class="h-full bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 rounded-full transition-all"
                :style="{ width: `${(moodStats.averageScore / 5) * 100}%` }"
              ></div>
            </div>
          </div>

          <!-- Trend -->
          <div class="bg-indigo-800/20 rounded-xl p-4 border border-indigo-700/30">
            <h3 class="text-indigo-300 text-sm mb-2">心情趋势</h3>
            <div class="flex items-center gap-2 mb-4">
              <span :class="getTrendClass(moodStats.trend)" class="text-2xl">
                {{ getTrendIcon(moodStats.trend) }}
              </span>
              <span class="text-white font-medium">{{ getTrendLabel(moodStats.trend) }}</span>
            </div>
            <!-- Trend Chart -->
            <div v-if="trendData.length > 0" class="h-32 flex items-end gap-1">
              <div
                v-for="(point, index) in trendData"
                :key="index"
                class="flex-1 flex flex-col items-center gap-1"
              >
                <div 
                  class="w-full rounded-t transition-all duration-300"
                  :class="getBarColorClass(point.score)"
                  :style="{ height: `${(point.score / 5) * 100}%` }"
                ></div>
                <span class="text-[10px] text-indigo-400">{{ point.label }}</span>
              </div>
            </div>
            <div v-else class="h-32 flex items-center justify-center text-indigo-400 text-sm">
              暂无足够数据生成趋势图
            </div>
          </div>

          <!-- Mood Distribution -->
          <div class="bg-indigo-800/20 rounded-xl p-4 border border-indigo-700/30">
            <h3 class="text-indigo-300 text-sm mb-3">心情分布</h3>
            <div class="space-y-2">
              <div
                v-for="mood in moodTypes"
                :key="mood.value"
                class="flex items-center gap-2"
              >
                <span class="w-6 text-center">{{ mood.emoji }}</span>
                <span class="w-12 text-xs text-indigo-300">{{ mood.label }}</span>
                <div class="flex-1 h-4 bg-indigo-900/50 rounded-full overflow-hidden">
                  <div
                    :class="mood.barClass"
                    class="h-full rounded-full transition-all"
                    :style="{ width: `${getMoodPercentage(mood.value)}%` }"
                  ></div>
                </div>
                <span class="w-8 text-xs text-indigo-300 text-right">
                  {{ moodStats.moodDistribution[mood.value] || 0 }}
                </span>
              </div>
            </div>
          </div>

          <!-- Total Entries -->
          <div class="bg-indigo-800/20 rounded-xl p-4 border border-indigo-700/30">
            <h3 class="text-indigo-300 text-sm mb-2">记录总数</h3>
            <span class="text-3xl font-bold text-white">{{ moodStats.totalEntries }}</span>
            <span class="text-indigo-300 ml-2">篇日记</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Add/Edit Modal -->
    <div v-if="showAddModal || editingEntry" class="fixed inset-0 bg-black/60 flex items-end justify-center z-50">
      <div class="bg-gray-900 w-full max-w-md rounded-t-3xl p-6 animate-slide-up max-h-[90vh] overflow-y-auto">
        <h2 class="text-xl font-semibold text-white mb-4">
          {{ editingEntry ? '编辑日记' : '写日记' }}
        </h2>
        
        <div class="space-y-4">
          <!-- Mood Selector -->
          <div>
            <label class="block text-sm text-indigo-300 mb-2">今天的心情</label>
            <div class="flex justify-between">
              <button
                v-for="mood in moodTypes"
                :key="mood.value"
                @click="formData.mood = mood.value as DiaryEntry['mood']"
                :class="[
                  'flex flex-col items-center p-2 rounded-xl transition-all',
                  formData.mood === mood.value
                    ? 'bg-indigo-600 scale-110'
                    : 'bg-indigo-800/30 hover:bg-indigo-800/50'
                ]"
              >
                <span class="text-2xl">{{ mood.emoji }}</span>
                <span class="text-xs text-white mt-1">{{ mood.label }}</span>
              </button>
            </div>
          </div>

          <!-- Mood Score -->
          <div>
            <label class="block text-sm text-indigo-300 mb-2">
              心情分数: {{ formData.moodScore }}
            </label>
            <input
              type="range"
              v-model.number="formData.moodScore"
              min="1"
              max="5"
              step="1"
              class="w-full accent-indigo-500"
            />
            <div class="flex justify-between text-xs text-indigo-400 mt-1">
              <span>😢 很差</span>
              <span>😊 很好</span>
            </div>
          </div>

          <!-- Content -->
          <div>
            <label class="block text-sm text-indigo-300 mb-2">日记内容</label>
            <textarea
              v-model="formData.content"
              rows="6"
              class="w-full bg-indigo-800/20 border border-indigo-700/30 rounded-xl px-4 py-3 text-white placeholder-indigo-400 focus:outline-none focus:border-indigo-500 resize-none"
              placeholder="今天发生了什么..."
            ></textarea>
          </div>

          <!-- Tags -->
          <div>
            <label class="block text-sm text-indigo-300 mb-2">标签</label>
            <div class="flex flex-wrap gap-2 mb-2">
              <span
                v-for="tag in formData.tags"
                :key="tag"
                class="px-2 py-1 bg-indigo-600 rounded-full text-xs text-white flex items-center gap-1"
              >
                #{{ tag }}
                <button @click="removeTag(tag)" class="hover:text-red-300">×</button>
              </span>
            </div>
            <div class="flex gap-2">
              <input
                v-model="newTag"
                @keyup.enter="addTag"
                class="flex-1 bg-indigo-800/20 border border-indigo-700/30 rounded-xl px-3 py-2 text-white text-sm placeholder-indigo-400 focus:outline-none focus:border-indigo-500"
                placeholder="添加标签..."
              />
              <button
                @click="addTag"
                class="px-3 py-2 bg-indigo-700 rounded-xl text-white text-sm"
              >
                添加
              </button>
            </div>
          </div>
        </div>

        <div class="flex gap-3 mt-6">
          <button
            @click="closeModal"
            class="flex-1 py-3 rounded-xl bg-gray-700 text-white font-medium"
          >
            取消
          </button>
          <button
            @click="saveEntry"
            :disabled="!formData.content.trim()"
            class="flex-1 py-3 rounded-xl bg-indigo-600 text-white font-medium disabled:opacity-50"
          >
            保存
          </button>
        </div>
      </div>
    </div>

    <!-- View Entry Modal -->
    <div v-if="viewingEntry" class="fixed inset-0 bg-black/60 flex items-end justify-center z-50">
      <div class="bg-gray-900 w-full max-w-md rounded-t-3xl p-6 animate-slide-up max-h-[90vh] overflow-y-auto">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-2">
            <span class="text-3xl">{{ getMoodEmoji(viewingEntry.mood) }}</span>
            <span :class="getMoodClass(viewingEntry.mood)" class="px-2 py-1 rounded-full text-sm font-medium">
              {{ getMoodLabel(viewingEntry.mood) }}
            </span>
          </div>
          <span class="text-sm text-indigo-400">{{ formatDate(viewingEntry.createdAt) }}</span>
        </div>
        
        <p class="text-white whitespace-pre-wrap mb-4">{{ viewingEntry.content }}</p>
        
        <div v-if="viewingEntry.tags && viewingEntry.tags.length > 0" class="flex flex-wrap gap-2 mb-4">
          <span
            v-for="tag in viewingEntry.tags"
            :key="tag"
            class="px-2 py-1 bg-indigo-700/30 rounded-full text-xs text-indigo-300"
          >
            #{{ tag }}
          </span>
        </div>

        <div class="flex gap-3">
          <button
            @click="viewingEntry = null"
            class="flex-1 py-3 rounded-xl bg-gray-700 text-white font-medium"
          >
            关闭
          </button>
          <button
            @click="editEntry(viewingEntry)"
            class="flex-1 py-3 rounded-xl bg-indigo-600 text-white font-medium"
          >
            编辑
          </button>
          <button
            @click="confirmDelete(viewingEntry)"
            class="py-3 px-4 rounded-xl bg-red-600 text-white font-medium"
          >
            删除
          </button>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation -->
    <div v-if="deletingEntry" class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div class="bg-gray-900 rounded-2xl p-6 max-w-sm w-full">
        <h3 class="text-lg font-semibold text-white mb-2">确认删除</h3>
        <p class="text-indigo-300 text-sm mb-4">确定要删除这篇日记吗？此操作无法撤销。</p>
        <div class="flex gap-3">
          <button
            @click="deletingEntry = null"
            class="flex-1 py-2 rounded-xl bg-gray-700 text-white font-medium"
          >
            取消
          </button>
          <button
            @click="deleteEntry"
            class="flex-1 py-2 rounded-xl bg-red-600 text-white font-medium"
          >
            删除
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import type { DiaryEntry, MoodStats } from '@/types'
import { API_URL } from '@/config'

const router = useRouter()
const API_BASE = API_URL

// State
const entries = ref<DiaryEntry[]>([])
const moodStats = ref<MoodStats | null>(null)
const loading = ref(false)
const activeTab = ref<'entries' | 'stats'>('entries')
const selectedMood = ref<string>('all')
const statsPeriod = ref<'week' | 'month'>('week')
const showAddModal = ref(false)
const editingEntry = ref<DiaryEntry | null>(null)
const viewingEntry = ref<DiaryEntry | null>(null)
const deletingEntry = ref<DiaryEntry | null>(null)
const newTag = ref('')

const formData = ref({
  content: '',
  mood: 'neutral' as DiaryEntry['mood'],
  moodScore: 3,
  tags: [] as string[]
})

const moodFilters = [
  { value: 'all', label: '全部', emoji: '📝' },
  { value: 'happy', label: '开心', emoji: '😊' },
  { value: 'excited', label: '兴奋', emoji: '🤩' },
  { value: 'neutral', label: '平静', emoji: '😐' },
  { value: 'anxious', label: '焦虑', emoji: '😰' },
  { value: 'sad', label: '难过', emoji: '😢' }
]

const moodTypes = [
  { value: 'happy', label: '开心', emoji: '😊', barClass: 'bg-green-500' },
  { value: 'excited', label: '兴奋', emoji: '🤩', barClass: 'bg-yellow-500' },
  { value: 'neutral', label: '平静', emoji: '😐', barClass: 'bg-blue-500' },
  { value: 'anxious', label: '焦虑', emoji: '😰', barClass: 'bg-orange-500' },
  { value: 'sad', label: '难过', emoji: '😢', barClass: 'bg-red-500' }
]

// Computed
const filteredEntries = computed(() => {
  if (selectedMood.value === 'all') return entries.value
  return entries.value.filter(e => e.mood === selectedMood.value)
})

// Trend data for chart visualization
const trendData = computed(() => {
  if (entries.value.length === 0) return []
  
  const days = statsPeriod.value === 'week' ? 7 : 30
  const now = new Date()
  const result: { label: string; score: number }[] = []
  
  // Group entries by day and calculate average score
  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(now)
    date.setDate(date.getDate() - i)
    const dateStr = date.toISOString().split('T')[0]
    
    const dayEntries = entries.value.filter(e => {
      const entryDate = new Date(e.createdAt).toISOString().split('T')[0]
      return entryDate === dateStr
    })
    
    let avgScore = 0
    if (dayEntries.length > 0) {
      const scores = dayEntries.map(e => e.moodScore || 3)
      avgScore = scores.reduce((a, b) => a + b, 0) / scores.length
    }
    
    // Format label based on period
    const label = statsPeriod.value === 'week' 
      ? ['日', '一', '二', '三', '四', '五', '六'][date.getDay()]
      : `${date.getDate()}`
    
    result.push({ label, score: avgScore })
  }
  
  return result
})

// Watch for stats period change
watch(statsPeriod, () => {
  if (activeTab.value === 'stats') fetchStats()
})

watch(activeTab, (tab) => {
  if (tab === 'stats') fetchStats()
})

// Methods
function goBack() {
  router.back()
}

function getMoodEmoji(mood: string): string {
  const m = moodTypes.find(t => t.value === mood)
  return m?.emoji || '😐'
}

function getMoodLabel(mood: string): string {
  const m = moodTypes.find(t => t.value === mood)
  return m?.label || mood
}

function getMoodClass(mood: string): string {
  const classes: Record<string, string> = {
    happy: 'bg-green-600/30 text-green-300',
    excited: 'bg-yellow-600/30 text-yellow-300',
    neutral: 'bg-blue-600/30 text-blue-300',
    anxious: 'bg-orange-600/30 text-orange-300',
    sad: 'bg-red-600/30 text-red-300'
  }
  return classes[mood] || 'bg-indigo-600/30 text-indigo-300'
}

function getScoreEmoji(score: number): string {
  if (score >= 4) return '😊'
  if (score >= 3) return '🙂'
  if (score >= 2) return '😐'
  return '😢'
}

function getTrendIcon(trend: string): string {
  if (trend === 'improving') return '📈'
  if (trend === 'declining') return '📉'
  return '➡️'
}

function getTrendLabel(trend: string): string {
  if (trend === 'improving') return '心情在好转'
  if (trend === 'declining') return '心情有些低落'
  return '心情稳定'
}

function getTrendClass(trend: string): string {
  if (trend === 'improving') return 'text-green-400'
  if (trend === 'declining') return 'text-red-400'
  return 'text-blue-400'
}

function getMoodPercentage(mood: string): number {
  if (!moodStats.value || moodStats.value.totalEntries === 0) return 0
  const count = moodStats.value.moodDistribution[mood] || 0
  return (count / moodStats.value.totalEntries) * 100
}

function getBarColorClass(score: number): string {
  if (score === 0) return 'bg-indigo-900/30'
  if (score >= 4) return 'bg-green-500'
  if (score >= 3) return 'bg-blue-500'
  if (score >= 2) return 'bg-yellow-500'
  return 'bg-red-500'
}

function formatDate(date: Date | string): string {
  const d = new Date(date)
  return d.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

async function fetchEntries() {
  loading.value = true
  try {
    const response = await fetch(`${API_BASE}/diary/`)
    if (response.ok) {
      entries.value = await response.json()
    }
  } catch (error) {
    console.error('Failed to fetch entries:', error)
  } finally {
    loading.value = false
  }
}

async function fetchStats() {
  try {
    const response = await fetch(`${API_BASE}/diary/stats?period=${statsPeriod.value}`)
    if (response.ok) {
      const data = await response.json()
      moodStats.value = {
        period: data.period,
        averageScore: data.average_score,
        moodDistribution: data.mood_distribution,
        trend: data.trend,
        totalEntries: data.total_entries
      }
    }
  } catch (error) {
    console.error('Failed to fetch stats:', error)
  }
}

function viewEntry(entry: DiaryEntry) {
  viewingEntry.value = entry
}

function editEntry(entry: DiaryEntry) {
  viewingEntry.value = null
  editingEntry.value = entry
  formData.value = {
    content: entry.content,
    mood: entry.mood,
    moodScore: entry.moodScore || 3,
    tags: [...(entry.tags || [])]
  }
}

function confirmDelete(entry: DiaryEntry) {
  viewingEntry.value = null
  deletingEntry.value = entry
}

function closeModal() {
  showAddModal.value = false
  editingEntry.value = null
  formData.value = {
    content: '',
    mood: 'neutral',
    moodScore: 3,
    tags: []
  }
}

function addTag() {
  const tag = newTag.value.trim().replace(/^#/, '')
  if (tag && !formData.value.tags.includes(tag)) {
    formData.value.tags.push(tag)
  }
  newTag.value = ''
}

function removeTag(tag: string) {
  formData.value.tags = formData.value.tags.filter(t => t !== tag)
}

async function saveEntry() {
  if (!formData.value.content.trim()) return

  try {
    const payload = {
      content: formData.value.content,
      mood: formData.value.mood,
      mood_score: formData.value.moodScore,
      tags: formData.value.tags
    }

    if (editingEntry.value) {
      const response = await fetch(`${API_BASE}/diary/${editingEntry.value.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      if (response.ok) {
        await fetchEntries()
      }
    } else {
      const response = await fetch(`${API_BASE}/diary/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      if (response.ok) {
        await fetchEntries()
      }
    }
    closeModal()
  } catch (error) {
    console.error('Failed to save entry:', error)
  }
}

async function deleteEntry() {
  if (!deletingEntry.value) return

  try {
    const response = await fetch(`${API_BASE}/diary/${deletingEntry.value.id}`, {
      method: 'DELETE'
    })
    if (response.ok) {
      entries.value = entries.value.filter(e => e.id !== deletingEntry.value?.id)
    }
  } catch (error) {
    console.error('Failed to delete entry:', error)
  } finally {
    deletingEntry.value = null
  }
}

onMounted(() => {
  fetchEntries()
})
</script>

<style scoped>
@keyframes slide-up {
  from { transform: translateY(100%); }
  to { transform: translateY(0); }
}

.animate-slide-up {
  animation: slide-up 0.3s ease-out;
}

.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
