<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import Avatar from '@/components/Avatar.vue'
import type { Companion, CreateCompanionInput } from '@/types'
import { API_BASE } from '@/config'

const router = useRouter()
const store = useAppStore()

// Form state
const showForm = ref(false)
const isEditing = ref(false)
const editingId = ref<string | null>(null)
const formData = ref<CreateCompanionInput>({
  name: '',
  personality: '',
  avatarUrl: '',
  avatarPrimaryColor: '#8B5CF6',
  avatarSecondaryColor: '#6366F1',
  avatarStyle: 'gradient',
  voiceId: '',
  voiceType: 'preset'
})

// Voice management state
const showVoiceModal = ref(false)
const voiceCompanionId = ref<string | null>(null)
const presetVoices = ref<Array<{id: string, name: string, gender: string}>>([])
const selectedVoiceId = ref('')
const voiceFile = ref<File | null>(null)
const isUploadingVoice = ref(false)

// Avatar customization state
const showAvatarModal = ref(false)
const avatarCompanionId = ref<string | null>(null)
const avatarPrimaryColor = ref('#8B5CF6')
const avatarSecondaryColor = ref('#6366F1')
const avatarStyle = ref<'gradient' | 'solid' | 'outline'>('gradient')

// Preset colors
const presetColors = [
  '#8B5CF6', '#6366F1', '#EC4899', '#F43F5E', 
  '#F97316', '#EAB308', '#22C55E', '#14B8A6',
  '#06B6D4', '#3B82F6', '#6B7280', '#1F2937'
]

// Local loading state instead of global store
const isPageLoading = ref(true)

onMounted(async () => {
  isPageLoading.value = true
  try {
    await loadCompanions()
    await loadPresetVoices()
  } finally {
    isPageLoading.value = false
  }
})

async function loadCompanions() {
  try {
    console.log('Loading companions from:', `${API_BASE}/api/companions/`)
    const response = await fetch(`${API_BASE}/api/companions/`)
    console.log('Response status:', response.status)
    if (response.ok) {
      const data = await response.json()
      console.log('Companions data:', data)
      const companions: Companion[] = data.map((c: any) => ({
        id: c.id,
        name: c.name,
        personality: c.personality,
        avatarUrl: c.avatar_url || '',
        avatarPrimaryColor: c.avatar_primary_color || '#8B5CF6',
        avatarSecondaryColor: c.avatar_secondary_color || '#6366F1',
        avatarStyle: c.avatar_style || 'gradient',
        voiceId: c.voice_id || '',
        voiceType: c.voice_type || 'preset',
        createdAt: new Date(c.created_at),
        lastActiveAt: c.last_active_at ? new Date(c.last_active_at) : new Date()
      }))
      store.setCompanions(companions)
    } else {
      console.error('Failed to load companions:', response.status, response.statusText)
      store.setError('加载智能体列表失败: ' + response.status)
    }
  } catch (err) {
    console.error('Error loading companions:', err)
    store.setError('加载智能体列表失败: ' + (err as Error).message)
  }
}

async function loadPresetVoices() {
  try {
    const response = await fetch(`${API_BASE}/api/voice/presets`)
    if (response.ok) {
      presetVoices.value = await response.json()
    }
  } catch (err) {
    console.error('Failed to load preset voices')
  }
}

function goBack() {
  router.push('/')
}

function openCreateForm() {
  isEditing.value = false
  editingId.value = null
  formData.value = { 
    name: '', 
    personality: '', 
    avatarUrl: '', 
    avatarPrimaryColor: '#8B5CF6',
    avatarSecondaryColor: '#6366F1',
    avatarStyle: 'gradient',
    voiceId: '', 
    voiceType: 'preset' 
  }
  showForm.value = true
}

function openEditForm(companion: Companion) {
  isEditing.value = true
  editingId.value = companion.id
  formData.value = {
    name: companion.name,
    personality: companion.personality,
    avatarUrl: companion.avatarUrl,
    avatarPrimaryColor: companion.avatarPrimaryColor,
    avatarSecondaryColor: companion.avatarSecondaryColor,
    avatarStyle: companion.avatarStyle,
    voiceId: companion.voiceId,
    voiceType: companion.voiceType
  }
  showForm.value = true
}

