<template>
  <div class="reminder-view h-full flex flex-col bg-gradient-to-b from-purple-900 to-gray-900">
    <!-- Header -->
    <header class="flex items-center justify-between p-4 border-b border-purple-800/30">
      <button @click="goBack" class="p-2 rounded-full hover:bg-purple-800/30 transition-colors">
        <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <h1 class="text-lg font-semibold text-white">提醒管理</h1>
      <button @click="showAddModal = true" class="p-2 rounded-full hover:bg-purple-800/30 transition-colors">
        <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
      </button>
    </header>

    <!-- Type Filter -->
    <div class="flex gap-2 p-4 overflow-x-auto">
      <button
        v-for="type in reminderTypes"
        :key="type.value"
        @click="selectedType = type.value"
        :class="[
          'px-4 py-2 rounded-full text-sm font-medium transition-colors whitespace-nowrap',
          selectedType === type.value
            ? 'bg-purple-600 text-white'
            : 'bg-purple-800/30 text-purple-200 hover:bg-purple-800/50'
        ]"
      >
        {{ type.icon }} {{ type.label }}
      </button>
    </div>

    <!-- Reminder List -->
    <div class="flex-1 overflow-y-auto p-4 space-y-3">
      <div v-if="loading" class="flex justify-center py-8">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-400"></div>
      </div>
      
      <div v-else-if="filteredReminders.length === 0" class="text-center py-8 text-purple-300">
        <svg class="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" 
            d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        <p>暂无提醒</p>
        <p class="text-sm mt-2">点击右上角添加新提醒</p>
      </div>

      <div
        v-else
        v-for="reminder in filteredReminders"
        :key="reminder.id"
        :class="[
          'rounded-xl p-4 border transition-all',
          reminder.enabled 
            ? 'bg-purple-800/20 border-purple-700/30' 
            : 'bg-gray-800/30 border-gray-700/30 opacity-60'
        ]"
      >
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <div class="flex items-center gap-2 mb-2">
              <span class="text-lg">{{ getTypeIcon(reminder.type) }}</span>
              <span :class="getTypeClass(reminder.type)" class="px-2 py-0.5 rounded-full text-xs font-medium">
                {{ getTypeLabel(reminder.type) }}
              </span>
              <span v-if="reminder.scheduledTime" class="text-xs text-purple-400">
                {{ formatTime(reminder.scheduledTime) }}
              </span>
            </div>
            <p class="text-white text-sm">{{ reminder.message }}</p>
            <p v-if="reminder.repeatPattern" class="text-xs text-purple-400 mt-2">
              🔄 {{ reminder.repeatPattern }}
            </p>
          </div>
          <div class="flex items-center gap-2 ml-2">
            <!-- Toggle Switch -->
            <button 
              @click="toggleReminder(reminder)"
              :class="[
                'relative w-12 h-6 rounded-full transition-colors',
                reminder.enabled ? 'bg-purple-600' : 'bg-gray-600'
              ]"
            >
              <span 
                :class="[
                  'absolute top-1 w-4 h-4 bg-white rounded-full transition-transform',
                  reminder.enabled ? 'left-7' : 'left-1'
                ]"
              ></span>
            </button>
            <!-- Delete Button -->
            <button 
              @click="confirmDelete(reminder)"
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

    <!-- Quick Actions -->
    <div class="p-4 border-t border-purple-800/30 space-y-2">
      <button 
        @click="sendMorningGreeting"
        class="w-full py-3 rounded-xl bg-yellow-600/20 text-yellow-300 font-medium flex items-center justify-center gap-2"
      >
        ☀️ 发送早安问候
      </button>
      <button 
        @click="sendEveningGreeting"
        class="w-full py-3 rounded-xl bg-indigo-600/20 text-indigo-300 font-medium flex items-center justify-center gap-2"
      >
        🌙 发送晚安问候
      </button>
    </div>

    <!-- Add Modal -->
    <div v-if="showAddModal" class="fixed inset-0 bg-black/60 flex items-end justify-center z-50">
      <div class="bg-gray-900 w-full max-w-md rounded-t-3xl p-6 animate-slide-up">
        <h2 class="text-xl font-semibold text-white mb-4">添加提醒</h2>
        
        <div class="space-y-4">
          <!-- Type -->
          <div>
            <label class="block text-sm text-purple-300 mb-2">类型</label>
            <div class="flex gap-2">
              <button
                v-for="type in reminderTypes.filter(t => t.value !== 'all')"
                :key="type.value"
                @click="formData.type = type.value as 'scheduled' | 'greeting' | 'checkin'"
                :class="[
                  'px-4 py-2 rounded-full text-sm font-medium transition-colors',
                  formData.type === type.value
                    ? 'bg-purple-600 text-white'
                    : 'bg-purple-800/30 text-purple-200'
                ]"
              >
                {{ type.icon }} {{ type.label }}
              </button>
            </div>
          </div>

          <!-- Message -->
          <div>
            <label class="block text-sm text-purple-300 mb-2">消息内容</label>
            <textarea
              v-model="formData.message"
              rows="3"
              class="w-full bg-purple-800/20 border border-purple-700/30 rounded-xl px-4 py-3 text-white placeholder-purple-400 focus:outline-none focus:border-purple-500"
              placeholder="输入提醒内容..."
            ></textarea>
          </div>

          <!-- Scheduled Time -->
          <div>
            <label class="block text-sm text-purple-300 mb-2">提醒时间（可选）</label>
            <input
              type="datetime-local"
              v-model="formData.scheduledTime"
              class="w-full bg-purple-800/20 border border-purple-700/30 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-purple-500"
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
            @click="saveReminder"
            :disabled="!formData.message.trim()"
            class="flex-1 py-3 rounded-xl bg-purple-600 text-white font-medium disabled:opacity-50"
          >
            保存
          </button>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation -->
    <div v-if="deletingReminder" class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div class="bg-gray-900 rounded-2xl p-6 max-w-sm w-full">
        <h3 class="text-lg font-semibold text-white mb-2">确认删除</h3>
        <p class="text-purple-300 text-sm mb-4">确定要删除这个提醒吗？</p>
        <div class="flex gap-3">
          <button
            @click="deletingReminder = null"
            class="flex-1 py-2 rounded-xl bg-gray-700 text-white font-medium"
          >
            取消
          </button>
          <button
            @click="deleteReminder"
            class="flex-1 py-2 rounded-xl bg-red-600 text-white font-medium"
          >
            删除
          </button>
        </div>
      </div>
    </div>

    <!-- Toast Notification -->
    <div 
      v-if="toast" 
      class="fixed bottom-24 left-4 right-4 bg-purple-600 text-white px-4 py-3 rounded-xl text-center"
    >
      {{ toast }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import type { Reminder } from '@/types'
import { API_URL } from '@/config'

const router = useRouter()
const store = useAppStore()

const API_BASE = API_URL

// State
const reminders = ref<Reminder[]>([])
const loading = ref(false)
const showAddModal = ref(false)
const deletingReminder = ref<Reminder | null>(null)
const selectedType = ref<string>('all')
const toast = ref<string | null>(null)

const formData = ref({
  type: 'scheduled' as 'scheduled' | 'greeting' | 'checkin',
  message: '',
  scheduledTime: ''
})

const reminderTypes = [
  { value: 'all', label: '全部', icon: '📋' },
  { value: 'scheduled', label: '定时', icon: '⏰' },
  { value: 'greeting', label: '问候', icon: '👋' },
  { value: 'checkin', label: '关怀', icon: '💭' }
]

// Computed
const filteredReminders = computed(() => {
  if (selectedType.value === 'all') {
    return reminders.value
  }
  return reminders.value.filter(r => r.type === selectedType.value)
})

// Methods
function goBack() {
  router.back()
}

function getTypeLabel(type: string): string {
  const t = reminderTypes.find(rt => rt.value === type)
  return t?.label || type
}

function getTypeIcon(type: string): string {
  const t = reminderTypes.find(rt => rt.value === type)
  return t?.icon || '📋'
}

function getTypeClass(type: string): string {
  const classes: Record<string, string> = {
    scheduled: 'bg-blue-600/30 text-blue-300',
    greeting: 'bg-yellow-600/30 text-yellow-300',
    checkin: 'bg-pink-600/30 text-pink-300'
  }
  return classes[type] || 'bg-purple-600/30 text-purple-300'
}

function formatTime(dateStr: string | Date): string {
  const d = new Date(dateStr)
  return d.toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function showToast(message: string) {
  toast.value = message
  setTimeout(() => { toast.value = null }, 2000)
}

async function fetchReminders() {
  if (!store.currentCompanionId) return
  
  loading.value = true
  try {
    const response = await fetch(
      `${API_BASE}/reminders/?companion_id=${store.currentCompanionId}`
    )
    if (response.ok) {
      reminders.value = await response.json()
    }
  } catch (error) {
    console.error('Failed to fetch reminders:', error)
  } finally {
    loading.value = false
  }
}

async function toggleReminder(reminder: Reminder) {
  try {
    const response = await fetch(`${API_BASE}/reminders/${reminder.id}/toggle`, {
      method: 'PUT'
    })
    if (response.ok) {
      const updated = await response.json()
      const index = reminders.value.findIndex(r => r.id === reminder.id)
      if (index !== -1) {
        reminders.value[index] = updated
      }
    }
  } catch (error) {
    console.error('Failed to toggle reminder:', error)
  }
}

function confirmDelete(reminder: Reminder) {
  deletingReminder.value = reminder
}

function closeModal() {
  showAddModal.value = false
  formData.value = {
    type: 'scheduled',
    message: '',
    scheduledTime: ''
  }
}

async function saveReminder() {
  if (!store.currentCompanionId || !formData.value.message.trim()) return

  try {
    const payload: any = {
      companion_id: store.currentCompanionId,
      type: formData.value.type,
      message: formData.value.message,
      enabled: true
    }
    
    if (formData.value.scheduledTime) {
      payload.scheduled_time = new Date(formData.value.scheduledTime).toISOString()
    }

    const response = await fetch(`${API_BASE}/reminders/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    
    if (response.ok) {
      await fetchReminders()
      closeModal()
      showToast('提醒已创建')
    }
  } catch (error) {
    console.error('Failed to save reminder:', error)
  }
}

async function deleteReminder() {
  if (!deletingReminder.value) return

  try {
    const response = await fetch(`${API_BASE}/reminders/${deletingReminder.value.id}`, {
      method: 'DELETE'
    })
    if (response.ok) {
      reminders.value = reminders.value.filter(r => r.id !== deletingReminder.value?.id)
      showToast('提醒已删除')
    }
  } catch (error) {
    console.error('Failed to delete reminder:', error)
  } finally {
    deletingReminder.value = null
  }
}

async function sendMorningGreeting() {
  if (!store.currentCompanionId) return
  
  try {
    const response = await fetch(
      `${API_BASE}/reminders/greeting?companion_id=${store.currentCompanionId}&greeting_type=morning`,
      { method: 'POST' }
    )
    if (response.ok) {
      await fetchReminders()
      showToast('早安问候已发送 ☀️')
    }
  } catch (error) {
    console.error('Failed to send greeting:', error)
  }
}

async function sendEveningGreeting() {
  if (!store.currentCompanionId) return
  
  try {
    const response = await fetch(
      `${API_BASE}/reminders/greeting?companion_id=${store.currentCompanionId}&greeting_type=evening`,
      { method: 'POST' }
    )
    if (response.ok) {
      await fetchReminders()
      showToast('晚安问候已发送 🌙')
    }
  } catch (error) {
    console.error('Failed to send greeting:', error)
  }
}

onMounted(() => {
  fetchReminders()
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
