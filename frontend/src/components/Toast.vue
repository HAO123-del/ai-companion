<template>
  <Teleport to="body">
    <Transition name="toast">
      <div
        v-if="visible"
        :class="[
          'fixed top-4 left-1/2 -translate-x-1/2 z-[100] px-4 py-3 rounded-xl shadow-lg max-w-[90%] flex items-center gap-3',
          typeClasses
        ]"
      >
        <span class="text-xl">{{ icon }}</span>
        <span class="text-sm font-medium">{{ message }}</span>
        <button
          v-if="dismissible"
          @click="hide"
          class="ml-2 opacity-70 hover:opacity-100 transition-opacity"
        >
          ✕
        </button>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'

const props = withDefaults(defineProps<{
  message: string
  type?: 'success' | 'error' | 'warning' | 'info'
  duration?: number
  dismissible?: boolean
  modelValue?: boolean
}>(), {
  type: 'info',
  duration: 3000,
  dismissible: true,
  modelValue: false
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()

const visible = ref(props.modelValue)
let timeoutId: number | null = null

const typeClasses = computed(() => {
  const classes: Record<string, string> = {
    success: 'bg-green-600 text-white',
    error: 'bg-red-600 text-white',
    warning: 'bg-yellow-600 text-white',
    info: 'bg-blue-600 text-white'
  }
  return classes[props.type]
})

const icon = computed(() => {
  const icons: Record<string, string> = {
    success: '✓',
    error: '✕',
    warning: '⚠',
    info: 'ℹ'
  }
  return icons[props.type]
})

function show() {
  visible.value = true
  emit('update:modelValue', true)
  
  if (props.duration > 0) {
    if (timeoutId) clearTimeout(timeoutId)
    timeoutId = window.setTimeout(hide, props.duration)
  }
}

function hide() {
  visible.value = false
  emit('update:modelValue', false)
  if (timeoutId) {
    clearTimeout(timeoutId)
    timeoutId = null
  }
}

watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    show()
  } else {
    hide()
  }
})

// Expose methods
defineExpose({ show, hide })
</script>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translate(-50%, -20px);
}

.toast-leave-to {
  opacity: 0;
  transform: translate(-50%, -20px);
}
</style>
