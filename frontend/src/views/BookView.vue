<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { API_URL } from '@/config'

const router = useRouter()
const appStore = useAppStore()

// Types
interface Book {
  id: string
  title: string
  author: string | null
  content: string
  total_chapters: number
}

interface Chapter {
  index: number
  title: string
  content?: string
}

interface ReadingPosition {
  chapter_index: number
  scroll_position: number
  progress_percent: number
}

// State
const books = ref<Book[]>([])
const currentBook = ref<Book | null>(null)
const chapters = ref<Chapter[]>([])
const currentChapter = ref<Chapter | null>(null)
const readingPosition = ref<ReadingPosition>({
  chapter_index: 0,
  scroll_position: 0,
  progress_percent: 0
})
const isReading = ref(false)
const showChapterList = ref(false)
const showAddBook = ref(false)
const newBook = ref({
  title: '',
  author: '',
  content: ''
})
const contentRef = ref<HTMLElement | null>(null)

const API_BASE = API_URL

// Computed
const companionId = computed(() => appStore.currentCompanionId || 'default')

// API calls
async function fetchBooks() {
  try {
    const res = await fetch(`${API_BASE}/books/`)
    if (res.ok) {
      books.value = await res.json()
    }
  } catch (e) {
    console.error('Failed to fetch books:', e)
  }
}

async function fetchChapters(bookId: string) {
  try {
    const res = await fetch(`${API_BASE}/books/${bookId}/chapters`)
    if (res.ok) {
      chapters.value = await res.json()
    }
  } catch (e) {
    console.error('Failed to fetch chapters:', e)
  }
}

async function fetchChapter(bookId: string, chapterIndex: number) {
  try {
    const res = await fetch(`${API_BASE}/books/${bookId}/chapters/${chapterIndex}`)
    if (res.ok) {
      currentChapter.value = await res.json()
    }
  } catch (e) {
    console.error('Failed to fetch chapter:', e)
  }
}

async function fetchReadingPosition(bookId: string) {
  try {
    const res = await fetch(`${API_BASE}/books/${bookId}/position?companion_id=${companionId.value}`)
    if (res.ok) {
      readingPosition.value = await res.json()
    }
  } catch (e) {
    console.error('Failed to fetch reading position:', e)
  }
}

async function saveReadingPosition() {
  if (!currentBook.value) return
  
  try {
    await fetch(`${API_BASE}/books/${currentBook.value.id}/position`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        chapter_index: readingPosition.value.chapter_index,
        scroll_position: contentRef.value?.scrollTop || 0,
        companion_id: companionId.value
      })
    })
  } catch (e) {
    console.error('Failed to save reading position:', e)
  }
}

async function openBook(book: Book) {
  currentBook.value = book
  await fetchChapters(book.id)
  await fetchReadingPosition(book.id)
  
  // Load the chapter at saved position
  await fetchChapter(book.id, readingPosition.value.chapter_index)
  isReading.value = true
  
  // Restore scroll position after content loads
  setTimeout(() => {
    if (contentRef.value) {
      contentRef.value.scrollTop = readingPosition.value.scroll_position
    }
  }, 100)
}

async function goToChapter(chapterIndex: number) {
  if (!currentBook.value) return
  
  readingPosition.value.chapter_index = chapterIndex
  await fetchChapter(currentBook.value.id, chapterIndex)
  showChapterList.value = false
  
  // Reset scroll
  if (contentRef.value) {
    contentRef.value.scrollTop = 0
  }
  
  await saveReadingPosition()
}

async function nextChapter() {
  if (!currentBook.value || !chapters.value.length) return
  
  const nextIndex = readingPosition.value.chapter_index + 1
  if (nextIndex < chapters.value.length) {
    await goToChapter(nextIndex)
  }
}

async function prevChapter() {
  if (!currentBook.value) return
  
  const prevIndex = readingPosition.value.chapter_index - 1
  if (prevIndex >= 0) {
    await goToChapter(prevIndex)
  }
}

