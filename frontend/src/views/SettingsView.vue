<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// API 配置弹窗
const showApiConfig = ref(false)
const apiKey = ref(localStorage.getItem('minimax_api_key') || '')
const apiGroupId = ref(localStorage.getItem('minimax_group_id') || '')

function goBack() {
  router.push('/')
}

function goToCompanion() {
  router.push('/companion')
}

function openApiConfig() {
  showApiConfig.value = true
}

function closeApiConfig() {
  showApiConfig.value = false
}

function saveApiConfig() {
  localStorage.setItem('minimax_api_key', apiKey.value)
  localStorage.setItem('minimax_group_id', apiGroupId.value)
  showApiConfig.value = false
  alert('API 配置已保存')
}
</script>

<template>
  <div class="flex flex-col h-full bg-black">
    <!-- Header -->
    <header class="flex items-center justify-between px-4 py-3 border-b border-dark-200">
      <button class="touch-btn text-primary" @click="goBack">
        ← 返回
      </button>
      <div class="font-medium">设置</div>
      <div class="w-16"></div>
    </header>

    <!-- Settings list -->
    <div class="flex-1 overflow-y-auto p-4 space-y-3">
      <div class="bg-dark-100 rounded-xl overflow-hidden">
        <button class="touch-btn flex items-center justify-between w-full p-4 border-b border-dark-200 text-left" @click="goToCompanion">
          <span>智能体管理</span>
          <span class="text-dark-500">→</span>
        </button>
        <button class="touch-btn flex items-center justify-between w-full p-4 border-b border-dark-200 text-left" @click="openApiConfig">
          <span>API 配置</span>
          <span class="text-dark-500">→</span>
        </button>
      </div>

      <div class="bg-dark-100 rounded-xl overflow-hidden">
        <div class="flex items-center justify-between p-4">
          <span>关于</span>
          <span class="text-dark-500">v0.0.1</span>
        </div>
      </div>
    </div>

    <!-- API Config Modal -->
    <div v-if="showApiConfig" class="fixed inset-0 z-50 flex items-center justify-center bg-black/80" @click="closeApiConfig">
      <div class="bg-dark-100 rounded-xl w-[90%] max-w-md p-5" @click.stop>
        <h3 class="text-lg font-medium mb-4">API 配置</h3>
        
        <div class="space-y-4">
          <div>
            <label class="block text-sm text-dark-500 mb-2">MiniMax API Key</label>
            <input 
              v-model="apiKey"
              type="password"
              placeholder="输入你的 API Key"
              class="w-full bg-dark-200 rounded-lg px-4 py-3 text-white placeholder-dark-500 outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          
          <div>
            <label class="block text-sm text-dark-500 mb-2">Group ID</label>
            <input 
              v-model="apiGroupId"
              type="text"
              placeholder="输入你的 Group ID"
              class="w-full bg-dark-200 rounded-lg px-4 py-3 text-white placeholder-dark-500 outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
        </div>

        <div class="flex gap-3 mt-6">
          <button 
            class="touch-btn flex-1 py-3 bg-dark-200 rounded-lg"
            @click="closeApiConfig"
          >
            取消
          </button>
          <button 
            class="touch-btn flex-1 py-3 bg-primary rounded-lg font-medium"
            @click="saveApiConfig"
          >
            保存
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