function closeForm() {
  showForm.value = false
  formData.value = { 
    name: '', 
    personality: '', 
    avatarUrl: '', 
    avatarPrimaryColor: '#8B5CF6',
    avatarSecondaryColor: '#6366F1',
    avatarStyle: 'gradient',
    voiceId: '', 
    voiceType: 'preset' 
  }
}

async function saveCompanion() {
  if (!formData.value.name || !formData.value.personality) {
    store.setError('请填写名称和性格描述')
    return
  }

  store.setLoading(true)
  try {
    const payload = {
      name: formData.value.name,
      personality: formData.value.personality,
      avatar_url: formData.value.avatarUrl || null,
      avatar_primary_color: formData.value.avatarPrimaryColor || '#8B5CF6',
      avatar_secondary_color: formData.value.avatarSecondaryColor || '#6366F1',
      avatar_style: formData.value.avatarStyle || 'gradient',
      voice_id: formData.value.voiceId || null,
      voice_type: formData.value.voiceType
    }

    let response: Response
    if (isEditing.value && editingId.value) {
      response = await fetch(`${API_BASE}/api/companions/${editingId.value}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
    } else {
      response = await fetch(`${API_BASE}/api/companions/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
    }

    if (response.ok) {
      await loadCompanions()
      closeForm()
    } else {
      store.setError('保存失败')
    }
  } catch (err) {
    store.setError('网络错误')
  } finally {
    store.setLoading(false)
  }
}

async function deleteCompanion(id: string) {
  if (!confirm('确定要删除这个智能体吗？')) return
  
  store.setLoading(true)
  try {
    const response = await fetch(`${API_BASE}/api/companions/${id}`, {
      method: 'DELETE'
    })
    if (response.ok) {
      store.removeCompanion(id)
    }
  } catch (err) {
    store.setError('删除失败')
  } finally {
    store.setLoading(false)
  }
}

function selectCompanion(id: string) {
  store.setCurrentCompanion(id)
  router.push('/')
}

// Voice management functions
function openVoiceModal(companionId: string) {
  voiceCompanionId.value = companionId
  const companion = store.companions.find(c => c.id === companionId)
  selectedVoiceId.value = companion?.voiceId || ''
  voiceFile.value = null
  showVoiceModal.value = true
}

function closeVoiceModal() {
  showVoiceModal.value = false
  voiceCompanionId.value = null
  voiceFile.value = null
}

function handleVoiceFileChange(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.files && target.files[0]) {
    voiceFile.value = target.files[0]
  }
}

async function uploadVoiceClone() {
  if (!voiceFile.value || !voiceCompanionId.value) return
  
  // Get API credentials from localStorage
  const apiKey = localStorage.getItem('minimax_api_key') || ''
  const groupId = localStorage.getItem('minimax_group_id') || ''
  
  if (!apiKey) {
    store.setError('请先在设置中配置 API Key')
    return
  }
  
  isUploadingVoice.value = true
  try {
    const formData = new FormData()
    formData.append('file', voiceFile.value)
    
    const response = await fetch(`${API_BASE}/api/voice/clone/${voiceCompanionId.value}`, {
      method: 'POST',
      headers: {
        'X-Api-Key': apiKey,
        'X-Group-Id': groupId
      },
      body: formData
    })
    
    if (response.ok) {
      await loadCompanions()
      closeVoiceModal()
      store.setError(null)
      alert('声音克隆成功！')
    } else {
      const error = await response.json()
      store.setError(error.detail || '声音克隆失败')
    }
  } catch (err) {
    store.setError('上传失败')
  } finally {
    isUploadingVoice.value = false
  }
}

