/**
 * Network Status Composable
 * Provides reactive network status and offline queue integration
 */

import { ref, onMounted, onUnmounted } from 'vue'
import { offlineQueue } from '@/utils/offlineQueue'

export function useNetworkStatus() {
  const isOnline = ref(navigator.onLine)
  const queueLength = ref(offlineQueue.length)

  function updateOnlineStatus() {
    isOnline.value = navigator.onLine
    queueLength.value = offlineQueue.length
  }

  function handleOnline() {
    isOnline.value = true
    // Sync queue when back online
    offlineQueue.syncQueue().then(() => {
      queueLength.value = offlineQueue.length
    })
  }

  function handleOffline() {
    isOnline.value = false
  }

  onMounted(() => {
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    updateOnlineStatus()
  })

  onUnmounted(() => {
    window.removeEventListener('online', handleOnline)
    window.removeEventListener('offline', handleOffline)
  })

  return {
    isOnline,
    queueLength,
    offlineQueue
  }
}
