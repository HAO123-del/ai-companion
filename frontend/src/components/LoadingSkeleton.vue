<template>
  <div class="loading-skeleton animate-pulse">
    <!-- Card skeleton -->
    <div v-if="type === 'card'" class="space-y-3">
      <div
        v-for="i in count"
        :key="i"
        class="bg-gray-700/30 rounded-xl p-4"
      >
        <div class="flex items-center gap-3 mb-3">
          <div class="w-10 h-10 bg-gray-600/50 rounded-full"></div>
          <div class="flex-1">
            <div class="h-4 bg-gray-600/50 rounded w-1/3 mb-2"></div>
            <div class="h-3 bg-gray-600/50 rounded w-1/4"></div>
          </div>
        </div>
        <div class="space-y-2">
          <div class="h-3 bg-gray-600/50 rounded w-full"></div>
          <div class="h-3 bg-gray-600/50 rounded w-5/6"></div>
          <div class="h-3 bg-gray-600/50 rounded w-4/6"></div>
        </div>
      </div>
    </div>

    <!-- List skeleton -->
    <div v-else-if="type === 'list'" class="space-y-2">
      <div
        v-for="i in count"
        :key="i"
        class="flex items-center gap-3 p-3 bg-gray-700/30 rounded-lg"
      >
        <div class="w-8 h-8 bg-gray-600/50 rounded-full"></div>
        <div class="flex-1">
          <div class="h-4 bg-gray-600/50 rounded w-2/3"></div>
        </div>
        <div class="w-16 h-4 bg-gray-600/50 rounded"></div>
      </div>
    </div>

    <!-- Message skeleton -->
    <div v-else-if="type === 'message'" class="space-y-4">
      <div
        v-for="i in count"
        :key="i"
        :class="[
          'flex gap-3',
          i % 2 === 0 ? 'justify-end' : 'justify-start'
        ]"
      >
        <div v-if="i % 2 !== 0" class="w-8 h-8 bg-gray-600/50 rounded-full flex-shrink-0"></div>
        <div
          :class="[
            'rounded-2xl p-3',
            i % 2 === 0 ? 'bg-primary/20' : 'bg-gray-700/30'
          ]"
          :style="{ width: `${40 + Math.random() * 40}%` }"
        >
          <div class="h-3 bg-gray-600/50 rounded w-full mb-2"></div>
          <div class="h-3 bg-gray-600/50 rounded w-3/4"></div>
        </div>
        <div v-if="i % 2 === 0" class="w-8 h-8 bg-gray-600/50 rounded-full flex-shrink-0"></div>
      </div>
    </div>

    <!-- Stats skeleton -->
    <div v-else-if="type === 'stats'" class="grid grid-cols-2 gap-3">
      <div
        v-for="i in count"
        :key="i"
        class="bg-gray-700/30 rounded-xl p-4"
      >
        <div class="h-3 bg-gray-600/50 rounded w-1/2 mb-3"></div>
        <div class="h-8 bg-gray-600/50 rounded w-2/3"></div>
      </div>
    </div>

    <!-- Default skeleton -->
    <div v-else class="space-y-3">
      <div
        v-for="i in count"
        :key="i"
        class="h-4 bg-gray-600/50 rounded"
        :style="{ width: `${60 + Math.random() * 40}%` }"
      ></div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  type?: 'card' | 'list' | 'message' | 'stats' | 'default'
  count?: number
}>()
</script>

<style scoped>
@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
</style>
