<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'

interface Props {
  name?: string
  expression?: 'neutral' | 'happy' | 'sad' | 'thinking' | 'surprised'
  isSpeaking?: boolean
  lipSyncData?: number[]
  size?: 'sm' | 'md' | 'lg' | 'xl'
  primaryColor?: string
  secondaryColor?: string
  avatarStyle?: 'gradient' | 'solid' | 'outline'
}

const props = withDefaults(defineProps<Props>(), {
  name: 'AI',
  expression: 'neutral',
  isSpeaking: false,
  lipSyncData: () => [],
  size: 'lg',
  primaryColor: '#8B5CF6',
  secondaryColor: '#6366F1',
  avatarStyle: 'gradient'
})

// Idle animation state
const idleOffset = ref(0)
const lipSyncFrame = ref(0)
let idleAnimationFrame: number | null = null
let lipSyncAnimationFrame: number | null = null

// Size classes
const sizeClasses = computed(() => {
  const sizes = {
    sm: 'w-12 h-12 text-xl',
    md: 'w-20 h-20 text-3xl',
    lg: 'w-32 h-32 text-5xl',
    xl: 'w-40 h-40 text-6xl'
  }
  return sizes[props.size]
})

// Expression emoji mapping
const expressionEmoji = computed(() => {
  const emojis = {
    neutral: '😊',
    happy: '😄',
    sad: '😢',
    thinking: '🤔',
    surprised: '😮'
  }
  return emojis[props.expression]
})

// Expression-based eye style
const eyeStyle = computed(() => {
  const styles = {
    neutral: { left: 'scale-100', right: 'scale-100' },
    happy: { left: 'scale-y-50', right: 'scale-y-50' },
    sad: { left: 'scale-100 rotate-12', right: 'scale-100 -rotate-12' },
    thinking: { left: 'scale-100', right: 'scale-75 translate-y-1' },
    surprised: { left: 'scale-125', right: 'scale-125' }
  }
  return styles[props.expression]
})

// Mouth style based on expression, speaking, and lip-sync
const mouthStyle = computed(() => {
  if (props.isSpeaking) {
    // Use lip-sync data if available
    if (props.lipSyncData && props.lipSyncData.length > 0) {
      const amplitude = props.lipSyncData[lipSyncFrame.value % props.lipSyncData.length] || 0
      const height = Math.max(4, amplitude * 16)
      const width = Math.max(8, 16 - amplitude * 4)
      return {
        height: `${height}px`,
        width: `${width}px`,
        borderRadius: amplitude > 0.5 ? '50%' : '9999px'
      }
    }
    return 'animate-mouth-speak'
  }
  const styles = {
    neutral: 'w-4 h-1 rounded-full',
    happy: 'w-6 h-3 rounded-b-full border-b-2 border-current',
    sad: 'w-6 h-3 rounded-t-full border-t-2 border-current',
    thinking: 'w-3 h-3 rounded-full translate-x-2',
    surprised: 'w-4 h-4 rounded-full'
  }
  return styles[props.expression]
})

// Background style
const backgroundStyle = computed(() => {
  if (props.avatarStyle === 'gradient') {
    return {
      background: `linear-gradient(135deg, ${props.primaryColor}, ${props.secondaryColor})`
    }
  } else if (props.avatarStyle === 'solid') {
    return {
      backgroundColor: props.primaryColor
    }
  } else {
    return {
      backgroundColor: 'transparent',
      border: `3px solid ${props.primaryColor}`
    }
  }
})

// Idle animation
function startIdleAnimation() {
  let time = 0
  const animate = () => {
    time += 0.02
    idleOffset.value = Math.sin(time) * 3
    idleAnimationFrame = requestAnimationFrame(animate)
  }
  animate()
}

function stopIdleAnimation() {
  if (idleAnimationFrame) {
    cancelAnimationFrame(idleAnimationFrame)
    idleAnimationFrame = null
  }
}

// Lip-sync animation
function startLipSyncAnimation() {
  let frame = 0
  const animate = () => {
    frame++
    lipSyncFrame.value = frame
    lipSyncAnimationFrame = requestAnimationFrame(animate)
  }
  animate()
}

function stopLipSyncAnimation() {
  if (lipSyncAnimationFrame) {
    cancelAnimationFrame(lipSyncAnimationFrame)
    lipSyncAnimationFrame = null
  }
  lipSyncFrame.value = 0
}

// Watch for speaking state changes
import { watch } from 'vue'

watch(() => props.isSpeaking, (speaking) => {
  if (speaking && props.lipSyncData && props.lipSyncData.length > 0) {
    startLipSyncAnimation()
  } else {
    stopLipSyncAnimation()
  }
})

onMounted(() => {
  startIdleAnimation()
})

onUnmounted(() => {
  stopIdleAnimation()
  stopLipSyncAnimation()
})

// First letter of name for fallback
const initial = computed(() => props.name?.charAt(0)?.toUpperCase() || 'A')
</script>

<template>
  <div class="avatar-container relative inline-block">
    <!-- Main avatar circle -->
    <div 
      :class="[
        'rounded-full flex items-center justify-center transition-all duration-300',
        sizeClasses,
        isSpeaking ? 'ring-4 ring-primary/50 animate-pulse' : ''
      ]"
      :style="[
        backgroundStyle,
        { transform: `translateY(${idleOffset}px)` }
      ]"
    >
      <!-- Face container -->
      <div class="face relative flex flex-col items-center justify-center">
        <!-- Eyes -->
        <div class="eyes flex gap-3 mb-2">
          <div 
            class="eye w-2 h-2 bg-white rounded-full transition-transform duration-200"
            :class="eyeStyle.left"
          ></div>
          <div 
            class="eye w-2 h-2 bg-white rounded-full transition-transform duration-200"
            :class="eyeStyle.right"
          ></div>
        </div>
        
        <!-- Mouth -->
        <div 
          class="mouth bg-white transition-all duration-200"
          :class="mouthStyle"
        ></div>
      </div>
      
      <!-- Fallback: Initial letter -->
      <span 
        v-if="false" 
        class="text-white font-bold select-none"
      >
        {{ initial }}
      </span>
    </div>
    
    <!-- Speaking indicator -->
    <div 
      v-if="isSpeaking"
      class="absolute -bottom-1 left-1/2 -translate-x-1/2 flex gap-0.5"
    >
      <span class="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" style="animation-delay: 0ms"></span>
      <span class="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" style="animation-delay: 100ms"></span>
      <span class="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" style="animation-delay: 200ms"></span>
    </div>
    
    <!-- Expression badge -->
    <div 
      v-if="expression !== 'neutral'"
      class="absolute -top-1 -right-1 text-lg"
    >
      {{ expressionEmoji }}
    </div>
  </div>
</template>

<style scoped>
.avatar-container {
  perspective: 1000px;
}

.face {
  transform-style: preserve-3d;
}

/* Mouth speaking animation */
@keyframes mouth-speak {
  0%, 100% { height: 4px; width: 12px; border-radius: 9999px; }
  25% { height: 8px; width: 10px; border-radius: 50%; }
  50% { height: 12px; width: 8px; border-radius: 50%; }
  75% { height: 6px; width: 14px; border-radius: 9999px; }
}

.animate-mouth-speak {
  animation: mouth-speak 0.3s ease-in-out infinite;
}
</style>
