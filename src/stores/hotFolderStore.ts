import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { HotFolderConfig, FileQueueItem, QueueStatus } from '../types/hotfolder'

interface HotFolderStore {
  // Hot folder configuration
  folders: HotFolderConfig[]
  addFolder: (folder: HotFolderConfig) => void
  updateFolder: (id: string, updates: Partial<HotFolderConfig>) => void
  removeFolder: (id: string) => void
  
  // Queue management
  queue: FileQueueItem[]
  queueStatus: QueueStatus
  addToQueue: (item: FileQueueItem) => void
  updateQueueItem: (id: string, updates: Partial<FileQueueItem>) => void
  removeFromQueue: (id: string) => void
  clearQueue: () => void
  
  // Watcher control
  isWatching: boolean
  startWatching: () => void
  stopWatching: () => void
  pauseQueue: () => void
  resumeQueue: () => void
}

export const useHotFolderStore = create<HotFolderStore>()(
  persist(
    (set) => ({
      // Initial state
      folders: [],
      queue: [],
      queueStatus: {
        totalItems: 0,
        pendingItems: 0,
        processingItems: 0,
        completedItems: 0,
        failedItems: 0,
        isPaused: false,
      },
      isWatching: false,

      // Folder management
      addFolder: (folder) => set((state) => ({
        folders: [...state.folders, folder]
      })),
      
      updateFolder: (id, updates) => set((state) => ({
        folders: state.folders.map(f => f.id === id ? { ...f, ...updates } : f)
      })),
      
      removeFolder: (id) => set((state) => ({
        folders: state.folders.filter(f => f.id !== id)
      })),

      // Queue management
      addToQueue: (item) => set((state) => {
        const newQueue = [...state.queue, item]
        return {
          queue: newQueue,
          queueStatus: calculateQueueStatus(newQueue, state.queueStatus.isPaused)
        }
      }),
      
      updateQueueItem: (id, updates) => set((state) => {
        const newQueue = state.queue.map(item => 
          item.id === id ? { ...item, ...updates } : item
        )
        return {
          queue: newQueue,
          queueStatus: calculateQueueStatus(newQueue, state.queueStatus.isPaused)
        }
      }),
      
      removeFromQueue: (id) => set((state) => {
        const newQueue = state.queue.filter(item => item.id !== id)
        return {
          queue: newQueue,
          queueStatus: calculateQueueStatus(newQueue, state.queueStatus.isPaused)
        }
      }),
      
      clearQueue: () => set({
        queue: [],
        queueStatus: {
          totalItems: 0,
          pendingItems: 0,
          processingItems: 0,
          completedItems: 0,
          failedItems: 0,
          isPaused: false,
        }
      }),

      // Watcher control
      startWatching: () => set({ isWatching: true }),
      stopWatching: () => set({ isWatching: false }),
      
      pauseQueue: () => set((state) => ({
        queueStatus: { ...state.queueStatus, isPaused: true }
      })),
      
      resumeQueue: () => set((state) => ({
        queueStatus: { ...state.queueStatus, isPaused: false }
      })),
    }),
    {
      name: 'hot-folder-storage',
      partialize: (state) => ({ 
        folders: state.folders,
        // Don't persist queue - it should be rebuilt on startup
      }),
    }
  )
)

function calculateQueueStatus(queue: FileQueueItem[], isPaused: boolean): QueueStatus {
  const stats = queue.reduce((acc, item) => {
    acc.totalItems++
    switch (item.status) {
      case 'pending':
        acc.pendingItems++
        break
      case 'processing':
        acc.processingItems++
        break
      case 'completed':
        acc.completedItems++
        break
      case 'failed':
        acc.failedItems++
        break
    }
    return acc
  }, {
    totalItems: 0,
    pendingItems: 0,
    processingItems: 0,
    completedItems: 0,
    failedItems: 0,
    isPaused
  })
  
  return stats
}