async function selectPresetVoice(voiceId: string) {
  if (!voiceCompanionId.value) return
  
  try {
    const response = await fetch(
      `${API_BASE}/api/voice/companion/${voiceCompanionId.value}/voice?voice_id=${voiceId}&voice_type=preset`,
      { method: 'PUT' }
    )
    
    if (response.ok) {
      await loadCompanions()
      closeVoiceModal()
    } else {
      store.setError('设置声音失败')
    }
  } catch (err) {
    store.setError('网络错误')
  }
}

function getVoiceName(voiceId: string): string {
  const preset = presetVoices.value.find(v => v.id === voiceId)
  if (preset) return preset.name
  if (voiceId?.startsWith('clone_')) return '克隆声音'
  return '未设置'
}

// Avatar customization functions
function openAvatarModal(companionId: string) {
  avatarCompanionId.value = companionId
  const companion = store.companions.find(c => c.id === companionId)
  if (companion) {
    avatarPrimaryColor.value = companion.avatarPrimaryColor || '#8B5CF6'
    avatarSecondaryColor.value = companion.avatarSecondaryColor || '#6366F1'
    avatarStyle.value = companion.avatarStyle || 'gradient'
  }
  showAvatarModal.value = true
}

function closeAvatarModal() {
  showAvatarModal.value = false
  avatarCompanionId.value = null
}

