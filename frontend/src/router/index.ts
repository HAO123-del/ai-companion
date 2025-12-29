import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

// Preload common views to avoid lazy loading delay
const HomeView = () => import('@/views/HomeView.vue')
const ChatView = () => import('@/views/ChatView.vue')

// Preload ChatView immediately after page load
if (typeof window !== 'undefined') {
  window.addEventListener('load', () => {
    setTimeout(() => ChatView(), 1000)
  })
}

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: HomeView,
    meta: { transition: 'fade' }
  },
  {
    path: '/chat',
    name: 'chat',
    component: ChatView,
    meta: { transition: 'slide-left' }
  },
  {
    path: '/call',
    name: 'call',
    component: () => import('@/views/CallView.vue'),
    meta: { transition: 'slide-up' }
  },
  {
    path: '/companion',
    name: 'companion',
    component: () => import('@/views/CompanionView.vue'),
    meta: { transition: 'slide-left' }
  },
  {
    path: '/memory',
    name: 'memory',
    component: () => import('@/views/MemoryView.vue'),
    meta: { transition: 'slide-left' }
  },
  {
    path: '/reminder',
    name: 'reminder',
    component: () => import('@/views/ReminderView.vue'),
    meta: { transition: 'slide-left' }
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('@/views/SettingsView.vue'),
    meta: { transition: 'slide-left' }
  },
  {
    path: '/music',
    name: 'music',
    component: () => import('@/views/MusicView.vue'),
    meta: { transition: 'slide-left' }
  },
  {
    path: '/book',
    name: 'book',
    component: () => import('@/views/BookView.vue'),
    meta: { transition: 'slide-left' }
  },
  {
    path: '/game',
    name: 'game',
    component: () => import('@/views/GameView.vue'),
    meta: { transition: 'slide-left' }
  },
  {
    path: '/diary',
    name: 'diary',
    component: () => import('@/views/DiaryView.vue'),
    meta: { transition: 'slide-left' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