async function addBook() {
  if (!newBook.value.title || !newBook.value.content) return
  
  try {
    const res = await fetch(`${API_BASE}/books/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...newBook.value,
        companion_id: companionId.value
      })
    })
    if (res.ok) {
      await fetchBooks()
      showAddBook.value = false
      newBook.value = { title: '', author: '', content: '' }
    }
  } catch (e) {
    console.error('Failed to add book:', e)
  }
}

async function deleteBook(bookId: string) {
  if (!confirm('确定要删除这本书吗？')) return
  
  try {
    const res = await fetch(`${API_BASE}/books/${bookId}`, {
      method: 'DELETE'
    })
    if (res.ok) {
      await fetchBooks()
    }
  } catch (e) {
    console.error('Failed to delete book:', e)
  }
}

function closeReader() {
  saveReadingPosition()
  isReading.value = false
  currentBook.value = null
  currentChapter.value = null
}

function goBack() {
  if (isReading.value) {
    closeReader()
  } else {
    router.back()
  }
}

// Save position on scroll
let scrollTimeout: number
function onScroll() {
  clearTimeout(scrollTimeout)
  scrollTimeout = window.setTimeout(saveReadingPosition, 1000)
}

onMounted(() => {
  fetchBooks()
})
</script>

<template>
  <div class="flex flex-col h-full bg-black">
    <!-- Header -->
    <header class="flex items-center justify-between px-4 py-3 border-b border-dark-200">
      <button class="touch-btn text-2xl" @click="goBack">←</button>
      <h1 class="text-lg font-medium">
        {{ isReading && currentBook ? currentBook.title : '一起看书' }}
      </h1>
      <button 
        v-if="!isReading"
        class="touch-btn text-2xl" 
        @click="showAddBook = true"
      >+</button>
      <button 
        v-else
        class="touch-btn text-xl" 
        @click="showChapterList = true"
      >📑</button>
    </header>

    <!-- Book list view -->
    <div v-if="!isReading" class="flex-1 overflow-y-auto p-4">
      <div v-if="books.length === 0" class="text-center py-12 text-dark-500">
        <div class="text-4xl mb-4">📚</div>
        <p>还没有书籍</p>
        <p class="text-sm mt-2">点击右上角添加</p>
      </div>
      
      <div class="grid grid-cols-2 gap-4">
        <div 
          v-for="book in books" 
          :key="book.id"
          class="bg-dark-100 rounded-lg p-3 cursor-pointer hover:bg-dark-200 transition-colors relative group"
          @click="openBook(book)"
        >
          <div class="aspect-[3/4] bg-dark-300 rounded mb-2 flex items-center justify-center text-4xl">
            📖
          </div>
          <div class="font-medium truncate">{{ book.title }}</div>
          <div class="text-sm text-dark-500 truncate">{{ book.author || '未知作者' }}</div>
          <div class="text-xs text-dark-500 mt-1">{{ book.total_chapters }} 章</div>
          
          <!-- Delete button -->
          <button 
            class="absolute top-2 right-2 w-6 h-6 bg-red-500/80 rounded-full text-xs opacity-0 group-hover:opacity-100 transition-opacity"
            @click.stop="deleteBook(book.id)"
          >×</button>
        </div>
      </div>
    </div>

    <!-- Reader view -->
    <div v-else class="flex-1 flex flex-col overflow-hidden">
      <!-- Chapter info -->
      <div class="px-4 py-2 bg-dark-100 text-sm text-dark-500 flex justify-between">
        <span>{{ currentChapter?.title || '加载中...' }}</span>
        <span>{{ Math.round(readingPosition.progress_percent) }}%</span>
      </div>
      
      <!-- Content -->
      <div 
        ref="contentRef"
        class="flex-1 overflow-y-auto px-4 py-4 text-base leading-relaxed"
        @scroll="onScroll"
      >
        <div class="whitespace-pre-wrap">{{ currentChapter?.content }}</div>
      </div>
      
      <!-- Navigation -->
      <div class="flex items-center justify-between px-4 py-3 border-t border-dark-200 bg-dark-100">
        <button 
          class="touch-btn px-4 py-2 bg-dark-300 rounded-lg disabled:opacity-50"
          :disabled="readingPosition.chapter_index === 0"
          @click="prevChapter"
        >
          上一章
        </button>
        <span class="text-sm text-dark-500">
          {{ readingPosition.chapter_index + 1 }} / {{ chapters.length }}
        </span>
        <button 
          class="touch-btn px-4 py-2 bg-dark-300 rounded-lg disabled:opacity-50"
          :disabled="readingPosition.chapter_index >= chapters.length - 1"
          @click="nextChapter"
        >
          下一章
        </button>
      </div>
    </div>

    <!-- Chapter list modal -->
    <div 
      v-if="showChapterList" 
      class="fixed inset-0 bg-black/80 flex items-end z-50"
      @click.self="showChapterList = false"
    >
      <div class="bg-dark-100 rounded-t-xl w-full max-h-[70vh] flex flex-col">
        <div class="flex items-center justify-between px-4 py-3 border-b border-dark-200">
          <h2 class="font-medium">目录</h2>
          <button class="touch-btn" @click="showChapterList = false">×</button>
        </div>
        <div class="flex-1 overflow-y-auto">
          <div 
            v-for="chapter in chapters" 
            :key="chapter.index"
            class="px-4 py-3 border-b border-dark-200 cursor-pointer hover:bg-dark-200"
            :class="{ 'text-primary': chapter.index === readingPosition.chapter_index }"
            @click="goToChapter(chapter.index)"
          >
            {{ chapter.title }}
          </div>
        </div>
      </div>
    </div>

    <!-- Add book modal -->
    <div 
      v-if="showAddBook" 
      class="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4"
      @click.self="showAddBook = false"
    >
      <div class="bg-dark-100 rounded-xl p-4 w-full max-w-sm max-h-[80vh] overflow-y-auto">
        <h2 class="text-lg font-medium mb-4">添加书籍</h2>
        
        <div class="space-y-3">
          <input
            v-model="newBook.title"
            type="text"
            placeholder="书名"
            class="w-full px-3 py-2 bg-dark-200 rounded-lg border border-dark-300 focus:border-primary focus:outline-none"
          />
          <input
            v-model="newBook.author"
            type="text"
            placeholder="作者 (可选)"
            class="w-full px-3 py-2 bg-dark-200 rounded-lg border border-dark-300 focus:border-primary focus:outline-none"
          />
          <textarea
            v-model="newBook.content"
            placeholder="粘贴书籍内容..."
            rows="10"
            class="w-full px-3 py-2 bg-dark-200 rounded-lg border border-dark-300 focus:border-primary focus:outline-none resize-none"
          ></textarea>
          <p class="text-xs text-dark-500">
            支持自动识别章节（第X章、Chapter X等格式）
          </p>
        </div>
        
        <div class="flex gap-3 mt-4">
          <button 
            class="flex-1 py-2 bg-dark-300 rounded-lg"
            @click="showAddBook = false"
          >
            取消
          </button>
          <button 
            class="flex-1 py-2 bg-primary rounded-lg"
            @click="addBook"
          >
            添加
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
