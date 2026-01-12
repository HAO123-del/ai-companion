/**
 * Toast Notification Composable
 * Provides a global toast notification system
 */

import { reactive } from 'vue'

interface ToastOptions {
  message: string
  type?: 'success' | 'error' | 'warning' | 'info'
  duration?: number
}

interface ToastItem extends ToastOptions {
  id: number
  visible: boolean
}

const toasts = reactive<ToastItem[]>([])
let nextId = 0

export function useToast() {
  function show(options: ToastOptions) {
    const id = nextId++
    const toast: ToastItem = {
      id,
      message: options.message,
      type: options.type || 'info',
      duration: options.duration || 3000,
      visible: true
    }
    
    toasts.push(toast)
    
    if (toast.duration && toast.duration > 0) {
      setTimeout(() => {
        hide(id)
      }, toast.duration)
    }
    
    return id
  }

  function hide(id: number) {
    const index = toasts.findIndex(t => t.id === id)
    if (index !== -1) {
      toasts[index].visible = false
      setTimeout(() => {
        const idx = toasts.findIndex(t => t.id === id)
        if (idx !== -1) {
          toasts.splice(idx, 1)
        }
      }, 300)
    }
  }

  function success(message: string, duration?: number) {
    return show({ message, type: 'success', duration })
  }

  function error(message: string, duration?: number) {
    return show({ message, type: 'error', duration: duration || 5000 })
  }

  function warning(message: string, duration?: number) {
    return show({ message, type: 'warning', duration })
  }

  function info(message: string, duration?: number) {
    return show({ message, type: 'info', duration })
  }

  return {
    toasts,
    show,
    hide,
    success,
    error,
    warning,
    info
  }
}

// Singleton for global access
export const toast = useToast()
