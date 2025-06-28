import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { invoke } from '@tauri-apps/api/core'
import { open } from '@tauri-apps/plugin-dialog'
import { listen } from '@tauri-apps/api/event'
import { useHotFolderStore } from '../stores/hotFolderStore'
import type { HotFolderConfig, WatcherEvent, QueueStatus } from '../types/hotfolder'

export function HotFolderPanel() {
  const {
    folders,
    addFolder,
    updateFolder,
    removeFolder,
    queueStatus,
    isWatching,
    startWatching,
    pauseQueue,
    resumeQueue,
  } = useHotFolderStore()

  const [error, setError] = useState<string | null>(null)
  const [isAddingFolder, setIsAddingFolder] = useState(false)

  // Subscribe to hot folder events
  useEffect(() => {
    const unsubscribe = listen<WatcherEvent>('hot-folder-event', (event) => {
      console.log('Hot folder event:', event.payload)
      // Handle the event - could update UI or show notifications
    })

    return () => {
      unsubscribe.then(fn => fn())
    }
  }, [])

  // Subscribe to queue status updates via SSE
  useEffect(() => {
    const eventSource = new EventSource('http://localhost:8888/queue/events')
    
    eventSource.onmessage = (event) => {
      try {
        const status: QueueStatus = JSON.parse(event.data)
        // Update queue status in store
        useHotFolderStore.setState({ queueStatus: status })
      } catch (err) {
        console.error('Failed to parse queue status:', err)
      }
    }

    eventSource.onerror = () => {
      console.error('Queue status stream error')
    }

    return () => eventSource.close()
  }, [])

  const handleAddFolder = async () => {
    try {
      setError(null)
      setIsAddingFolder(true)

      const selected = await open({
        directory: true,
        multiple: false,
      })

      if (selected && typeof selected === 'string') {
        const newFolder: HotFolderConfig = {
          id: crypto.randomUUID(),
          path: selected,
          enabled: true,
          extensions: ['jpg', 'jpeg', 'png', 'webp', 'raw', 'cr2', 'nef', 'arw'],
          stabilityTimeout: 2000,
          priority: 'normal',
        }

        // Start watching immediately
        await invoke('start_hot_folder', { config: newFolder })
        addFolder(newFolder)
        
        if (!isWatching) {
          startWatching()
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add folder')
    } finally {
      setIsAddingFolder(false)
    }
  }

  const handleToggleFolder = async (folder: HotFolderConfig) => {
    try {
      setError(null)
      
      if (folder.enabled) {
        await invoke('stop_hot_folder', { folderId: folder.id })
        updateFolder(folder.id, { enabled: false })
      } else {
        await invoke('start_hot_folder', { config: { ...folder, enabled: true } })
        updateFolder(folder.id, { enabled: true })
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to toggle folder')
    }
  }

  const handleRemoveFolder = async (folderId: string) => {
    try {
      setError(null)
      await invoke('stop_hot_folder', { folderId })
      removeFolder(folderId)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to remove folder')
    }
  }

  const handleToggleQueue = async () => {
    try {
      if (queueStatus.isPaused) {
        await fetch('http://localhost:8888/queue/resume', { method: 'POST' })
        resumeQueue()
      } else {
        await fetch('http://localhost:8888/queue/pause', { method: 'POST' })
        pauseQueue()
      }
    } catch (err) {
      setError('Failed to toggle queue')
    }
  }

  return (
    <div className="bg-gray-800 rounded-2xl p-6 backdrop-blur-sm bg-opacity-90">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-white">Hot Folders</h2>
        <button
          onClick={handleAddFolder}
          disabled={isAddingFolder}
          className="px-4 py-2 bg-neon-blue hover:bg-blue-600 disabled:bg-gray-600 text-white rounded-lg transition-colors"
        >
          {isAddingFolder ? 'Selecting...' : 'Add Folder'}
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-500 bg-opacity-20 border border-red-500 rounded-lg text-red-300 text-sm">
          {error}
        </div>
      )}

      {/* Queue Status */}
      <div className="mb-6 p-4 bg-gray-900 rounded-lg">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-gray-300">Processing Queue</h3>
          <button
            onClick={handleToggleQueue}
            className={`px-3 py-1 text-xs rounded-full transition-colors ${
              queueStatus.isPaused
                ? 'bg-yellow-600 hover:bg-yellow-700'
                : 'bg-green-600 hover:bg-green-700'
            } text-white`}
          >
            {queueStatus.isPaused ? 'Resume' : 'Pause'}
          </button>
        </div>
        
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-400">Total:</span>
            <span className="text-white font-medium">{queueStatus.totalItems}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Pending:</span>
            <span className="text-yellow-400 font-medium">{queueStatus.pendingItems}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Processing:</span>
            <span className="text-blue-400 font-medium">{queueStatus.processingItems}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Completed:</span>
            <span className="text-green-400 font-medium">{queueStatus.completedItems}</span>
          </div>
        </div>
      </div>

      {/* Folder List */}
      <div className="space-y-2">
        <AnimatePresence>
          {folders.map((folder) => (
            <motion.div
              key={folder.id}
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className={`p-3 bg-gray-900 rounded-lg border ${
                folder.enabled ? 'border-green-600' : 'border-gray-700'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white truncate">
                    {folder.path.split('/').pop() || folder.path}
                  </p>
                  <p className="text-xs text-gray-400 truncate">{folder.path}</p>
                </div>
                
                <div className="flex items-center gap-2 ml-4">
                  <button
                    onClick={() => handleToggleFolder(folder)}
                    className={`px-3 py-1 text-xs rounded-full transition-colors ${
                      folder.enabled
                        ? 'bg-green-600 hover:bg-green-700'
                        : 'bg-gray-600 hover:bg-gray-700'
                    } text-white`}
                  >
                    {folder.enabled ? 'Active' : 'Inactive'}
                  </button>
                  
                  <button
                    onClick={() => handleRemoveFolder(folder.id)}
                    className="p-1 text-gray-400 hover:text-red-400 transition-colors"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {folders.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            <p>No hot folders configured</p>
            <p className="text-sm mt-1">Click "Add Folder" to start monitoring a directory</p>
          </div>
        )}
      </div>
    </div>
  )
}