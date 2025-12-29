/**
 * Offline Message Queue
 * Queues messages when offline and syncs when back online
 */

interface QueuedMessage {
  id: string
  companionId: string
  content: string
  timestamp: number
  retries: number
}

const QUEUE_KEY = 'ai_companion_offline_queue'
const MAX_RETRIES = 3

class OfflineQueue {
  private queue: QueuedMessage[] = []
  private isOnline: boolean = navigator.onLine
  private syncInProgress: boolean = false

  constructor() {
    this.loadQueue()
    this.setupListeners()
  }

  private loadQueue(): void {
    try {
      const stored = localStorage.getItem(QUEUE_KEY)
      if (stored) {
        this.queue = JSON.parse(stored)
      }
    } catch (error) {
      console.error('Failed to load offline queue:', error)
      this.queue = []
    }
  }

  private saveQueue(): void {
    try {
      localStorage.setItem(QUEUE_KEY, JSON.stringify(this.queue))
    } catch (error) {
      console.error('Failed to save offline queue:', error)
    }
  }

  private setupListeners(): void {
    window.addEventListener('online', () => {
      this.isOnline = true
      this.syncQueue()
    })

    window.addEventListener('offline', () => {
      this.isOnline = false
    })
  }

  /**
   * Add a message to the queue
   */
  enqueue(companionId: string, content: string): string {
    const id = `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    const message: QueuedMessage = {
      id,
      companionId,
      content,
      timestamp: Date.now(),
      retries: 0
    }
    
    this.queue.push(message)
    this.saveQueue()
    
    // Try to sync immediately if online
    if (this.isOnline) {
      this.syncQueue()
    }
    
    return id
  }

  /**
   * Remove a message from the queue
   */
  dequeue(id: string): void {
    this.queue = this.queue.filter(m => m.id !== id)
    this.saveQueue()
  }

  /**
   * Get all queued messages
   */
  getQueue(): QueuedMessage[] {
    return [...this.queue]
  }

  /**
   * Get queue length
   */
  get length(): number {
    return this.queue.length
  }

  /**
   * Check if online
   */
  get online(): boolean {
    return this.isOnline
  }

  /**
   * Sync queued messages with server
   */
  async syncQueue(): Promise<void> {
    if (this.syncInProgress || !this.isOnline || this.queue.length === 0) {
      return
    }

    this.syncInProgress = true

    const messagesToSync = [...this.queue]
    
    for (const message of messagesToSync) {
      try {
        const response = await fetch('/api/messages/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            companion_id: message.companionId,
            content: message.content,
            role: 'user'
          })
        })

        if (response.ok) {
          this.dequeue(message.id)
        } else if (message.retries < MAX_RETRIES) {
          message.retries++
          this.saveQueue()
        } else {
          // Max retries reached, remove from queue
          this.dequeue(message.id)
        }
      } catch (error) {
        console.error('Failed to sync message:', error)
        if (message.retries < MAX_RETRIES) {
          message.retries++
          this.saveQueue()
        }
      }
    }

    this.syncInProgress = false
  }

  /**
   * Clear the entire queue
   */
  clear(): void {
    this.queue = []
    this.saveQueue()
  }
}

// Singleton instance
export const offlineQueue = new OfflineQueue()

// Export type
export type { QueuedMessage }
