import { create } from 'zustand'
import { invoke } from '@tauri-apps/api/core'

export interface PhotoSession {
  id: string
  name: string
  date: string
  type: 'wedding' | 'portrait' | 'sports' | 'event' | 'product' | 'landscape' | 'custom'
  description: string
  sourceFolder?: string
  outputFolder?: string
  imageCount: number
  processedCount: number
  status: 'active' | 'completed' | 'archived'
  clientName?: string
  location?: string
  tags: string[]
  averageQualityScore: number
  processingTimeTotal: number
}

export interface ProcessingPreset {
  id: string
  name: string
  description: string
  pipelineConfig: any
  tags: string[]
}

interface SessionState {
  sessions: PhotoSession[]
  currentSession: PhotoSession | null
  presets: ProcessingPreset[]
  isLoading: boolean
  error: string | null
  
  // Actions
  loadSessions: () => Promise<void>
  createSession: (session: Partial<PhotoSession>) => Promise<PhotoSession>
  updateSession: (id: string, updates: Partial<PhotoSession>) => Promise<void>
  setCurrentSession: (session: PhotoSession | null) => void
  loadPresets: () => Promise<void>
  createPreset: (preset: Partial<ProcessingPreset>) => Promise<ProcessingPreset>
}

export const useSessionStore = create<SessionState>((set) => ({
  sessions: [],
  currentSession: null,
  presets: [],
  isLoading: false,
  error: null,

  loadSessions: async () => {
    set({ isLoading: true, error: null })
    try {
      const sessions = await invoke<PhotoSession[]>('get_sessions')
      set({ sessions, isLoading: false })
    } catch (error) {
      set({ error: error as string, isLoading: false })
    }
  },

  createSession: async (sessionData) => {
    set({ isLoading: true, error: null })
    try {
      const session = await invoke<PhotoSession>('create_session', { session: sessionData })
      set(state => ({ 
        sessions: [...state.sessions, session],
        currentSession: session,
        isLoading: false 
      }))
      return session
    } catch (error) {
      set({ error: error as string, isLoading: false })
      throw error
    }
  },

  updateSession: async (id, updates) => {
    set({ isLoading: true, error: null })
    try {
      await invoke('update_session', { id, updates })
      set(state => ({
        sessions: state.sessions.map(s => 
          s.id === id ? { ...s, ...updates } : s
        ),
        currentSession: state.currentSession?.id === id 
          ? { ...state.currentSession, ...updates }
          : state.currentSession,
        isLoading: false
      }))
    } catch (error) {
      set({ error: error as string, isLoading: false })
      throw error
    }
  },

  setCurrentSession: (session) => {
    set({ currentSession: session })
  },

  loadPresets: async () => {
    try {
      const presets = await invoke<ProcessingPreset[]>('get_presets')
      set({ presets })
    } catch (error) {
      set({ error: error as string })
    }
  },

  createPreset: async (presetData) => {
    try {
      const preset = await invoke<ProcessingPreset>('create_preset', { preset: presetData })
      set(state => ({ 
        presets: [...state.presets, preset]
      }))
      return preset
    } catch (error) {
      set({ error: error as string })
      throw error
    }
  }
}))