async function saveAvatarCustomization() {
  if (!avatarCompanionId.value) return
  
  store.setLoading(true)
  try {
    const response = await fetch(`${API_BASE}/api/companions/${avatarCompanionId.value}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        avatar_primary_color: avatarPrimaryColor.value,
        avatar_secondary_color: avatarSecondaryColor.value,
        avatar_style: avatarStyle.value
      })
    })
    
    if (response.ok) {
      await loadCompanions()
      closeAvatarModal()
    } else {
      store.setError('保存头像设置失败')
    }
  } catch (err) {
    store.setError('网络错误')
  } finally {
    store.setLoading(false)
  }
}
</script>

<template>
  <div class="flex flex-col h-full bg-black">
    <!-- Header -->
    <header class="flex items-center justify-between px-4 py-3 border-b border-dark-200">
      <button class="touch-btn text-primary" @click="goBack">← 返回</button>
      <div class="font-medium">智能体管理</div>
      <div class="w-16"></div>
    </header>

    <!-- Loading -->
    <div v-if="isPageLoading" class="flex-1 flex items-center justify-center">
      <div class="text-dark-500">加载中...</div>
    </div>

    <!-- Companion list -->
    <div v-else class="flex-1 overflow-y-auto p-4">
      <div 
        v-for="companion in store.companions" 
        :key="companion.id"
        class="p-4 bg-dark-100 rounded-xl mb-3"
      >
        <div class="flex items-center gap-4">
          <Avatar 
            :name="companion.name"
            :primary-color="companion.avatarPrimaryColor"
            :secondary-color="companion.avatarSecondaryColor"
            :avatar-style="companion.avatarStyle"
            size="md"
          />
          <div class="flex-1 min-w-0">
            <div class="font-medium">{{ companion.name }}</div>
            <div class="text-sm text-dark-500 truncate">{{ companion.personality }}</div>
            <div class="text-xs text-dark-400 mt-1">
              🎤 {{ getVoiceName(companion.voiceId) }}
            </div>
          </div>
        </div>
        <div class="flex gap-2 mt-3">
          <button 
            class="flex-1 touch-btn py-2 bg-dark-200 rounded-lg text-sm"
            @click="openEditForm(companion)"
          >编辑</button>
          <button 
            class="flex-1 touch-btn py-2 bg-dark-200 rounded-lg text-sm"
            @click="openAvatarModal(companion.id)"
          >头像</button>
          <button 
            class="flex-1 touch-btn py-2 bg-dark-200 rounded-lg text-sm"
            @click="openVoiceModal(companion.id)"
          >声音</button>
          <button 
            class="flex-1 touch-btn py-2 bg-red-600 rounded-lg text-sm"
            @click="deleteCompanion(companion.id)"
          >删除</button>
        </div>
        <button 
          class="w-full mt-2 touch-btn py-2 bg-primary rounded-lg text-sm"
          :class="{ 'ring-2 ring-white': store.currentCompanionId === companion.id }"
          @click="selectCompanion(companion.id)"
        >{{ store.currentCompanionId === companion.id ? '当前选中' : '选择此智能体' }}</button>
      </div>

      <div v-if="store.companions.length === 0" class="text-center text-dark-500 py-8">
        暂无智能体，点击下方按钮创建
      </div>
    </div>

    <!-- Add button -->
    <div class="p-4 safe-area-bottom">
      <button class="w-full py-4 bg-primary rounded-xl font-medium" @click="openCreateForm">
        + 创建新智能体
      </button>
    </div>

    <!-- Create/Edit Form Modal -->
    <div v-if="showForm" class="fixed inset-0 bg-black/80 flex items-center justify-center p-4 z-50" @click.self="closeForm">
      <div class="bg-dark-100 rounded-2xl w-full max-w-sm p-6 max-h-[90vh] overflow-y-auto">
        <h2 class="text-lg font-medium mb-4">{{ isEditing ? '编辑智能体' : '创建新智能体' }}</h2>
        <div class="space-y-4">
          <div>
            <label class="block text-sm text-dark-500 mb-1">名称</label>
            <input v-model="formData.name" type="text" placeholder="给你的智能体起个名字"
              class="w-full px-4 py-3 bg-dark-200 rounded-xl text-white placeholder-dark-500 outline-none focus:ring-2 focus:ring-primary" />
          </div>
          <div>
            <label class="block text-sm text-dark-500 mb-1">性格描述</label>
            <textarea v-model="formData.personality" placeholder="描述智能体的性格特点..." rows="3"
              class="w-full px-4 py-3 bg-dark-200 rounded-xl text-white placeholder-dark-500 outline-none focus:ring-2 focus:ring-primary resize-none"></textarea>
          </div>
          <div>
            <label class="block text-sm text-dark-500 mb-1">头像URL（可选）</label>
            <input v-model="formData.avatarUrl" type="text" placeholder="https://..."
              class="w-full px-4 py-3 bg-dark-200 rounded-xl text-white placeholder-dark-500 outline-none focus:ring-2 focus:ring-primary" />
          </div>
        </div>
        <div class="flex gap-3 mt-6">
          <button class="flex-1 py-3 bg-dark-200 rounded-xl" @click="closeForm">取消</button>
          <button class="flex-1 py-3 bg-primary rounded-xl font-medium" @click="saveCompanion">
            {{ isEditing ? '保存' : '创建' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Voice Management Modal -->
    <div v-if="showVoiceModal" class="fixed inset-0 bg-black/80 flex items-center justify-center p-4 z-50" @click.self="closeVoiceModal">
      <div class="bg-dark-100 rounded-2xl w-full max-w-sm p-6 max-h-[90vh] overflow-y-auto">
        <h2 class="text-lg font-medium mb-4">声音设置</h2>
        
        <!-- Voice Clone Upload -->
        <div class="mb-6">
          <h3 class="text-sm text-dark-500 mb-2">克隆声音</h3>
          <p class="text-xs text-dark-400 mb-3">上传10秒以上的清晰语音样本</p>
          <input 
            type="file" 
            accept="audio/*" 
            @change="handleVoiceFileChange"
            class="w-full text-sm text-dark-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-primary file:text-white"
          />
          <button 
            v-if="voiceFile"
            class="w-full mt-3 py-3 bg-primary rounded-xl font-medium disabled:opacity-50"
            :disabled="isUploadingVoice"
            @click="uploadVoiceClone"
          >
            {{ isUploadingVoice ? '上传中...' : '开始克隆' }}
          </button>
        </div>
        
        <!-- Preset Voices -->
        <div>
          <h3 class="text-sm text-dark-500 mb-2">预设声音</h3>
          <div class="grid grid-cols-2 gap-2">
            <button 
              v-for="voice in presetVoices" 
              :key="voice.id"
              class="p-3 bg-dark-200 rounded-xl text-sm text-left"
              :class="{ 'ring-2 ring-primary': selectedVoiceId === voice.id }"
              @click="selectPresetVoice(voice.id)"
            >
              <div>{{ voice.name }}</div>
              <div class="text-xs text-dark-400">{{ voice.gender === 'male' ? '男声' : '女声' }}</div>
            </button>
          </div>
        </div>
        
        <button class="w-full mt-6 py-3 bg-dark-200 rounded-xl" @click="closeVoiceModal">关闭</button>
      </div>
    </div>

    <!-- Error toast -->
    <div v-if="store.error" class="fixed bottom-20 left-4 right-4 bg-red-600 text-white px-4 py-3 rounded-xl text-center" @click="store.setError(null)">
      {{ store.error }}
    </div>

    <!-- Avatar Customization Modal -->
    <div v-if="showAvatarModal" class="fixed inset-0 bg-black/80 flex items-center justify-center p-4 z-50" @click.self="closeAvatarModal">
      <div class="bg-dark-100 rounded-2xl w-full max-w-sm p-6 max-h-[90vh] overflow-y-auto">
        <h2 class="text-lg font-medium mb-4">头像设置</h2>
        
        <!-- Preview -->
        <div class="flex justify-center mb-6">
          <Avatar 
            :name="store.companions.find(c => c.id === avatarCompanionId)?.name || 'AI'"
            :primary-color="avatarPrimaryColor"
            :secondary-color="avatarSecondaryColor"
            :avatar-style="avatarStyle"
            size="xl"
          />
        </div>
        
        <!-- Style Selection -->
        <div class="mb-4">
          <h3 class="text-sm text-dark-500 mb-2">样式</h3>
          <div class="flex gap-2">
            <button 
              class="flex-1 py-2 rounded-lg text-sm"
              :class="avatarStyle === 'gradient' ? 'bg-primary' : 'bg-dark-200'"
              @click="avatarStyle = 'gradient'"
            >渐变</button>
            <button 
              class="flex-1 py-2 rounded-lg text-sm"
              :class="avatarStyle === 'solid' ? 'bg-primary' : 'bg-dark-200'"
              @click="avatarStyle = 'solid'"
            >纯色</button>
            <button 
              class="flex-1 py-2 rounded-lg text-sm"
              :class="avatarStyle === 'outline' ? 'bg-primary' : 'bg-dark-200'"
              @click="avatarStyle = 'outline'"
            >描边</button>
          </div>
        </div>
        
        <!-- Primary Color -->
        <div class="mb-4">
          <h3 class="text-sm text-dark-500 mb-2">主色</h3>
          <div class="grid grid-cols-6 gap-2">
            <button 
              v-for="color in presetColors" 
              :key="'primary-' + color"
              class="w-10 h-10 rounded-lg"
              :class="{ 'ring-2 ring-white': avatarPrimaryColor === color }"
              :style="{ backgroundColor: color }"
              @click="avatarPrimaryColor = color"
            ></button>
          </div>
        </div>
        
        <!-- Secondary Color -->
        <div class="mb-4" v-if="avatarStyle === 'gradient'">
          <h3 class="text-sm text-dark-500 mb-2">副色</h3>
          <div class="grid grid-cols-6 gap-2">
            <button 
              v-for="color in presetColors" 
              :key="'secondary-' + color"
              class="w-10 h-10 rounded-lg"
              :class="{ 'ring-2 ring-white': avatarSecondaryColor === color }"
              :style="{ backgroundColor: color }"
              @click="avatarSecondaryColor = color"
            ></button>
          </div>
        </div>
        
        <div class="flex gap-3 mt-6">
          <button class="flex-1 py-3 bg-dark-200 rounded-xl" @click="closeAvatarModal">取消</button>
          <button class="flex-1 py-3 bg-primary rounded-xl font-medium" @click="saveAvatarCustomization">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>
