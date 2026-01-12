<template>
  <div class="memory-view h-full flex flex-col bg-gradient-to-b from-purple-900 to-gray-900">
    <!-- Header -->
    <header class="flex items-center justify-between p-4 border-b border-purple-800/30">
      <button @click="goBack" class="p-2 rounded-full hover:bg-purple-800/30 transition-colors">
        <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <h1 class="text-lg font-semibold text-white">记忆管理</h1>
      <button @click="showAddModal = true" class="p-2 rounded-full hover:bg-purple-800/30 transition-colors">
        <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
      </button>
    </header>

    <!-- Category Filter -->
    <div class="flex gap-2 p-4 overflow-x-auto">
      <button
        v-for="cat in categories"
        :key="cat.value"
        @click="selectedCategory = cat.value"
        :class="[
          'px-4 py-2 rounded-full text-sm font-medium transition-colors whitespace-nowrap',
          selectedCategory === cat.value
            ? 'bg-purple-600 text-white'
            : 'bg-purple-800/30 text-purple-200 hover:bg-purple-800/50'
        ]"
      >
        {{ cat.label }}
      </button>
    </div>

    <!-- Memory List -->
    <div class="flex-1 overflow-y-auto p-4 space-y-3">
      <div v-if="loading" class="flex justify-center py-8">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-400"></div>
      </div>
      
      <div v-else-if="filteredMemories.length === 0" class="text-center py-8 text-purple-300">
        <svg class="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" 
            d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
        <p>暂无记忆</p>
        <p class="text-sm mt-2">点击右上角添加新记忆</p>
      </div>

      <div
        v-else
        v-for="memory in filteredMemories"
        :key="memory.id"
        class="bg-purple-800/20 rounded-xl p-4 border border-purple-700/30"
      >
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <div class="flex items-center gap-2 mb-2">
              <span :class="getCategoryClass(memory.category)" class="px-2 py-0.5 rounded-full text-xs font-medium">
                {{ getCategoryLabel(memory.category) }}
              </span>
              <span class="text-xs text-purple-400">
                重要度: {{ Math.round(memory.importance * 100) }}%
              </span>
            </div>
            <p class="text-white text-sm">{{ memory.content }}</p>
            <p class="text-xs text-purple-400 mt-2">
              {{ formatDate(memory.createdAt) }}
            </p>
          </div>
          <div class="flex gap-1 ml-2">
            <button 
              @click="editMemory(memory)"
              class="p-2 rounded-full hover:bg-purple-700/30 transition-colors"
            >
              <svg class="w-4 h-4 text-purple-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                  d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </button>
            <button 
              @click="confirmDelete(memory)"
              class="p-2 rounded-full hover:bg-red-700/30 transition-colors"
            >
              <svg class="w-4 h-4 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Add/Edit Modal -->
    <div v-if="showAddModal || editingMemory" class="fixed inset-0 bg-black/60 flex items-end justify-center z-50">
      <div class="bg-gray-900 w-full max-w-md rounded-t-3xl p-6 animate-slide-up">
        <h2 class="text-xl font-semibold text-white mb-4">
          {{ editingMemory ? '编辑记忆' : '添加记忆' }}
        </h2>
        
        <div class="space-y-4">
          <!-- Category -->
          <div>
            <label class="block text-sm text-purple-300 mb-2">类别</label>
            <div class="flex gap-2">
              <button
                v-for="cat in categories.filter(c => c.value !== 'all')"
                :key="cat.value"
                @click="formData.category = cat.value as 'preference' | 'fact' | 'event'"
                :class="[
                  'px-4 py-2 rounded-full text-sm font-medium transition-colors',
                  formData.category === cat.value
                    ? 'bg-purple-600 text-white'
                    : 'bg-purple-800/30 text-purple-200'
                ]"
              >
                {{ cat.label }}
              </button>
            </div>
          </div>

          <!-- Content -->
          <div>
            <label class="block text-sm text-purple-300 mb-2">内容</label>
            <textarea
              v-model="formData.content"
              rows="3"
              class="w-full bg-purple-800/20 border border-purple-700/30 rounded-xl px-4 py-3 text-white placeholder-purple-400 focus:outline-none focus:border-purple-500"
              placeholder="输入记忆内容..."
            ></textarea>
          </div>

          <!-- Importance -->
          <div>
            <label class="block text-sm text-purple-300 mb-2">
              重要度: {{ Math.round(formData.importance * 100) }}%
            </label>
            <input
              type="range"
              v-model.number="formData.importance"
              min="0"
              max="1"
              step="0.1"
              class="w-full accent-purple-500"
            />
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
            @click="saveMemory"
            :disabled="!formData.content.trim()"
            class="flex-1 py-3 rounded-xl bg-purple-600 text-white font-medium disabled:opacity-50"
          >
            保存
          </button>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation -->
    <div v-if="deletingMemory" class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div class="bg-gray-900 rounded-2xl p-6 max-w-sm w-full">
        <h3 class="text-lg font-semibold text-white mb-2">确认删除</h3>
        <p class="text-purple-300 text-sm mb-4">确定要删除这条记忆吗？此操作无法撤销。</p>
        <div class="flex gap-3">
          <button
            @click="deletingMemory = null"
            class="flex-1 py-2 rounded-xl bg-gray-700 text-white font-medium"
          >
            取消
          </button>
          <button
            @click="deleteMemory"
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
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import type { Memory } from '@/types'
import { API_URL } from '@/config'

