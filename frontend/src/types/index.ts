// Companion types
export interface Companion {
  id: string
  name: string
  personality: string
  avatarUrl: string
  avatarPrimaryColor: string
  avatarSecondaryColor: string
  avatarStyle: 'gradient' | 'solid' | 'outline'
  voiceId: string
  voiceType: 'cloned' | 'preset'
  createdAt: Date
  lastActiveAt: Date
}

export interface CreateCompanionInput {
  name: string
  personality: string
  avatarUrl?: string
  avatarPrimaryColor?: string
  avatarSecondaryColor?: string
  avatarStyle?: 'gradient' | 'solid' | 'outline'
  voiceId?: string
  voiceType?: 'cloned' | 'preset'
}

// Message types
export interface Message {
  id: string
  companionId: string
  role: 'user' | 'companion'
  content: string
  audioUrl?: string
  timestamp: Date
}

// Call types
export interface CallSession {
  id: string
  companionId: string
  startTime: Date
  status: 'connecting' | 'active' | 'ended'
}

// Music types
export interface MusicTrack {
  id: string
  title: string
  artist: string
  coverUrl: string
  audioUrl: string
  duration: number
}

// Book types
export interface Book {
  id: string
  title: string
  author: string
  coverUrl: string
  chapters: Chapter[]
}

export interface Chapter {
  id: string
  title: string
  content: string
}

export interface ReadingPosition {
  bookId: string
  chapterIndex: number
  scrollPosition: number
}

// Memory types
export interface Memory {
  id: string
  companionId: string
  category: 'preference' | 'fact' | 'event'
  content: string
  importance: number
  createdAt: Date
  lastAccessedAt: Date
}

// Reminder types
export interface Reminder {
  id: string
  companionId: string
  type: 'scheduled' | 'greeting' | 'checkin'
  message: string
  scheduledTime?: Date
  repeatPattern?: string
  enabled: boolean
}

// Diary types
export interface DiaryEntry {
  id: string
  content: string
  mood: 'happy' | 'neutral' | 'sad' | 'anxious' | 'excited'
  moodScore: number
  tags: string[]
  createdAt: Date
}

export interface MoodStats {
  period: 'week' | 'month'
  averageScore: number
  moodDistribution: Record<string, number>
  trend: 'improving' | 'stable' | 'declining'
  totalEntries: number
}

// Game types
export interface Game {
  id: string
  name: string
  type: 'word' | 'trivia' | 'card'
  description: string
}

export interface GameSession {
  id: string
  gameId: string
  companionId: string
  state: Record<string, unknown>
  score: { user: number; companion: number }
}

// Avatar types
export interface AvatarState {
  expression: 'neutral' | 'happy' | 'sad' | 'thinking' | 'surprised'
  isSpeaking: boolean
  lipSyncData?: number[]
}
