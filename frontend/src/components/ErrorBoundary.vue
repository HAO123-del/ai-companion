<template>
  <div v-if="error" class="error-boundary p-4 bg-red-900/20 rounded-xl border border-red-700/30">
    <div class="flex items-center gap-3 mb-3">
      <span class="text-2xl">⚠️</span>
      <h3 class="text-red-300 font-medium">出错了</h3>
    </div>
    <p class="text-red-200 text-sm mb-4">{{ errorMessage }}</p>
    <div class="flex gap-2">
      <button
        @click="retry"
        class="px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700 transition-colors"
      >
        重试
      </button>
      <button
        @click="dismiss"
        class="px-4 py-2 bg-gray-700 text-white rounded-lg text-sm font-medium hover:bg-gray-600 transition-colors"
      >
        关闭
      </button>
    </div>
  </div>
  <slot v-else></slot>
</template>

<script setup lang="ts">
import { ref, computed, onErrorCaptured } from 'vue'

const props = defineProps<{
  fallbackMessage?: string
}>()

const emit = defineEmits<{
  (e: 'retry'): void
  (e: 'error', error: Error): void
}>()

const error = ref<Error | null>(null)

const errorMessage = computed(() => {
  if (props.fallbackMessage) return props.fallbackMessage
  if (error.value?.message) return error.value.message
  return '发生了未知错误，请稍后重试'
})

onErrorCaptured((err) => {
  error.value = err as Error
  emit('error', err as Error)
  return false
})

function retry() {
  error.value = null
  emit('retry')
}

function dismiss() {
  error.value = null
}

// Expose methods for parent components
defineExpose({
  setError: (err: Error) => { error.value = err },
  clearError: () => { error.value = null }
})
</script>