const router = useRouter()
const store = useAppStore()

const API_BASE = API_URL

// State
const memories = ref<Memory[]>([])
const loading = ref(false)
const showAddModal = ref(false)
const editingMemory = ref<Memory | null>(null)
const deletingMemory = ref<Memory | null>(null)
const selectedCategory = ref<string>('all')

const formData = ref({
  category: 'preference' as 'preference' | 'fact' | 'event',
  content: '',
  importance: 0.5
})

const categories = [
  { value: 'all', label: '全部' },
  { value: 'preference', label: '偏好' },
  { value: 'fact', label: '事实' },
  { value: 'event', label: '事件' }
]

// Computed
const filteredMemories = computed(() => {
  if (selectedCategory.value === 'all') {
    return memories.value
  }
  return memories.value.filter(m => m.category === selectedCategory.value)
})

// Methods
function goBack() {
  router.back()
}

function getCategoryLabel(category: string): string {
  const cat = categories.find(c => c.value === category)
  return cat?.label || category
}

function getCategoryClass(category: string): string {
  const classes: Record<string, string> = {
    preference: 'bg-pink-600/30 text-pink-300',
    fact: 'bg-blue-600/30 text-blue-300',
    event: 'bg-green-600/30 text-green-300'
  }
  return classes[category] || 'bg-purple-600/30 text-purple-300'
}

function formatDate(date: Date | string): string {
  const d = new Date(date)
  return d.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

async function fetchMemories() {
  if (!store.currentCompanionId) return
  
  loading.value = true
  try {
    const response = await fetch(
      `${API_BASE}/memories/?companion_id=${store.currentCompanionId}`
    )
    if (response.ok) {
      memories.value = await response.json()
    }
  } catch (error) {
    console.error('Failed to fetch memories:', error)
  } finally {
    loading.value = false
  }
}

function editMemory(memory: Memory) {
  editingMemory.value = memory
  formData.value = {
    category: memory.category,
    content: memory.content,
    importance: memory.importance
  }
}

function confirmDelete(memory: Memory) {
  deletingMemory.value = memory
}

function closeModal() {
  showAddModal.value = false
  editingMemory.value = null
  formData.value = {
    category: 'preference',
    content: '',
    importance: 0.5
  }
}

async function saveMemory() {
  if (!store.currentCompanionId || !formData.value.content.trim()) return

  try {
    if (editingMemory.value) {
      // Update existing memory
      const response = await fetch(`${API_BASE}/memories/${editingMemory.value.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          category: formData.value.category,
          content: formData.value.content,
          importance: formData.value.importance
        })
      })
      if (response.ok) {
        await fetchMemories()
      }
    } else {
      // Create new memory
      const response = await fetch(`${API_BASE}/memories/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          companion_id: store.currentCompanionId,
          category: formData.value.category,
          content: formData.value.content,
          importance: formData.value.importance
        })
      })
      if (response.ok) {
        await fetchMemories()
      }
    }
    closeModal()
  } catch (error) {
    console.error('Failed to save memory:', error)
  }
}

async function deleteMemory() {
  if (!deletingMemory.value) return

  try {
    const response = await fetch(`${API_BASE}/memories/${deletingMemory.value.id}`, {
      method: 'DELETE'
    })
    if (response.ok) {
      memories.value = memories.value.filter(m => m.id !== deletingMemory.value?.id)
    }
  } catch (error) {
    console.error('Failed to delete memory:', error)
  } finally {
    deletingMemory.value = null
  }
}

onMounted(() => {
  fetchMemories()
})
</script>

<style scoped>
@keyframes slide-up {
  from {
    transform: translateY(100%);
  }
  to {
    transform: translateY(0);
  }
}

.animate-slide-up {
  animation: slide-up 0.3s ease-out;
}
</style>
